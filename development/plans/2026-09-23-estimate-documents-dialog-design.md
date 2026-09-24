# Estimate Documents dialog — Additional Information & images

**Status:** Design — sections 1–3 discussed in chat; written spec up for review
**Date:** 2026-09-23

## Why

The Google Doc template's `{{NOTES}}` placeholder is filled from
`Estimate.notes`, a single scalar field the portal no longer shows (its dialog
was removed 2026-09-19 when the Notes system shipped). There is no longer any
way to tell the portal what goes in that section. At the same time, estimators
want to hand the customer site photos inside the document itself.

This replaces the Documents dropdown on the estimate page with a dialog that
does three jobs: lists the generated versions, collects **Additional
Information** text for `{{NOTES}}`, and collects **images** that are placed in
the doc after the NOTES section.

## Decisions (from brainstorming, 2026-09-23)

| # | Decision |
|---|---|
| D1 | The dialog replaces `DocumentsBar`. The estimate page shows a **"Documents (N)"** button, where N is the number of versions. |
| D2 | Version delete moves into the dialog. No existing capability is lost. |
| D3 | Blank Additional Information prints **`--`**. `Estimate.notes` no longer feeds `{{NOTES}}` at all. |
| D4 | **Images only.** PDFs are out of scope. |
| D5 | Additional Information and images are **stored on the version record**, and the dialog prefills from the latest version. |
| D6 | Images are **new uploads only**. There is no picker for existing note photos. They carry forward through D5. |
| D7 | Images reach Google through **short-lived signed Firebase Storage URLs**. They are not platform URLs, which Google can't reach from local dev. |
| D8 | Generated versions are **read-only** in the dialog: open or delete only, with no reloading of an older version's inputs. |
| D9 | **Maple never writes what prints.** "Add a note to the estimate" in Maple now files a real estimate-level `Note` in the Notes feed and no longer writes `Estimate.notes`. Maple has no access to Additional Information. (Option C, decided 2026-09-23.) |

## Section 1 — Storage & data model

### Where images live

Firebase Storage, in the bucket logos already use (`settings.firebase_storage_bucket`):

```
estimate-doc-images/{company_id}/{estimate_id}/{image_id}.jpg
```

### Processing on upload

A new `services/estimate_doc_images.py` follows `services/company_logo.py`:

- It accepts `image/jpeg`, `image/png`, `image/webp` and `image/gif`. iOS
  converts HEIC to JPEG when a file is picked from Photos, so HEIC is not
  accepted.
- It applies the EXIF rotation (`ImageOps.exif_transpose`), so phone photos
  aren't sideways.
- It scales down to at most **2000px** on the long edge, then re-encodes as
  JPEG (quality ~85).
- It sets a `MAX_IMAGE_PIXELS` guard (decompression-bomb protection), the same
  way the logo code does.
- Limits: **10MB per file** before processing, and **10 images per
  document**.

Processing validates every file before anything is stored. One bad file
rejects the whole request with a 400 that names the file.

### Signed URLs at generation time

For each image, `blob.generate_signed_url(version="v4", expiration=10 min)`.
Google fetches the image once and keeps its own copy inside the Doc, so the URL
never has to outlive the request. The blob itself carries no public download
token, unlike logos.

### Model

`models/estimate.py`:

```python
class DocImage(BaseModel):
    id: str               # uuid4 hex; stable across versions that reuse it
    storage_path: str
    file_name: str        # original upload name, shown in the dialog
    width: int            # post-processing pixels, used for sizing in the doc
    height: int

class GoogleDocsVersion(BaseModel):
    ...existing fields...
    additional_info: Optional[str] = None   # exactly what went into {{NOTES}}; None on legacy versions
    images: List[DocImage] = []
```

### Carry-forward and lifecycle

- When v4 reuses an image from v3, both versions point to the **same blob**.
  Nothing is copied.
- **Deleting a version** deletes each of its blobs only if no remaining
  version of that estimate still references the same `storage_path`.
- **Deleting an estimate** deletes every image blob of every version, through
  the existing `cleanup_estimate_external_resources`
  (`routers/estimate_helpers/doc_versions.py`).
- Blob deletion is best-effort and logged, matching the Drive trash pattern. A
  failed delete never fails the user's request.

### Security

A reused image id is resolved **only** against this estimate's own
`google_docs_versions[*].images`. The client never sends a `storage_path`, so
a request cannot pull in a blob from another estimate or company. An unknown id
returns a 400.

### Legacy versions

Versions written before this change have `additional_info=None` and
`images=[]`. If the newest version is a legacy one, the dialog opens with an
empty textbox and no images. No backfill is needed.

## Section 2 — API & doc placement

### `POST /estimates/{estimate_id}/generate-doc` becomes multipart

The portal is the only caller: Maple does not generate docs, and
`agents/estimate/crud_handlers.py::_create_estimate_from_template` refers to
*estimate templates*, not this. So the JSON body is replaced outright instead
of being kept alongside.

| Form field | Type | Notes |
|---|---|---|
| `created_by` | `str` | Unchanged meaning (display name). Default `"portal-user"`. |
| `additional_info` | `str` | Default `""`. Stripped. Max **5,000** chars (422 above that). Newlines preserved. |
| `keep_image_ids` | repeated `str` | Ids of images from earlier versions to carry forward, in display order. |
| `files` | repeated `UploadFile` | New images, appended after the kept ones in upload order. |

Validation (all before any side effect): the estimate exists, the company
matches, `len(keep) + len(files) <= 10`, every kept id resolves (see Security
above), and every file passes processing.

### Order of operations and rollback

1. Validate and process all new files in memory.
2. Upload the new blobs to Firebase Storage.
3. Build the doc: copy the template, replace text, replace the logo, populate
   work items, **insert images**, share.
4. Append the `GoogleDocsVersion` (with `additional_info` and `images`).

If step 2 or 3 fails, the endpoint deletes the blobs uploaded in step 2 and,
if a doc was already created, trashes it. It then returns a **502** with
*"Couldn't add images to the document. Please try again."* (or the existing
500 copy for non-image failures). **Invariant:** a version record never
describes a doc that doesn't contain what the record says it does. Image
insertion is **fail-closed**, unlike the logo, which is fail-open. The user
attached these images deliberately, so a doc that is silently missing them is
the worse outcome.

### `{{NOTES}}` text

`prepare_template_data` takes `additional_info` as a parameter:

```python
'{{NOTES}}': additional_info.strip() or "--",
```

`Estimate.notes` is no longer read by the doc path. The unused
`EstimateDocumentGenerator.generate_doc_content` (the pre-template DocBuilder
path, which has no callers) still reads `estimate.notes`. It is **deleted** in
this change so the field has one less stale reader.

### Placing images after NOTES

`replaceAllText` gives no positions back, so the service marks the spot:

1. If images are present, the text pass replaces `{{NOTES}}` with
   `f"{notes_text}\n{{{{NOTES_IMAGES}}}}"`, which creates a new paragraph
   right after the notes text, carrying the notes paragraph's style.
2. `documents.get` finds the paragraph that contains `{{NOTES_IMAGES}}`.
3. One `batchUpdate` deletes the marker text, then inserts the images at that
   index **in reverse order**, each followed by a `\n`, so earlier indexes stay
   valid. Each image uses `insertInlineImage` with
   `objectSize.width = min(468pt, width_px × 0.75pt)` and the height scaled to
   match. 468pt is the 6.5" text width of a Letter page with 1" margins.

If the template has **no** `{{NOTES}}` placeholder, the images are appended
at the end of the document body instead of being dropped, and a warning is
logged.

This lives in a new `GoogleDriveService._insert_images_after_marker(doc_id,
marker, images)`, which `create_estimate_from_template` calls after
work-items population (so work-item row inserts don't shift indexes under it).

### `GET /estimates/{estimate_id}/doc-images/{image_id}`

This endpoint streams the stored JPEG for the dialog's thumbnails. It is
authenticated and company-scoped, and resolves the id the same way as
`keep_image_ids`. It mirrors the note-attachment read
(`GET /notes/{id}/attachments/{att}`), which the portal consumes through
`apiRequestBlob` and object URLs. A `?size=thumb` variant is **not** added:
images are already capped at 2000px, and there are at most 10.

### Delete

`DELETE /estimates/{id}/docs-versions/{version}` keeps its contract. It gains
the reference-checked blob cleanup described in Section 1.

## Section 3 — Dialog UI (proposed — up for review)

### Estimate page

`DocumentsBar` is removed. In its place, in the same row below the title bar, is a
`DocumentsButton`: **"Documents (N)"**, where N is
`google_docs_versions.length` (so "Documents (0)" before any doc exists). It
keeps `data-tour="estimate-documents"`, and the estimate-editor tour's step
copy is updated to describe the dialog. Like today, it only shows in edit mode.

### `DocumentsDialog` (`portal/src/components/estimates/DocumentsDialog.tsx`)

It is a modal on desktop and uses `ModalBottomSheet` on phones, the same shell
`NoteComposer` uses. There are two stacked regions:

1. **Generated versions.** Versions newest-first. Each row shows **Estimate
   vN** with an external-link icon, the created date, who created it, and the
   image count ("· 3 images", omitted when zero). Clicking the row opens
   `doc_url` in a new tab (`<a target="_blank" rel="noopener noreferrer">`).
   A trash icon per row opens the existing delete-confirmation dialog. When
   there are none, the list shows *"No documents yet."*
   **Generated versions are read-only** (decided 2026-09-23). The only
   actions are to open or delete one. There is no "use for new document"
   to load an older version's text or images back into the form. The form
   always prefills from the latest version.
2. **New document.**
   - An **Additional Information** textarea, prefilled from the latest
     version's `additional_info`. It shows a character counter near the 5,000
     limit, and helper text: *"Printed in the Notes section. Left blank, it
     shows "--"."*
   - **Images.** Thumbnails of the prefilled images (fetched through the new
     GET endpoint) and of new picks (through `URL.createObjectURL`). Each one
     has an `AttachmentRemoveBadge`. There is an "Add images" picker (with
     drag-and-drop on desktop), `accept="image/jpeg,image/png,image/webp,image/gif"`,
     and a counter reading "3 / 10". Picks over the cap, or over 10MB, are
     rejected on the client with an inline message. The server still
     re-validates.
   - A **Generate document** button. It keeps today's behavior: it saves a
     dirty estimate first, shows the "Generating Google Doc…" overlay, and on
     success opens the new doc in a new tab. The dialog **stays open**, with
     the new version at the top of the list, and the form re-prefills from it.

Removing a prefilled image only drops it from the next version. Earlier
versions keep it (Section 1 lifecycle).

### State and API

- `estimatesApi.generateGoogleDoc(id, { createdBy, additionalInfo,
  keepImageIds, files })` builds a `FormData`.
- `estimatesApi.getDocImageBlob(id, imageId)` uses `apiRequestBlob`.
- The dialog owns its own form state. The page keeps owning `docVersions` and
  the delete-confirmation state, as it does today. Object URLs are revoked on
  unmount and on removal (the `NoteComposer` pattern).

## Section 4 — Maple estimate notes (D9)

`agents/estimate/crud_handlers.py::_handle_update_estimate_notes` is replaced
by `_handle_add_estimate_note`, which calls `services.notes.create_note_as`
with `parent_type=ESTIMATE`, attributing the note to `current_user_email` and
`current_user_name`. It follows the property and contact agents' note
behavior:

- **No signed-in user:** the note is skipped with `NOTE_SAVE_NO_AUTHOR_REASON`.
- **Insert failure:** reported with `NOTE_SAVE_FAILED_REASON`. The body is
  never logged.

Two consequences:

- **Replace phrasings add a note too.** "set/replace the notes to …" adds a
  note as well, because a feed has nothing to overwrite. The `set`/`append`
  mode from `_detect_note_update` is ignored.
- **Notes skip the edit lock.** Following the Notes system's rule that an
  estimate's status never gates notes, the handler loads the estimate without
  the Draft/Review lock. Every other update sub-op keeps the lock.

`Estimate.notes` is then written by nothing in Maple and read by nothing on
the doc path. It stays in the model as legacy data. Estimate details still
render it when it's non-empty.

## Testing

**Backend** (TDD, with new or extended test files):

- `tests/test_estimate_doc_images.py`: accepted and rejected types, the
  10MB limit, EXIF rotation, the downscale to 2000px, the pixel-bomb guard,
  and the storage path shape.
- `tests/test_generate_google_doc_router.py`: multipart happy path, blank
  info → `--`, info over 5,000 → 422, more than 10 images → 400, a
  keep-id from another estimate → 400, kept and new ordering on the stored
  version, rollback that deletes uploaded blobs and trashes the doc on an
  image-insert failure, and the version record carrying `additional_info` and
  `images`.
- Version delete: a blob shared with another version survives, and a blob
  referenced only by the deleted version is removed. The estimate-delete
  cascade removes all of them.
- `tests/test_google_drive_service.py`: the marker replacement, the reverse
  order of inserts, width clamping and aspect ratio, and the append-at-end
  fallback when `{{NOTES}}` is missing.
- The `GET doc-images` endpoint: 404 for an unknown id, and 403 for another
  company.

**Portal:**

- `DocumentsButton`: the count, and hidden outside edit mode.
- `DocumentsDialog`: the list renders and links open in a new tab, delete
  triggers confirmation, prefill from the latest version, remove and add
  images, the cap and size client validation, the `FormData` shape on
  generate, and re-prefill after success.
- Existing `DocumentsBar` tests are deleted along with the component.

## Docs to update in the same change

- `CLAUDE.md` → Notes system item 6: `Estimate.notes` **no longer prints**
  on the Google Doc. `{{NOTES}}` now comes from the Documents dialog's
  Additional Information. Maple can still set the field. Its remaining reader
  is Maple itself, and its future is still deferred.
- `documentation/development/plans/2026-09-17-notes-design.md`: a
  cross-reference to this doc for D1.
- The Maple guide / user guide, where it describes the Documents dropdown.

## Risks

- **Signing needs a private key.** `generate_signed_url` works with the
  service-account key credentials firebase-admin is initialized with. If an
  environment runs on ADC without a key, signing falls back to IAM `signBlob`
  and needs `iam.serviceAccounts.signBlob`. Verify on Dev before release.
- **Popup blockers.** `window.open` after an `await` can be blocked, as it can
  today. The dialog's list is the fallback, because the new version is
  immediately clickable there.
- **Google fetch failures.** If Google can't fetch a signed URL (for example,
  it expired during an unusually slow template copy), the request fails closed
  with a 502. The 10-minute TTL gives wide headroom over a typical ~5–15s
  generation.

## Out of scope

- PDFs (D4).
- Choosing photos from existing estimate notes (D6).
- Reordering images beyond "kept, then new".
- Captions on images.
- Migrating or removing `Estimate.notes`.
