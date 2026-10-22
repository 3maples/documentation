# Estimate document images: sizes, captions, note photos, edit access

**Status:** Implemented 2026-10-21
**Builds on:** [2026-09-23-estimate-documents-dialog-design.md](2026-09-23-estimate-documents-dialog-design.md)

## Why

The Documents dialog put up to 10 uploaded photos after the Notes section,
each at full width with no label. Users asked for four things:

1. A size for each photo (Large, Medium or Small) and a caption under it.
2. Photos already on the estimate's notes, and on its property's notes, to
   be usable without uploading them again.
3. More than 10 photos.
4. The ability to edit the generated Google Doc. The docs belong to the
   service account and were shared "anyone with the link can view".

## Decisions (Simon, 2026-10-21)

| # | Decision |
|---|---|
| L1 | Each image has `size`: **large** = full text width, **medium** = a third (three per row), **small** = a quarter (four per row). (Changed the same day from a half and a third.) |
| L2 | Each image has an optional `caption` (at most 200 characters, whitespace collapsed), printed centred under it. |
| L3 | Medium and Small images sit **side by side in rows**. Consecutive images of the same size fill a row; a size change or a full row starts a new one. |
| L4 | "Estimate notes" means notes on the estimate **and** on its work items. |
| L5 | **No grouping by source.** Images show in the dialog and print in the document one after another, in the order they were added, with no headings. (Revised the same day: the first build grouped them under "Photos", "Notes photos" and "Property photos".) |
| L6 | In the dialog every tile is the same size whatever its L/M/S setting; the browser width decides how many fit per row. The three add buttons (**Add images**, **Choose from Notes**, **Choose from Property**) sit together above one grid. |
| L7 | The cap is **30** images per document, shared across the groups. |
| L8 | Edit access is a **per-user writer grant** on each file for the signed-in user's login email. The "anyone with the link can view" permission stays. |

## Data model

`DocImage` (`platform/models/estimate.py`) gains, all with defaults so older
rows load unchanged:

- `thumb_storage_path`: a ~320px JPEG next to the image, for the dialog tile.
- `size` (`large` / `medium` / `small`) and `caption`.
- `source` (`upload` / `estimate_note` / `property_note`), plus
  `source_note_id` and `source_attachment_id` for note photos.
- `blob_paths()`: the image and its thumbnail, used by every cleanup path.

`GoogleDocsVersion` gains `editors`: the lowercased login emails already
granted edit access, so a grant runs once per user per version.

`size` and `caption` belong to the version. Carrying an image forward keeps
its blob and may change both.

## API

### `POST /estimates/{id}/generate-doc`

`keep_image_ids` is replaced by one `images` form field: a JSON array of
specs, in order (`routers/estimate_helpers/doc_image_specs.py`):

```json
[
  {"kind": "kept", "id": "<DocImage.id>", "size": "large", "caption": null},
  {"kind": "upload", "file_index": 0, "size": "medium", "caption": "Back gate"},
  {"kind": "note", "note_id": "<Note id>", "attachment_id": "<NoteAttachment.file_id>", "size": "small"}
]
```

- A malformed field, an unknown size or a caption over 200 characters is a
  422. A `file_index` out of range, a file placed twice or a file nobody
  placed is a 400. More than 30 images is a 400. All of this is checked
  before anything is stored.
- A repeated kept id or note photo is placed once. So is a note photo that
  is already a kept image (matched on `source_attachment_id`).
- The client's order is the print order; the server keeps it.
- The caller is granted edit access to the new doc, best effort, and seeded
  into its `editors`. A failed grant never fails the generate.

### Note photos

`services/estimate_doc_note_images.py`:

- Every lookup filters on the estimate's company. A note on another
  company, on another estimate or property, or a missing note, is the same
  404 "Note not found". An attachment that isn't an image on that note is a
  404 "Attachment not found".
- The photo's bytes are read from GridFS and run through the same
  processing as an upload (`process_doc_image_upload`). The version gets its
  own copy in Firebase Storage, so a later edit to the note, or deleting it,
  doesn't change any document. A GridFS blob that has gone is a 409.

`GET /estimates/{id}/doc-image-sources` lists the image attachments the
pickers offer: `estimate_notes` (estimate and work-item notes, newest
first, with a work item's first description line as `work_item_title`) and
`property_notes` (`null` when the estimate has no property).

### Thumbnails

Each staged image also stores `{image_id}_thumb.jpg`.
`GET /estimates/{id}/doc-images/{image_id}?size=thumb` serves it, falling
back to the full image for images stored before thumbnails existed or whose
thumbnail blob is gone. Version delete, estimate delete and every rollback
path remove thumbnails with their images.

### Edit access

`POST /estimates/{id}/docs-access`, called by the dialog when it opens and
after each generate:

- For each version whose `editors` lacks the caller's email,
  `GoogleDriveService.grant_writer` creates a `user` / `writer` permission
  with `sendNotificationEmail=False`.
- Drive only shares silently with Google accounts. A login email with no
  Google account comes back as `invalidSharingRequest`; the endpoint stops
  trying the remaining versions and returns the message "Your login email
  isn't a Google account, so documents open read-only."
- Any other Drive error is reported as "Couldn't give you edit access right
  now, so documents open read-only." and retried on the next open.
- Granted emails are recorded with a raw `$addToSet` (array filter on the
  version numbers). A grant is not an edit to the estimate, so it must not
  move `updated_at`.
- A call that granted anything writes one `ESTIMATE_DOC_ACCESS_GRANT` audit
  entry with the version numbers (code review 2026-10-21 #3).

### Taking access back

Access goes with the membership (code review 2026-10-21 #2). Leaving a
company (`DELETE /users/me/company`), being removed from it
(`DELETE /users/{id}`), the company closing (`DELETE /companies/{id}`, for
each detached member) and the nightly Brevo reconcile's heal of a closed
company's stragglers all run `services/estimate_doc_access.revoke_doc_access`
(as a background task in the routes). It finds every version in the company
whose `editors` hold the user's email, deletes their Drive permission
(`google_drive_sharing.revoke_writer`) and pulls the email. A failed revoke
keeps the email, so a later call can retry it.

## Layout in the Google Doc

`services/google_doc_images.py`. The `{{NOTES_IMAGES}}` marker placement is
unchanged; what replaces it is new.

| size | per row | column width | image max width | max height |
|---|---|---|---|---|
| large | 1 | 468pt | 460pt | 600pt |
| medium | 3 | 156pt | 148pt | 200pt |
| small | 4 | 117pt | 109pt | 150pt |

Images never scale up past their natural size. Cells have 4pt padding,
which leaves slack so an image never equals the cell's content width (Docs
would then rescale it).

Two `batchUpdate` calls with a read-back in between, the same pattern as the
work-items table:

1. Delete the marker, then insert one `insertTable` (one row, n columns) per
   planned row, all at the marker index and in reverse, so the document
   reads in plan order.
2. Read the document back. Find the new tables and check their shape;
   anything unexpected raises `DocImageInsertError`, which trashes the
   half-built doc as before.
3. Table by table from the last one up, set fixed column widths, zero
   borders and padding, and insert each cell's image, caption and centring
   from the last cell back.

Consecutive images of one size share a row; a size change or a full row
starts the next one. Where an image came from never affects its place.

Precomputing the indexes of several nested tables in one batch was rejected:
the arithmetic is undocumented and one miscount corrupts every later cell.

## Portal

`portal/src/components/estimates/`: under **Document Details** the dialog
has the **Notes** field (printed in the doc's Notes section) and one ordered
draft list of kept, uploaded and note images in a single grid, with a shared
`n / 30` counter. **Add images**, **Choose from Notes** and **Choose from
Property** sit together above it; the last shows only when the estimate has
a property. Each tile has an L/M/S control and a caption field. `NoteImagePickerModal`
picks note photos with checkboxes; photos already in the draft show as
"Included". The read-only message from `docs-access` shows under the
version list.

## Thread safety of the Drive client

The dialog asks for edit access when it opens (twice at once in React's dev
mode), so Drive calls now overlap with a generate. The shared Drive and Docs
clients ran on one `httplib2.Http`, which is not thread-safe: overlapping
calls garbled the connection ("SSL record layer failure") and failed the
generate. Since 2026-10-21 both clients are built with a `requestBuilder`
that gives every request its own authorized `Http`
(`google_drive_service._request_builder`), Google's documented pattern.
Don't remove it to "reuse the connection".

## Risks

- **A grant made outside 3Maples.** Revocation removes only grants it
  recorded; someone who shared a doc by hand in Drive keeps that share.
- **Shared-drive sharing policy.** If the Shared Drive forbids sharing
  outside the organisation, every grant fails and users see the "couldn't
  give you edit access" message. Check the Dev and prod drive settings
  before release.
- **Grant cost on open.** A user is granted once per version, then skipped.
  The first open of an estimate with many versions makes one Drive call per
  version.
- **Edits made in Google Docs are not read back.** A regenerated version is
  built from the estimate again, so hand edits stay in the version they
  were made in.
