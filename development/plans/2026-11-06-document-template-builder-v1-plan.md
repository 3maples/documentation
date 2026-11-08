# Document editor and templates — v1 scope and implementation plan

Mockups: https://claude.ai/artifact/6KUnMnk1ww9C9dJAMKpS8p (Settings list, editor in template mode, Documents hub, editor in document mode, sample output). Redrawn 2026-11-07 for one editor.
PRD: "Document Builder" (14 pp, read in full).

**Status:** Plan, not started.
- **2026-11-06:** reviewed against the code (platform 56e66ff, portal 89dd848).
- **2026-11-07:** reshaped by Simon three times that day:
  - A template is one top-down list of blocks: no sections, no columns.
  - Text Blocks and an image library move into the editor.
  - **One editor builds both templates and documents.** A document starts from a blank page, a template or an earlier version, and is then edited block by block with the estimate's data already filled in. This brings the PRD's per-estimate tailoring (A*, B10–B12, F2) into v1.
- **Q5–Q8** were answered the same day (D15–D18).
- **Final review, 2026-11-07** (the last section): gaps fixed in place; Q9 and Q10 accepted as D19 and D20. Nothing is open.

**Builds on:** [2026-09-23-estimate-documents-dialog-design.md](2026-09-23-estimate-documents-dialog-design.md),
[2026-10-21-estimate-doc-images-layout.md](2026-10-21-estimate-doc-images-layout.md),
[2026-10-27-document-sharing-plan.md](2026-10-27-document-sharing-plan.md).

## Context

Today every company's customer document comes from **one platform-wide Google Doc template** (`GOOGLE_DRIVE_ESTIMATE_TEMPLATE_ID`). Generation copies it and runs `replaceAllText` over fixed `{{PLACEHOLDER}}`s (`services/estimate_doc_generator.py`, `services/google_drive_service.py::create_estimate_from_template`). The only per-document inputs are Notes, saved Text Blocks and photos (`DocumentsDialog.tsx`). Layout, order and wording can't change, per company or per document.

This release adds **one block editor** that works in two modes:

| | Template mode | Document mode |
|---|---|---|
| Opened from | Settings → Document Templates | An estimate's Documents → Start a document |
| Data in the blocks | A sample estimate | This estimate, live |
| Saves to | The template | The estimate's draft |
| Main action | Save | **Generate document** (a Google Doc version) |
| Who | Owners and Admins | Everyone who can open the estimate |

A template is only a starting point. A document starts from a blank page, a ready-made template or an earlier version of this estimate's document, and then everything can change in the editor: add, remove and reorder blocks, retype text, add photos, flip show/hide options. Editing a document never touches its template. The generated Google Doc is ordinary and independent, and the existing edit window still lets users change it afterwards.

Naming: Settings already has **Templates** (work-item templates). The new feature is called **Document Templates** everywhere: collection `document_templates`, route `/document-templates`, tab id `document-templates`.

## Decisions (2026-11-07)

| # | Question | Decision |
|---|---|---|
| D1 | Where the logo lives | **The Company block only.** It inserts `Company.logo_url` inline. The style base carries no image, so nothing replaces "the first image in the doc" any more. |
| D2 | "Valid until" date | **Not in v1.** Estimates have no such field. |
| D3 | An estimate's division | An estimate's divisions are its work items' division names (`JobItem.division`), resolved to `Division` ids within the company. Templates with any of them in `suggested_division_ids` are listed first. The **division default** is preselected only when exactly one template is the default for all of them; otherwise the company default is preselected. A division deleted later is dropped from a template's lists when the template is read. |
| D4 | Deleting a library item a template uses | **Library images only** (narrowed by D16): deleting an image a template uses is refused with a 409 that names the templates. Saved text deletes freely, because templates and documents hold copies. |
| D6 | Who may do what | **Members** start, edit and generate documents in the editor, including adding blocks and inserting saved text and library images. **Owners and Admins** also create and edit templates, manage the two libraries, and use "Save as template" from a document. Members don't see Settings → Document Templates. |
| D7 | Sections | **Dropped.** The PRD's 21 guide sections become starter content: the built-in templates and a starter saved-text library. |
| D8 | Text Blocks | **Move into the editor's palette.** When the flag is on, Settings → Text Blocks goes away; when it's off, the tab stays as it is today. |
| D9 | Images | A company **image library** in the palette. In document mode, an Image block also takes photos: upload, from Notes, from Property, as the dialog does today. |
| D10 | Where block options are set | **In the editor**: on the template as its defaults, and again on each document. *(Revised: was "Builder only".)* |
| D11 | The Note block | **Typed straight into the block in document mode.** A template's Note block can carry starter text. It doesn't pull estimate notes. |
| D12 | Style base | **One fixed system style** (today's template minus its body). Not editable per company in v1. |
| D13 | Layout blocks | **Page break, Divider, Spacer**, plus "Space above / below" on every block. No columns for now. |
| D14 | Generating | **The editor is the generator** (Simon, 2026-11-07). The Documents dialog shrinks to a hub: the versions list, the saved draft, and "Start a document". |
| D15 | Phones | **The same editor, page only.** Below tablet width the palette and the inspector open as bottom sheets ("Add a block", "Edit block"), blocks move with up/down buttons instead of drag, and Save draft / Generate sit in a sticky bottom bar. Template mode stays tablet and desktop only (a phone shows a notice). |
| D16 | Saved text | **Inserting saved text copies it**, in templates and documents alike. The library is a set of snippets: a later edit changes only new inserts, and the inserted copy can be retyped. |
| D17 | Note vs Text | **Note stays its own block.** It is the only block that raises a "still empty" readiness warning, and its text is the only text Save as template leaves out. |
| D18 | Template edits and open drafts | **A draft keeps its own copy of the blocks** from the moment it started. Later template edits never reach an open draft or a version. |
| D19 | Preview | **The canvas is the preview.** No server HTML renderer, no preview endpoint, no iframe. The canvas is drawn at the Doc's text width with the Doc's fonts, fed by a context endpoint; readiness is computed on the client. The real check is Generate, then Open. |
| D20 | Starter texts | **Not seeded.** They live in code and show in the palette as a read-only Starter texts group, inserted as copies. "Save to my saved text" copies one into the library (Owners and Admins). |

## The flow

1. **Estimate → Documents** opens the hub. It has three parts:
   - The **versions** (Open / Share / Delete, as today), each labelled with what it started from.
   - The saved **draft**, if any: "Continue draft · saved 2 min ago by Dana".
   - **Start a document**: Blank, the company's templates (suggested-for-division first, the default marked), the built-ins, and "Copy of v2" (any earlier version).

   Starting a document while a draft exists asks to replace the draft.
2. The **editor in document mode** opens at `/estimates/:id/document`, a page of its own (the hub is a dialog on the estimate page, `EstimateTitleBar`). It is filled from the chosen start: the template's blocks, or the version's stored layout. The Company, Customer and Estimate blocks show this estimate's live data, and Text blocks show their merge fields resolved. Back, and a finished Generate, return to `/estimates/:id/with-activity?documents=1`, which reopens the hub.
3. The user edits anything. Readiness warnings show in a bar and as a badge on the block they concern, and they are non-blocking.
4. **Save draft** stores the layout and photos on the estimate (one draft per estimate, as today, with the same "someone saved a newer draft" check). An unsaved-changes guard covers leaving the page.
5. **Generate document** composes the Google Doc from the layout. It records a version with the layout, the starting point's name and its photos, and clears the draft. Then it returns to the hub, with Open / Share on the new version. The Drive file keeps today's name, `Estimate-{id}-V{n}`, whatever the document label says; Share and email already know it.
6. **Save as template** (Owners and Admins) asks for a name (unique in the company; a clash is a 409 and the prompt stays open) and copies the current layout into a new template. Estimate-specific content is left out: photos added to Image blocks, and any text typed into the Note block.

**What prints when something is empty:** a data line with no value (no website, no phone, no description) is skipped, not printed as "N/A" as today; an Image block with no images and a Note block with no text are skipped whole, heading included; a layout with no Estimate block prints no pricing, and readiness says so. Readiness never blocks.

Data blocks show the estimate as it is and can't be retyped in the editor. To change a work item or the customer, the user edits the estimate (a link in the block's inspector), or retypes the words in a Text block, or edits the Google Doc afterwards. Data is read again at Generate, so a draft never prints stale prices.

## Blocks

Every block has an optional **heading** (prints as Heading 2), **Space above / below** (none / small / medium / large) and its own options, all in the inspector.

| Block | Content | Options | Per layout |
|---|---|---|---|
| **Company** | Logo (`logo_url`), name, address, phone, email, website | Show/hide each item; document label (Estimate / Proposal / Agreement / none) | any |
| **Customer** | Contact names, phone, email; property address | Show/hide each item | any |
| **Estimate** | Estimate #, title, created date, division, description; the work-items table (summary rows as today: optional # column, description with its recurrence note, amount); grand total; tax-included note | Show/hide each item; table style; number the rows | **at most one** |
| **Text** | Markdown typed in place (`MarkdownDescriptionEditor`), or saved text from the library; merge fields inserted with `{{` autocomplete | — | any |
| **Image** | Library images, then (document mode) photos from upload / Notes / Property | Size per image (large / medium / small, as today), caption | any |
| **Note** | Typed in place in document mode | Starter text (template) | **at most one** |
| **Signature** | Print-and-sign lines (no e-signature) | Customer and/or company; date; printed name | any |
| **Page break** | Starts a new page | — | any |
| **Divider** | A horizontal rule | Line weight; colour (gray / brand green) | any |
| **Spacer** | Empty vertical space | Height: small / medium / large (12 / 24 / 48 pt) | any |

Caps: a Text or Note block holds up to 5,000 characters (today's Notes cap); a document holds up to 30 photos across all its Image blocks (`MAX_DOC_IMAGES`, which keeps the PDF under Drive's 10 MB export cap and generation inside Render's memory).

Itemised work items (a Plant and Material Schedule) are v2.

Merge fields are grouped Company / Customer / Property / Estimate. They cover every placeholder today's template uses (`{{COMPANY_CONTACT}}`, `{{CATEGORY}}`, `{{GENERATED_DATE}}` …), so Standard Estimate can reproduce today's output. A field with no value shows as a highlighted `[Missing: …]` in the editor and raises a readiness warning.

## v1 scope

### Must
1. **Editor** (`DocumentEditor`), one component in two modes (see Context). On tablet and desktop it has three panes; on a phone, document mode shows the page only (D15):
   - **Palette:** block types; **Saved text** (insert; Owners and Admins also create / edit / delete in place); **Starter texts** (read-only, from code; insert, or "Save to my saved text" for Owners and Admins); **Images** (insert; Owners and Admins also upload / rename / delete).
   - **Page canvas:** one column of blocks rendered with real content: live data in document mode, sample data in template mode. Drag in from the palette; reorder by drag, keyboard or up/down; select to edit; duplicate; remove; type into Text and Note blocks in place.
   - **Inspector:** the selected block's options. In document mode, an Image block's inspector also has the photo sources. The **Document** tab holds name, description and division tags in template mode, and the starting point plus readiness in document mode.
   - No separate preview (D19): the canvas is drawn at the Doc's text width (468 pt) with the Doc's fonts and heading sizes, and shows each Page break block as a page edge. Automatic page overflow isn't shown.
2. **Settings → Document Templates** (Owners and Admins, flag on): the list shows name, description, division tags, block count and a Default badge. Actions: New (blank or from a built-in), Edit (opens the editor in template mode), Duplicate, Set default, Delete. Saving uses a version check ("Updated by X, reload").
3. **Documents hub** (the slimmed `DocumentsDialog`), as in The flow.
4. **Built-in templates:** **Standard Estimate** (= today's output) and **Full Estimate and Agreement**. Both are read-only, and both can be duplicated or used to start a document.
5. **Generation** from the editor (The flow, steps 5–6). Open, the edit window, PDF and email don't change.
6. **Flag:** env `DOCUMENT_TEMPLATES_ENABLED` / `VITE_DOCUMENT_TEMPLATES_ENABLED`, plus a per-company `Company.document_templates_enabled`, set by hand like `overage_billing_disabled`. With the flag off, today's dialog, the Text Blocks tab and the template all behave as today.
7. **Limits:** 20 templates per company; 60 blocks per layout; image library 50 images, each ≤ 5 MB; saved text keeps today's caps (100-character name, 5,000-character content); photos per document as today.

### Deferred (v2+)
- Retyping estimate data inside a document (a per-document override of a work item's description, say)
- Itemised work items
- Per-division saved-text defaults and locking (B4–B9, H1, DV-*)
- Options and Alternates (CX-2)
- Deposit, payment, schedule and agreement fields; "valid until" (D2); license and insurance numbers
- Two-column layouts
- A per-company editable style base (D12)
- Readiness blocking (G2)
- Conditional text (C4)
- Saved-text history (B8)
- Undo / redo history beyond the unsaved-changes guard; autosave
- E-signature
- Invoices and work orders

## Starter content

- **Standard Estimate:** Company, Customer, Estimate, Note, Image. The spike checks that its output matches today's doc.
- **Full Estimate and Agreement:** Standard Estimate, followed by Text blocks for the PRD's guide sections, in the PRD's order (Project identity → Work and pricing → Project conditions → Risk and performance → Approval and support), then a Signature block. Page breaks go between the groups.
- **Starter texts** (`starter_texts.py`): the same guide sections, one per section, each with the banner "Starter text. Have a local attorney review before use." They are read from code into the palette (D20) and are the source Full Estimate and Agreement is built from. Nothing is written to a company until someone inserts one.
  - *Content dependency:* product supplies the wording. The code ships with placeholder wording.

## Output engine — decided

**Compose the Google Doc with the Docs API, into a copy of the style base** (PRD design, approved):
1. Generation copies the fixed style-base Doc (fonts, heading styles, header, footer).
2. It appends each block as `batchUpdate` requests (text with paragraph styles, tables, inline images, page breaks). Named ranges per block are dropped from v1: nothing reads them back (restore-into-the-doc is v2), and they cost requests.

The engine reuses `doc_markdown.py`, `google_doc_images.py` (image rows as borderless tables), `_populate_work_items_table` and the PDF export.

The editor's canvas is rendered on the client from a context endpoint (D19); the composer is the only server-side rendering. PRD E4 accepts small drift ("Final layout may shift slightly in Google Docs").

**Composer approach:**
- Append in order at the document end.
- Batch consecutive non-table blocks into one `batchUpdate`.
- Re-read the document after each table insert (the existing `_populate_work_items_table` pattern).

**Spike at the start of step 2:** compose Standard Estimate and Full Estimate and Agreement into a copy of today's template with its body stripped. Confirm that headings, the work-items table, image rows, the inline logo and page breaks land correctly, and measure the call count and the time (see Risks).

## Data model

One layout shape serves templates, drafts and versions.

```python
class LayoutBlock(BaseModel):
    id: str                                  # uuid4 hex, stable across saves
    type: BlockType                          # company | customer | estimate | text | image | note | signature | page_break | divider | spacer
    heading: Optional[str] = None
    space_above: Spacing = "none"; space_below: Spacing = "none"
    props: dict                              # validated per type via BLOCK_REGISTRY

class DocumentTemplate(Document):            # "document_templates"
    company: PydanticObjectId
    name: str                                # unique per company (index)
    description: Optional[str] = None
    suggested_division_ids: List[PydanticObjectId] = []
    default_for_division_ids: List[PydanticObjectId] = []
    schema_version: int = 1
    blocks: List[LayoutBlock]
    version: int = 1                         # optimistic concurrency
    created_by_email / created_at / updated_by_email / updated_at

class DocumentImage(Document):               # "document_images": the image library
    company: PydanticObjectId
    name: str                                # unique per company
    storage_path: str; thumb_storage_path: str; width: int; height: int
    created_by_email / created_at / updated_at
```

- **Text block props:** `text` (markdown) and `source_text_block_id: Optional` (which saved text it was copied from, for the label only; never resolved again, D16).
- **Image block props:**
  - `library: [{image_id, size, caption}]`: references in a template.
  - `photo_ids: [str]`: document mode only. The photos themselves stay in the draft's or version's flat `images: List[DocImage]`, as today, and the block lists them by `DocImage.id` in print order. That keeps every piece of blob bookkeeping that exists (shared blobs across versions, `doc_image_trash.py`, `services/estimate_delete.py`, the PDF path) working on the flat list without walking blocks; only the composer reads `photo_ids`. A photo no block lists prints nowhere and is marked for deletion on the next save.
- **Note block props:** `text`.

Changes to existing models:
- **`Company`** gains:
  - `document_templates_enabled: bool = False`
  - `default_document_template_id: Optional[str] = None` (None means `builtin:standard`)

  The default lives on `Company`, so a built-in can be the default and there can never be two.
- **`DocDraft`** gains:
  - `blocks: Optional[List[LayoutBlock]]`: None on drafts saved before this change, which open as Standard Estimate with the old Notes and photos placed in its Note and Image blocks.
  - `started_from: Optional[StartedFrom]`: `{kind: blank|template|version, id, name}`.

  A draft's photos stay in `DocDraft.images`; its Image blocks point at them by id (above).
- **`GoogleDocsVersion`** gains `blocks: Optional[List[LayoutBlock]]` (the layout as generated, so "Copy of vN" can start from it) and `started_from`. `images` stays the flat photo list.

  The version keeps `additional_info` and `text_blocks` for rows made before this change; a "Copy of" one of those starts from Standard Estimate filled with them (`legacy.py`).

  **Size:** 60 blocks with up to 5,000 characters each is the worst case, at ~300 KB per version on the estimate document (16 MB cap). Per-version layouts stay well under that for any real estimate, but the 60-block and 5,000-character caps are what keep them there.

Template ids are strings wherever they're referenced (`builtin:standard`, `builtin:full-agreement` live in code, in `builtin.py`). The `/{id}` routes accept both forms, and writes to a built-in are refused (403).

## Backend work (`platform/`)
1. **Models and config:** the flag; the `Company` fields; `models/document_template.py` (with `LayoutBlock`), `models/document_image.py`; `DocDraft` / `GoogleDocsVersion` fields. Register in `models/__init__.py` and `database.py::DOCUMENT_MODELS`. Audit enums for templates and library images, with matching `ResourceType`s, as `TEXT_BLOCK_*` has.
2. **`services/document_templates/`:**
   - `blocks.py`: per-type props models, the registry, the "at most one" rule.
   - `builtin.py`, `starter_texts.py`.
   - `context.py`: the document context (`DocContext`): the merge-field dictionary, the company / customer / estimate lines and today's summary rows (`_work_item_rows`), built for a real estimate or for the sample one. The composer and the context endpoints both read it, so the canvas and the Doc print the same values.
   - `docs_composer.py`: blocks → batchUpdate requests and named ranges, plus `create_estimate_from_style_base(...)`. This stays out of `google_drive_service.py`, which is already 90 lines over the file-size line.
   - `sample_estimate.py`: the sample `DocContext` for template mode.
   - `legacy.py`: maps a pre-change draft or version (notes, text blocks, photos) onto Standard Estimate's layout.
3. **`routers/document_templates.py`** (modelled on `routers/text_blocks.py`). Template writes and library writes are manager-only; the reads the editor needs are open to every role. All routes return 404 when the flag is off. Register the router in `main.py`.
   - Templates: list / create / get / update / delete / duplicate / set-default.
   - `GET /sample-context`: the sample `DocContext` (template mode), with the merge-field catalogue.
   - `GET /starter-texts`: the starter texts, from code.
   - Image library: create / list / rename / delete.
   - `POST /from-estimate/{estimate_id}`: Save as template, manager-only.
4. **Saved text:** `routers/text_blocks.py` stays the library's API. Writes become manager-only if they aren't already. Delete stays unconditional (D16); only the library-image delete checks templates (D4).
5. **Estimate documents** (`routers/estimate_documents.py`, `routers/estimate_helpers/doc_versions.py`):
   - `doc-draft` takes `blocks` + `started_from`.
   - `generate-doc` takes the same (as a JSON `Form` field; the route is multipart) and composes from them, with the old fields still accepted while the flag is off.
   - Image specs are carried inside Image blocks.
   - `GET /estimates/{id}/doc-context`: this estimate's `DocContext` (every role that can read the estimate). Readiness is computed on the client from it (D19); the server validates only the layout's shape on save and generate.
   - Keep generate's fail-closed path and record through `append_doc_version_to_estimate` (the Brevo "first document generated" event).
6. **Tests** in `tests/document_templates/`:
   - Template CRUD and tenancy (modelled on `test_text_blocks_api.py`).
   - Block validation, including the one-Estimate and one-Note rules.
   - `DocContext` for a real estimate and the sample one; composer request snapshots per block.
   - Draft save / reopen with blocks; generate from blocks (Drive mocked), photos per Image block; "Copy of vN".
   - Legacy draft and version mapping.
   - Estimate delete and the trash sweep still remove every photo blob when photos sit behind Image blocks; a photo dropped from every block is marked for deletion.
   - Save as template drops photos and Note text.
   - Saved-text delete leaves template copies intact; library-image delete refused while a template uses it.
   - Flag off; built-ins read-only; Member 403 on template and library writes but 200 on draft and generate.
7. **User guide:** a section in `user_guides/users_guide.md` (feeds Maple's help).

## Frontend work (`portal/`)
1. `src/lib/documentTemplatesFlag.ts`; `.env.example`.
2. Types in `src/types/api.ts`; `src/api/documentTemplates.ts`, `src/api/documentImages.ts`.
3. **Editor** in `components/documentEditor/`:
   - `DocumentEditor` (mode prop), `BlockPalette`, `SavedTextLibrary` (reusing `TextBlockModals`), `StarterTexts`, `ImageLibrary`
   - `LayoutCanvas`, `BlockCard`, the per-type block renderers (shared by both modes, fed sample or live context)
   - `Inspector` and the per-type inspectors; `ImageBlockPhotos` reusing `DocImagePicker` / `useDocImageDraft`
   - `useDocContext` (live or sample), `readiness.ts` (pure: layout + context → warnings keyed by block id)
   - `ReadinessBar`
   - `useLayoutEditor.ts`: the reducer
   - Phone layout (D15): `AddBlockSheet`, `EditBlockSheet`, a sticky action bar; reorder with up/down only

   Drag and drop uses `@dnd-kit` + `sortableDrag.ts`. Keyboard reordering uses dnd-kit's keyboard sensor with announcements (`useDragAnnouncements`).
4. **Pages:**
   - `pages/DocumentTemplateEditorPage.tsx` (`/settings/document-templates/:id`).
   - `pages/EstimateDocumentEditorPage.tsx` (`/estimates/:id/document`).

   Both are gated in `App.tsx`.
5. **Settings:** the Document Templates tab (manager-only, flag-gated) via `components/settings/DocumentTemplatesTab.tsx` and `useDocumentTemplatesAdmin.ts`. The Text Blocks tab is hidden when the flag is on.
6. **Documents hub:** `DocumentsDialog.tsx` behind the flag keeps the versions list and gains the draft row and the Start a document chooser. Today's form (`useDocumentsForm.ts`) stays for the flag-off path only.
7. **Vitest coverage:** the reducer, `readiness.ts`, the block renderers in both modes, the inspectors, the libraries (manager vs Member), the hub's chooser, the editor's save / generate / leave guard, the phone layout's sheets and up/down reorder, and the flag.

## Delivery order
1. Backend: models, CRUD, built-ins, starter texts, image library, the context endpoints (sample + live), tests.
2. Docs composer, generate and draft from blocks, the legacy mapping; the flag-off path untouched.
3. The editor (template mode first: Settings tab and template pages).
4. Document mode: the hub, the estimate editor page, photos in Image blocks, readiness, Save as template.
5. The user guide, `.env.example`, full test runs.

Trunk-based: each step lands on `main` through `/commit`, behind the flags (off on prod), platform before portal. No PRs.

## Verification
- **Backend:** `scripts/start_test_mongo.sh`; `./run_tests.sh tests/document_templates tests/estimate_documents`; `./run_ruff.sh`; `./run_mypy.sh`.
- **Frontend:** `npm test`, `npm run typecheck`, `npm run lint`.
- **Manual,** with the flags on and Drive enabled:
  1. Duplicate Full Estimate and Agreement; add a saved text, a starter text and a library image; save; set it as default.
  2. On an estimate, open Documents → Start from it. The editor shows the estimate's data and the warnings are listed.
  3. Hide the Website in the Company block, delete one terms block, type a note, add photos to the Image block, then Save draft. Close, reopen and continue the draft.
  4. Generate. Open the doc and check the logo, the block order, the hidden item, the photos and the page breaks. Download the PDF.
  5. Start "Copy of v1": the same layout, with the photos carried.
  6. Save as template; the photos and the note are left out.
  7. As a Member: start, edit and generate. No library writes and no Settings tab.
  8. On a phone: start from a template, type a note, add a photo, move a block with up/down, Generate.
  9. Edit the template while a draft from it is open: the draft doesn't change (D18). Delete a saved text a template used: the template keeps its copy (D16).
  10. With the flag off: today's dialog and the Text Blocks tab are back.

## Risks the spike measures

- **Docs API write quota.** Every doc is written by the one service account, and the Docs API caps writes per minute per user (believed 60 at the time of writing; check the project's quota page). Only the Estimate table, image rows and Signature (if drawn as a table) force a re-read. Target: ≤ 12 writes for Full Estimate and Agreement. On a 429, retry once with backoff, then return the existing friendly 500.
- **Generate time** for the Full template, so the editor's progress copy is honest.
- **Standard Estimate parity** with today's doc, including the logo's position (D1).
- **Canvas vs Doc drift.** The canvas is the only preview (D19). The spike compares the two on both built-ins and fixes the canvas's widths, fonts and spacing to match; both read the same `DocContext`, so the values can't differ.

## Still to build in (from the 2026-11-06 review)

- **Library images:**
  - Stored in Firebase Storage like doc images, at `document_images/{company}/{image}`, with a thumbnail.
  - Placed in the Doc from a 10-minute signed URL, so the Doc keeps its own copy.
  - Placed into a **document**, a library image is copied into doc-image storage, as note photos are today, so a later library delete never touches a draft or version.
  - Templates reference library images, and D4 guards their delete.
  - The canvas shows library images and photos from their thumbnails, as the dialog does today.
- **Text safety.** All text is user input. The canvas renders markdown with the same component the app already uses for descriptions (no raw HTML), and the composer sends text, never markup, to the Docs API.
- **Tenant checks:**
  - Division ids and image ids in a layout go through `dependencies.assert_company_refs` on every write.
  - Templates load with `dependencies.own_record`.
  - A `started_from` id resolves within the estimate's company (404 for another company's id and for a missing one alike).
  - Live preview checks the caller's access to the estimate.
- **A template deleted after use.** `started_from.name` keeps the label on drafts and versions. "Start a document" simply no longer lists it.
- **Estimate delete and photo blobs.** `services/estimate_delete.py` and `doc_image_trash.py` read the flat `images` lists, so they need no change as long as photos stay there (Data model). A test pins that.
- **The user guide.** Its Documents steps (`users_guide.md` ~line 1247) and the Text Blocks section change, so Maple's help answers follow.
- **Concurrent editing of one draft.** There is one draft per estimate, shared by the company, as today. Saving over a newer draft is refused with "Dana saved a newer draft — reload" (the existing `saved_at` check). No live co-editing.
- **Maple and the customer MCP server.** Neither gets document tools in v1, and Maple's "template" keeps meaning work-item templates.
- **Settings tab bar.** With the flag on, Document Templates replaces Text Blocks, so there are still nine tabs.
- **Rule file.** Once the model settles, add `.claude/rules/document-templates.md` (paths `platform/services/document_templates/**`, `platform/routers/document_templates.py`, `portal/src/components/documentEditor/**`).

## Final review (2026-11-07)

Read end to end against the code once more. Fixed in place above: the editor's route and the way back to the hub (the hub is a dialog on the estimate page, so the editor is a page of its own and returns with `?documents=1`); what prints when a line, a block or the pricing is missing; the text and photo caps; photos kept in the flat `images` lists so the blob bookkeeping, estimate delete and the trash sweep don't change; readiness as a POST if it stays on the server; named ranges dropped; Save as template's name prompt; the Drive file name. Two proposals below each removed a module; Simon accepted both the same day (D19, D20), and the sections above are already written to them.

### Q9 → D19. Drop the server HTML preview; the canvas is the preview

The plan has three renderings of every block: the client canvas, the server HTML renderer behind "Preview as pages", and the Docs composer. The middle one exists only for pagination, and the PRD already accepts drift ("Final layout may shift slightly in Google Docs"). It also brings the sandboxed iframe, signed URLs for its images and a preview endpoint that renders user input.

*Decided:* no `html_renderer.py`, no `POST /preview`, no `PagesPreview`. Instead:
- The canvas is drawn at the Doc's text width (468 pt), with the same fonts and heading sizes, and shows explicit Page break blocks as a page edge; automatic overflow isn't shown.
- One context endpoint feeds it: `GET /estimates/{id}/doc-context` returns the merge-field values, the company/customer/estimate lines and the work-item rows; `GET /document-templates/sample-context` returns the same shape for the sample estimate. Both are read-only and open to every role that can read the estimate.
- Readiness is computed on the client from that context plus the layout (a missing field, an empty Note, no Estimate block), so `doc-readiness` goes too. The server still validates the layout's shape on save and generate.
- The real check of the output is Generate, then Open in Google Docs, which users do anyway.

Cost: no page count before generating. If that turns out to matter, the HTML renderer can come back in v2 as it is specified today.

### Q10 → D20. Don't seed starter texts into the company library

Seeding 21 texts into every company's saved-text list, on first open, clutters the library of a company that curated its own, needs a "Starter" badge to tell them apart, and the idempotence rule means a renamed starter comes back on the next open.

*Decided:* the starter wording lives in code (`starter_texts.py`) and shows in the palette as a read-only **Starter texts** group under the company's **Saved text**, inserted as copies like everything else (D16). The built-in Full Estimate and Agreement is built from the same source. Nothing is written to the company until someone inserts one; "Save to my saved text" on a starter copies it into the library for Owners and Admins. No seeding, no badge, no `(company, name)` clashes.

### Checked and fine
- Text block writes are already manager-only (`assert_is_manager` in `routers/text_blocks.py`); the list is open to all roles.
- Photos are staged in memory and sent as multipart files on Save draft and Generate today (`useDocImageDraft`, `docForm`), which is what the editor needs.
- `ESTIMATE_DOC_GENERATE` and `ESTIMATE_DOC_DRAFT_SAVE` audit actions exist; only the template and library actions are new.
- Open, the edit window, its sweeper, PDF export and email are untouched by any of this.
