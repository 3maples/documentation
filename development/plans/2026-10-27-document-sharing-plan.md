# Document sharing: PDF download and email from a generated estimate doc

**Status:** Implemented 2026-10-27, uncommitted. Decided the same day in two
rounds of questions, then **revised after the first build**: Email PDF opens
the user's own email app instead of sending through Brevo (S3–S5, S7, S9 and
S12 below). Not yet verified by hand: a click-through on a phone and a
desktop browser, and a regenerated many-photo doc's PDF size (Section 2).
**Builds on:** [2026-09-23-estimate-documents-dialog-design.md](2026-09-23-estimate-documents-dialog-design.md),
[2026-10-21-estimate-doc-images-layout.md](2026-10-21-estimate-doc-images-layout.md)
and the edit windows of 2026-10-26 (`platform/services/estimate_doc_edit_window.py`).

## Why

A generated estimate is a Google Doc owned by the 3Maples service account.
Until now the only way to hand it to a customer was to open it (which shares
the link for editing until the window closes), download it from Google Docs
by hand, and attach it to an email outside the app. Users want a **Share**
action on each generated version that (a) downloads it as a PDF and (b)
starts an email with the PDF attached, with the PDF produced from the Google
Doc behind the scenes.

## What exists that this builds on

- **The doc belongs to the service account.** `GoogleDriveService` holds a
  Drive v3 client with the full `drive` scope, so `files().export()` works on
  every generated doc without any sharing change. Export runs in the
  threadpool like every other Drive call.
- **Drive exports Google Docs to PDF directly** (`files.export`,
  `mimeType=application/pdf`). The exported output is capped at **10 MB**
  (Google's documented limit; Drive answers 403 `exportSizeLimitExceeded`).
  The export has **no image-quality or size option**: the PDF carries the
  doc's images as they are.
- **A web page can't open the email app with a file attached.** A `mailto:`
  link carries no attachments in any browser. The closest the web allows is
  the device's share sheet with the file in it (Web Share with files:
  iOS and Android browsers, Safari on macOS, Edge and Chrome on Windows),
  where the user picks their email app. Firefox and Chrome on macOS can't
  share files.
- **Each version row is read-only** in the Documents dialog
  (`portal/src/components/estimates/DocVersionList.tsx`): Open and Delete.
  Share joins them.
- **`apiRequestBlob`** (`portal/src/api/client.ts`) already fetches binary
  responses with the auth header, for task photos.
- **Audit log** actions exist for every doc event (generate, edit open and
  close); downloading gets one more.
- **No branch resized doc images per size.** Generation signed the full
  2000 px image whatever the S/M/L choice; Google Docs only displays it
  narrower (checked on `main` and every platform worktree, 2026-10-27).

## Decisions (Simon, 2026-10-27)

| # | Decision |
|---|---|
| S1 | **Where:** a Share button on each version row of the Documents dialog, opening a small menu: **Download PDF** and **Email PDF**. |
| S2 | **The PDF is exported live from the Google Doc on every download and every email.** No stored copy. Edits made in Google Docs during an edit window show in the PDF. No warning when the version's edit window is open. |
| S3 | **Who:** everyone who can open the estimate, for both. Archived estimates included. *(Revised: Email was Owner/Admin only while the app sent the email itself.)* |
| S4 | **Email PDF opens the device's own email app with the PDF attached, on a blank email** the user addresses and writes, on phones and desktops alike. Through the share sheet where the browser can share files; otherwise the PDF is saved and a blank `mailto:` email opens for the user to attach it to. *(Revised: the first build sent through Brevo as "{Company} via 3Maples" with reply-to the company, recipients from the property's contacts, a bcc copy, an editable subject and message, and a branded body. Removed before commit.)* |
| S5 | **A "Preparing PDF" dialog** shows while the PDF is exported, for both actions, with Cancel. |
| S6 | **Size:** Images are right-sized **per the S/M/L choice at generation time**, and anything still large is shrunk inside the exported PDF (Section 2). **The fallback stays:** when Drive refuses to export at all, the error message points to Google Docs' own menu in the open doc, File → Download → PDF. |
| S7 | **Record:** each PDF fetch is audited (`estimate_doc_download`). The send itself happens in the user's email app, so the app neither sees nor records it. |
| S8 | **Status: sharing never touches it.** Marking Sent stays the manual step it is today. |
| S10 | **File name:** `Estimate-E0042.pdf` for the download and the attachment, no version suffix (the version is in the audit row). |
| S11 | **One PDF:** download and email get the same shrunk PDF. |

S9 (a rate limit on sends) and S12 (no Brevo lifecycle event) belonged to
the Brevo send and went with it.

## Section 1 — PDF export (platform)

`services/google_drive_service.py` gains one method:

```python
def export_pdf(self, file_id: str) -> bytes:
    """The doc as a PDF, straight from Drive. Raises DocExportTooLarge when
    Drive refuses (its 10 MB export cap) and DocMissing on Drive's 404."""
```

- `files().export(fileId=file_id, mimeType="application/pdf").execute()`,
  which returns the bytes in one response (Drive caps the export at 10 MB,
  so no chunked download is needed; the per-request `AuthorizedHttp`
  builder keeps it thread-safe like every other call).
- Error mapping, in a new `services/estimate_doc_pdf.py` that owns the
  exceptions, the file name (`Estimate-{estimate_id}.pdf`, S10) and the
  shrink of Section 2: 404 → `DocMissing` ("This document no longer exists
  in Drive"); 403 whose reason is `exportSizeLimitExceeded` →
  `DocExportTooLarge`; anything else re-raises and the route answers 503
  like the edit window does.
- Nothing about sharing changes: the service account exports its own file.

**Endpoint** in `routers/estimate_documents.py`:

```
GET /estimates/{estimate_id}/docs-versions/{version}/pdf
→ application/pdf, Content-Disposition: attachment; filename="Estimate-E0042.pdf"
   Cache-Control: private, no-store
```

- Tenant boundary through `_authorized_estimate`, same as every doc route.
  Any role; archived estimates included (the archived-*company* block in
  `assert_user_company_access` still applies).
- Rate limited per user: 30 PDFs in 10 minutes (`doc_pdf_rate_limiter`),
  then 429 "Too many PDF downloads. Try again in a few minutes." Each call
  is a Drive export and a re-encode (code review 2026-10-27 #3).
- `require_drive_service()` first: 503 when Drive is off.
- Audit `AuditAction.ESTIMATE_DOC_DOWNLOAD` with `{"version": n}` via
  `create_audit_log` (the `@audit_log` decorator expects a model result;
  the edit-window route shows the manual form).
- Errors: 404 (doc gone), 413 "This document is too large to export as a
  PDF. Open it and use File → Download → PDF in Google Docs." (Drive's
  cap), 503 (Drive failure).

## Section 2 — Image size: per S/M/L at generation, then a PDF safety net

Drive's export can't be told to shrink images; the PDF carries whatever the
doc holds. Today every doc image is stored and placed at up to **2000 px**
on the long edge, whatever its size in the dialog, while the doc prints it
at (`services/google_doc_images.py`):

| Size | Printed width | Pixels needed at 300 dpi | Placed today |
|---|---|---|---|
| Large | 460 pt (6.4 in) | ~1,900 | 2,000 |
| Medium | 148 pt (2.1 in) | ~620 | 2,000 |
| Small | 109 pt (1.5 in) | ~450 | 2,000 |

A medium or small image therefore carries 10–20× the pixels the page can
show. Generation is the one place the S/M/L choice is known for certain
(the PDF carries no image ids, and a doc the user edited in Google Docs may
hold images that are in no version record). Two layers:

### Layer 1 — a rendition per size, placed at generation (its own commit)

`services/estimate_doc_images.py` gains renditions next to the image and
its thumbnail:

```python
DOC_IMAGE_RENDITION_EDGE_PX = {"medium": 800, "small": 600}   # large: the stored 2000 px image
DOC_IMAGE_RENDITION_JPEG_QUALITY = 80

# models/estimate_documents.py (split out of models/estimate.py, review #4):
# a pure path function the model's blob_paths() can use
def doc_image_rendition_path(storage_path: str, size: DocImageSize) -> str   # "…/{id}_medium.jpg"
# services/estimate_doc_images.py
def needs_rendition(size: DocImageSize, width: int, height: int) -> bool
def list_doc_image_paths(prefix: str) -> set[str]           # one listing of an estimate's folder
def ensure_doc_image_rendition(storage_path, size, width, height, existing: AbstractSet[str]) -> str
    """The blob to place the image from at `size`: its rendition, made from
    the stored image the first time any version needs it, or the stored
    image itself for large or for one already within the edge."""
```

- `build_doc_image_inserts` (`routers/estimate_helpers/doc_versions.py`)
  signs the rendition's URL for a medium or small image. A large image is
  placed from the stored 2000 px image as today (6.4 in at 300 dpi needs it).
- `width`/`height` stay the **stored** image's. The layout fits each image
  to its size's box by aspect ratio, and a rendition is always larger than
  that box, so the print size is identical; this avoids reading a rendition
  back to learn its pixels.
- A rendition that can't be made (a storage error) is logged and the stored
  image is placed instead: generation never fails for an optimisation.
- One image at a time, as before: the storage client is shared across
  threads. The estimate's folder is **listed once per generate**, and only
  when some image needs a rendition; a rendition already made then costs
  no call, and a new one a read, resize and write. A failed listing is
  logged and the renditions are made again, which is harmless (review #1).
- Renditions are made on demand, so a carried-forward image that changes
  from large to small in a later version gets its small rendition then, and
  the stored full-size image is never touched (a later version may want it
  large again).
- `DocImage.blob_paths()` lists the two rendition paths with the image and
  thumbnail, so version delete and estimate delete clean them up through
  the existing paths. The paths are **derived, not recorded**: a recorded
  path would leak when the version that made it is deleted before an older
  one still holding the image. `delete_doc_images` skips a path that isn't
  there (Storage's `NotFound`) without a warning. It also **lists each
  folder once first** and deletes only the paths stored, so a rendition
  never made costs no call; a failed listing falls back to deleting every
  path (review #2).
- `scripts/copy_storage_files.py` copies by prefix, so it carries
  renditions with no change.
- Existing versions are unchanged: their docs already hold 2000 px images.
  Regenerating a version applies the renditions.
- Expected effect: a 30-photo doc of mostly medium and small images shrinks
  from roughly 10 MB to 1–2 MB **in the doc itself**, so Drive's export cap
  stops being a practical risk for such docs and the Google Doc loads faster
  during edit windows.

### Layer 2 — shrink what is still large, inside the exported PDF

Large images (2000 px) and images the user added by hand in Google Docs
are still bigger than an emailed PDF needs. After the export, in
`services/estimate_doc_pdf.py`, with **pikepdf** (pip-installable, bundles
qpdf, MPL-2.0; not PyMuPDF, which is AGPL):

```python
PDF_IMAGE_MAX_EDGE = 1200   # px; ~185 dpi at the doc's full text width
PDF_IMAGE_QUALITY = 75      # JPEG

def shrink_pdf_images(pdf: bytes) -> bytes:
    """The same PDF with every raster image larger than PDF_IMAGE_MAX_EDGE
    re-encoded as a JPEG at that size. Images already small, and any the
    code can't safely re-encode (soft masks, unusual colour spaces), are
    left as they are. Returns the input unchanged on any pikepdf error."""
```

- Iterate each page's images with `Page.get_images()` (recursive, so
  images drawn through form XObjects count; `Page.images` is deprecated),
  decode with Pillow (`as_pil_image()`), fit to the max edge, re-encode
  JPEG, write the stream back with `/Filter /DCTDecode` and the new
  `/Width`, `/Height`, `/BitsPerComponent 8`. The colour space is kept: an
  ICC profile with the same component count stays valid. A re-encode that
  comes out no smaller keeps the original.
- Medium and small renditions, the company logo and the template's small
  graphics fall under the threshold and are untouched.
- `Image.MAX_IMAGE_PIXELS` guard, as the upload path has.
- Both download and email use the shrunk PDF (S11).

### What this does not do

- It does not rescue a doc Drive refuses to export (its 10 MB cap applies
  before we see the file). That is the File → Download → PDF fallback in the
  error message (S6). With Layer 1, only a doc of many **large** photos, or
  one the user filled with images by hand, can still get there.
- It does not re-fit PDF images to their drawn size on the page (which would
  need content-stream parsing to find each image's placement). Layer 1 makes
  that unnecessary for the images the app places.

### Measurements (Dev, 2026-10-27)

The Dev docs with the most images, exported live and shrunk with Layer 2.
These docs predate Layer 1, so every image is placed at its stored pixels.

| Doc | Images by size | Exported | After Layer 2 |
|---|---|---|---|
| E0060 v2–v5 | 1 large, 1–2 medium, 2–3 small | 2.11 MB | 1.03 MB (49%) |
| E0024 v1 | 6 large | 1.02 MB | 0.84 MB (82%) |
| E0032 v1 | 6 small | 0.86 MB | 0.61 MB (71%) |

What the exports showed:

- **Google keeps each image at its stored pixels** in the PDF: a small
  photo printed 1.5" wide is still 1500×2000 in E0060. This confirms the
  case for Layer 1.
- Images are 90–95% of each file, at roughly 150–300 KB each (one photo at
  920 KB). A 30-photo doc would export at roughly 5–9 MB today, close to
  Drive's 10 MB cap.
- Every photo is a JPEG with an ICC colour profile (`/ICCBased`); the logo
  is a Flate (PNG) image under the size threshold. The shrink keeps the ICC
  profile; a side-by-side check of one photo showed no colour or
  orientation change.

**Layer 1, projected for E0060 v5** (its stored images read from Dev
storage and passed through the rendition code; nothing written):

| Image | Stored | Placed with Layer 1 |
|---|---|---|
| small | 1500×2000, 283 KB | 450×600, 41 KB |
| small | 1500×2000, 1,064 KB | 450×600, 89 KB |
| medium | 1500×2000, 326 KB | 600×800, 72 KB |
| medium | 738×1600, 58 KB | 369×800, 23 KB |
| large | 1600×1200, 353 KB | unchanged |
| **total** | **2.08 MB** | **0.58 MB** |

Google re-encodes each placed image at about 0.9× the bytes it was given,
at the same pixels (E0060's PDF streams vs its stored blobs), so the export
should fall from 2.11 MB to roughly 0.8 MB, and to roughly 0.65 MB once
Layer 2 shrinks the one large photo. **Not yet confirmed by a real
regenerate**: that needs a new version generated on Dev, which writes to a
real estimate, so it waits for a manual test.

## Section 3 — Email PDF on the device (portal only)

No server work beyond Section 1: Email PDF fetches the same PDF as
Download, then hands it to the device.

1. **Prepare.** Share → Email PDF shows "Preparing PDF" while
   `GET …/pdf` runs (1–4 s), the same as Download.
2. **Hand over, on a second click.** A share sheet opens only on a fresh
   click, and the export takes longer than the browser keeps the first one
   (Safari refuses `navigator.share` after an `await`), so the dialog turns
   into "Email PDF" with an **Open email** button. That click calls
   `navigator.share({ files: [pdf] })` with the file alone, so the email
   the user's app starts is blank.
3. **Without file sharing** (`navigator.canShare({ files })` false or
   absent), the button reads **Save PDF and open email**: it saves the PDF
   and opens a blank `mailto:` email to attach it to. A share the device
   refuses (`NotAllowedError` and the like) falls back the same way;
   closing the share sheet (`AbortError`) keeps the dialog for another try.

## Section 4 — Portal

- **`DocVersionList`**: each row gains a Share button (lucide `Share2`) next
  to Delete, opening **Download PDF** and **Email PDF** for everyone. The
  menu is the shared `ActionsMenu`, which gained an optional `triggerIcon`
  (the three dots stay the default).
- **`useDocSharing`** (beside the Documents dialog) runs both: one job at a
  time; Cancel drops a PDF that arrives afterwards; a failure goes to the
  Documents dialog's error line with the server's message.
- **`SharePdfDialog`**: "Preparing PDF" with a spinner, the file's name and
  Cancel; for Email PDF, then the "Email PDF" step of Section 3.
- **`lib/docSharing.ts`**: `pdfFileName`, `pdfFile` (the Blob as a named
  `application/pdf` File, which a share sheet needs), `canShareFile`,
  `openBlankEmail`, and `handOverPdf`, Email PDF's whole hand-over, which
  `useDocSharing` calls on the "Open email" click: the share sheet with the
  file alone, "dismissed" on a closed sheet (the dialog stays), otherwise
  the PDF saved and a blank email. **`lib/saveBlob.ts`** saves a Blob as a
  named download (the object URL is revoked on the next tick, which Safari
  needs); the Materials and People CSV templates use it too.
- **`apiRequestBlob`** now goes through the same request path as JSON
  calls, so its errors carry the server's message: the 413's File →
  Download → PDF guidance reaches the user instead of "Request failed
  (413)". Its other callers (task photos, note attachments, doc images)
  only gain better messages.
- The page passes the estimate's readable id (`estimateLabel`) for the
  file's name; nothing else.

## Section 5 — Data model and config

No change to `GoogleDocsVersion`. `models/audit_log.py`:
`ESTIMATE_DOC_DOWNLOAD = "estimate_doc_download"`, metadata `{"version"}`.
No new environment variables. One new dependency: `pikepdf` in
`platform/requirements.txt` (pinned, wheels for the Render image; verify
the build once on Dev).

## Section 6 — Tests

Platform: `tests/test_estimate_doc_pdf.py` (export, errors, file name,
shrink), `tests/estimate_documents/test_estimate_doc_pdf_api.py` (the
route: roles, scope, archived, errors, audit), and Layer 1 in
`tests/test_estimate_doc_images.py`, `tests/test_estimate_doc_version_images.py`
and `tests/estimate_documents/test_estimate_documents_api.py`.

Portal: `tests/DocumentsDialogSharing.test.tsx` (the menu, the progress
dialog, Cancel, a failed download, the share sheet getting the file alone,
a closed share sheet, both fallbacks, and the one-PDF-at-a-time guards),
`tests/docSharing.test.ts` (the helpers, and `handOverPdf`'s five outcomes),
`tests/saveBlob.test.ts`, `tests/apiRequestBlob.test.ts`,
`tests/estimatesApiDocSharing.test.ts`, `tests/ActionsMenu.test.tsx`, and
the CSV template downloads in `tests/MaterialsPageMenus.test.tsx` and
`tests/PeoplePageCsvUpload.test.tsx`.

## Section 7 — Rollout

1. Platform: export, download route and the PDF shrink (Layer 2).
2. Platform: the per-size renditions at generation (Layer 1). Its own
   commit: it changes what every new doc holds, independent of sharing.
3. Portal: Share, the progress dialog, device email.
4. Docs: the user guide (Maple answers help from it), Maple's "send it"
   and "export a PDF" redirects (`agents/conversation/out_of_chat.py`) and
   their rows in the phrasing reference. Changelog entry comes with
   `/release`, not before.

Nothing here constrains deploy order: an old portal never calls the new
route, and a new portal against an old platform only sees Share fail with a
404 that its error line shows.

## Out of scope (noted, not planned)

- Rescuing docs Drive won't export at all (over its 10 MB cap) by exporting
  a temporary downsized copy of the doc instead. The File → Download → PDF
  fallback covers it; revisit if the measurement shows it is common.
- Sending from the app (the first build's Brevo send), or from the user's
  mailbox through Gmail or Outlook sign-in. Both would let the app record
  the send; neither is needed for Email PDF as decided.
- Any status change from sharing (S8).
- Sharing the Google Doc link itself (view-only links); the edit window
  covers in-app editing, and a PDF is what customers expect to keep.
- A customer-facing acceptance link ("Approve this estimate"). Worth a plan
  of its own once sharing is in use.

## Sources

- Drive `files.export` and its 10 MB cap: https://developers.google.com/workspace/drive/api/reference/rest/v3/files/export
- Web Share API, sharing files (`navigator.canShare`, `navigator.share`): https://developer.mozilla.org/en-US/docs/Web/API/Navigator/share
