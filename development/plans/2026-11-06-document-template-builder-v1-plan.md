# Document editor and templates — v1 scope and implementation plan

Mockups: https://claude.ai/artifact/6KUnMnk1ww9C9dJAMKpS8p (Settings list, editor in template mode, Documents hub, editor in document mode, sample output). Redrawn 2026-11-07 for one editor.
PRD: "Document Builder" (14 pp, read in full).

**Status:** All 5 steps built (not yet committed); the live spike ran on 2026-11-07 against Dev Drive (results under step 2 below). Steps 3 and 4 are in Simon's manual test (his changes are listed under each). The full platform and portal suites haven't been run yet: they run when Simon asks.
- **2026-11-06:** reviewed against the code (platform 56e66ff, portal 89dd848).
- **2026-11-07:** reshaped by Simon three times that day:
  - A template is one top-down list of blocks: no sections, no columns.
  - Text Blocks and an image library move into the editor.
  - **One editor builds both templates and documents.** A document starts from a blank page, a template or an earlier version, and is then edited block by block with the estimate's data already filled in. This brings the PRD's per-estimate tailoring (A*, B10–B12, F2) into v1.
- **Q5–Q8** were answered the same day (D15–D18).
- **Final review, 2026-11-07** (the last section): gaps fixed in place; Q9 and Q10 accepted as D19 and D20. Nothing is open.
- **Step 1 built, 2026-11-07** (backend models, CRUD, built-ins, starter texts, image library, context endpoints; 42 tests in `tests/document_templates/`). Where it differs from the text below:
  - The image library has its own router and prefix, `/document-images` (`routers/document_images.py`), so its routes can't collide with `/document-templates/{id}`.
  - Saved-text create and update were **not** manager-only (only delete was); they are now, matching the Settings tab, which already hid them from Members.
  - Starter texts are the guide's **13** text and mixed sections (9–21). Sections 1–8 are data, covered by the Company, Customer and Estimate blocks (6 and 8 are v2).
  - Merge-field keys are today's placeholder names (`{{TITLE}}`, `{{COMPANY_CONTACT}}` …), plus `COMPANY_WEBSITE`, `CUSTOMER_PHONE`, `CUSTOMER_EMAIL`.
- **Step 2 built, 2026-11-07** (the Docs composer, draft and generate from blocks, the legacy mapping; tested against a Docs simulator, `tests/document_templates/fake_docs.py`, then live through `scripts/spike_document_composer.py`). Choices made in building it:
  - **No new style-base Doc to set up.** `GOOGLE_DRIVE_STYLE_BASE_ID` is optional; unset, the composer copies today's template and clears its body, keeping its header, footer and styles.
  - **Writes:** one per batch of tables plus one. In the simulator Standard Estimate with photos takes 3, Full Estimate and Agreement 3 (budget 12).
  - **The logo** goes into a paragraph reserved at the top of the Company block, in the last batch; if Google can't fetch it, that batch is resent without it.
  - **New photos carry an id the editor chooses** (`id` on an upload or note image spec, 32 hex), so an Image block can name a photo before it is stored. A photo no block names isn't kept.
  - **Library images are copied into the document on save** (source `library`) and listed first in their block's `photo_ids`; a saved document's Image blocks hold no library references.
  - **`GET /estimates/{id}/doc-start?source=blank|template|draft|version`** returns the layout, the start and the photos to carry: the one place legacy drafts and versions map onto Standard Estimate. It and `doc-context` live in `routers/estimate_document_layouts.py`.
  - A missing merge field prints as nothing; an unknown `{{FIELD}}` prints as typed. Merge values never read as markdown.
- **Spike, 2026-11-07** (Dev Drive, both built-ins with a logo and 5 photos, PDFs checked page by page):
  - **Writes and time:** Standard Estimate 3 writes, 3 reads, ~10 s; Full Estimate and Agreement 3 writes, 3 reads, ~10–12 s (5 pages). Well inside the budget of 12. The logo placed on both runs.
  - **Index rules held:** the work-items table, image rows with captions, bullets in starter texts, page breaks, the signature and the header/footer fields all landed where the simulator put them; nothing in the composer's index arithmetic needed changing.
  - **Fixed after the first run (tests added):** today's template keeps a logo placeholder picture in its **first-page header**, which today's flow swaps for the logo. It printed as a grey picture above the Company block's logo, so the composer now deletes every picture in the style base's headers. Headings were set with no space above or below; they now keep the style base's Heading 1/2 spacing, and body paragraphs stay tight. The built-ins' Estimate and Image blocks (no heading) start with medium space above, or they printed straight under the block before.
  - **For step 3's canvas:** headings take the template's Heading 1/2 space; body lines have none; Space above/below is 0 / 12 / 24 / 48 pt. The canvas copies these.
  - A worktree has no `platform/secrets/`; run the spike with `GOOGLE_DRIVE_CREDENTIALS_PATH` pointing at the main checkout's key.
- **Step 3 built, 2026-11-07** (template mode: Settings → Document Templates and `/settings/document-templates/:id`). Portal files: `components/documentEditor/` (`DocumentEditor`, `BlockPalette`, `LayoutCanvas`, `BlockView`, `Inspector`, `DocMarkdown`, `layoutReducer`, `blockDefaults`, `mergeFields`, `docStyles`, `useEditorLibraries`, `useTemplateEditor`), `pages/DocumentTemplateEditorPage.tsx`, `components/settings/DocumentTemplatesTab.tsx` + `useDocumentTemplatesAdmin.ts`, `api/documentTemplates.ts`, `api/documentImages.ts`, `lib/documentTemplatesFlag.ts`, `types/documentTemplates.ts`; `VITE_DOCUMENT_TEMPLATES_ENABLED` in `.env.example` (moved up from step 5). Choices made in building it:
  - **The markdown editor escapes `_` in merge fields** (it saves `{{COMPANY\_NAME}}`). The editor undoes that on every edit (`unescapeMergeFields`), and the composer's field pattern now ignores backslashes in a key too, for text saved any other way (test added).
  - **Merge fields go in through "Insert a field"** in the inspector (grouped Company / Customer / Property / Estimate, inserted at the cursor through a new `insertMarkdown` on the markdown editor's handle), not `{{` autocomplete, which MDXEditor has no hook for.
  - **A selected Text or Note block is the markdown editor**, with a "Prints as" preview under it when the text has fields; unselected, it shows as printed, a field with no value as a highlighted `[Missing: …]`.
  - **Leaving with unsaved changes:** Back asks, and closing the tab warns. Leaving through the app's own menu doesn't ask: the app uses `BrowserRouter`, which has no `useBlocker`. Step 4's document editor has the same limit unless the router changes.
  - **Flag:** the Settings tab reads the company only while the env flag is on. With both on, Document Templates replaces Text Blocks for Owners and Admins, and a Member sees neither. The editor route is always registered; the page itself refuses Members, a phone, and the flag off.
  - **Set as default** shows in the editor's top bar for a saved template with no unsaved changes; the list's star does the same.
- **Revised after Simon's first test, 2026-11-07** (D8, D16, D20, D4 above):
  - **Text Blocks are linked, not copied** (`saved_text` blocks). Templates and drafts check the link is the company's (`services/document_templates/refs.py`, 404 otherwise); deleting a Text Block a template links is a 409 naming the templates (`routers/text_blocks.py`); the composer prints the Text Block's content as it is at Generate (`ComposeInput.saved_texts`), and the version stores it as a typed Text block (`LayoutPlan.version_blocks`). A link to a deleted Text Block prints nothing and shows as deleted on the canvas.
  - **Text Blocks are managed under the templates** on Settings → Document Templates (the Text Blocks list, reused); the palette only inserts them.
  - **Starter texts, `GET /document-templates/starter-texts` and Full Estimate and Agreement are gone.** `TextProps` lost `source_text_block_id` / `source_starter_key` (unknown keys are dropped on read, so templates saved during testing still load).
  - **Layout:** the editor fills the content area (`h-full`, white); the centre is a grey desk with a Letter-sized white sheet. The top bar is the top-bar height and leaves room for the floating Maple button while the panel is closed.
  - **Deselect:** a click anywhere off a block on the page or the desk deselects it, and so does Escape. Clicks in the palette and the options panel don't (the palette adds under the selected block; the options panel edits it).
  - **Bug found in testing:** an empty template description crashed the save (a 500 the browser showed as "Failed to fetch"): the 500-character cap was applied to `None`. Fixed in `routers/document_templates.py`, with tests.

- **Step 4 built, 2026-11-08** (document mode). Portal: `pages/EstimateDocumentEditorPage.tsx` at `/estimates/:id/document?source=blank|template|draft|version&id=`; `components/estimates/DocumentsHub.tsx`; in `components/documentEditor/`: `documentPhotos.ts`, `useDocumentPhotos.ts`, `PhotoOptions.tsx`, `usePhotoThumb.ts`, `readiness.ts`, `ReadinessBar.tsx`, `startChoices.ts`, `useDocumentTemplatesOn.ts`; `lib/documentPaths.ts`. No platform change: step 2 built the routes. Choices made in building it:
  - **The hub is `DocumentsDialog` when document templates are on for the company;** today's dialog is untouched otherwise (it reads the company only while the env flag is on). The hub lists the versions (each with "From <start>"), the draft ("Continue draft", who saved it and when), and "Start a document": every template (D3 as revised: the company default picked), then Blank, then "Copy of vN" newest first. Starting while a draft exists asks ("Keep the draft" / "Start over"); the draft is replaced only when the new document is saved or generated.
  - **Back and a finished Generate return to `/estimates/:id/with-activity?documents=1`,** which opens the hub once the estimate has loaded and then drops the flag from the address.
  - **Photos:** one pool per document; each photo keeps its own size and caption (as today's `DocImage`), and an Image block names its photos in order. They're added in the selected Image block's options (Upload, From Notes, From Property, reusing the dialog's note picker and checks, one 30-photo cap across the document) and ordered there with up / down. A save reloads the layout and photos from the stored draft, so library images copied in by the server show as photos.
  - **Readiness** (never blocks): no Estimate block; an empty Note; a merge field with no value (Text, Note and linked Text Blocks); a linked Text Block that was deleted; an Image block with no images. A bar under the top bar counts them and lists them (a name there selects the block); each block gets a badge.
  - **Save as template** (Owners and Admins, tablet and desktop): a name prompt; a clash or the 20-template cap shows in it and it stays open.
  - **Phone (D15):** the page only, fitted to the screen; "Add a block" and "Edit block" open as bottom sheets; blocks move with up / down (no drag); Save draft and Generate sit in a bottom bar. Template mode stays tablet and desktop.
  - **Leaving with unsaved changes:** as in template mode, Back asks and closing the tab warns; the app's own menu doesn't ask.

- **After Simon's test of step 4, 2026-11-08:**
  - **The Note block is gone** (D11, D17). Server: `note` left `BlockType`, the registry, the composer and Save as template; Standard Estimate's Notes is a Text block (`std-notes`), and `legacy.py` puts an old document's notes there. A document from the editor stores `additional_info` as empty: its text is in its blocks. Portal: the palette, the options, readiness ("This Text block is empty") and the types follow. Nothing on Dev had saved a Note block, so no data changes.
  - **The hub's start section is "Generate a new document"** (Simon), with the intro "You can generate a new document using previous settings or choose an available template." It has two groups: **Previous Settings** first (this estimate's earlier versions, newest first, each "Version N · Generated <date> · from <start>"; shown only when there is one), then **Available Templates** (the company's templates by name, Standard Estimate, Blank). The latest version is picked by default; with no versions, the company's default template is (D3 as revised). A start from a version is named "Version N" (was "Copy of vN") in the editor's "Started from" line, the draft and the new version. Versions saved before the rename still stored "Copy of vN", so the portal names a version start by its number (`startName` in `lib/documentPaths.ts`), never by the stored name. **Start** sits beside **Close** in the dialog's footer. **Revised 2026-11-09 (Simon):** the group is **Previous Versions**, beside Available Templates where the dialog is wide enough, each version with a Delete; the intro reads "You can generate a new document from a previous version or choose an available template."

- **Step 5 built, 2026-11-08:** the user guide's section 9.8 (templates, Text Blocks, the image library, generating a document), with pointers from 7.2's Documents and a Documents tab in 7.8; `DOCUMENT_TEMPLATES_ENABLED` and `GOOGLE_DRIVE_STYLE_BASE_ID` in `platform/.env.example`; the rule file `.claude/rules/document-templates.md` and its row in `CLAUDE.md`. Not done: the full test runs (Simon's call).
- **Maple, 2026-11-08 (Simon):** asked to generate a document, Maple still makes none and now says the steps: today's dialog's (Document Details → Generate document) or, for a company with document templates, the editor's (Generate a new document → Previous Settings or Available Templates → Start → Generate), each with Share → Download PDF for a PDF. `out_of_chat._DOCUMENTS` / `DOCUMENTS_EDITOR`; the company is read in `agents/planner/execute.py` through `access.company_has_document_templates`. The planner's prompt is unchanged, so no parity run is owed. **Revised 2026-11-08:** with the per-company flag dropped, `access.document_templates_on()` (the env flag) picks the editor's steps, and they name Previous Versions.
- **Preset Blocks, 2026-11-10 (Simon):** on Settings → Documents and in the editor, Text Blocks are called **Preset Blocks**, with the intro "These are paragraphs that you can use again and again, such as warranty or payment terms. When you change the wording of a block, every template using it will be updated. A Preset Block used by a template cannot be deleted." The 409 on delete, the 404 for a missing link, the user guide's section 9.8 and Maple's documents note say Preset Block too. The model, API and code names are unchanged, and today's dialog and Settings tab (flag off) still say Text Blocks.
- **Content tab, 2026-11-10 (Simon):** the intro reads "Drag any Block onto the page, or click to add it below the selected block. If none selected, it will be added to the end of the page." The block types are in three sections, **From Estimate** (Company, Customer, Estimate, Signature), **Content** (Text, Image) and **Layout** (Divider, Spacer, Page break), then **Preset Blocks**, whose line "Change the wording in Settings → Documents → Preset Blocks" sits under its heading, then **Gallery** (the image library, was Images). A block added by a click (or a drop, or Duplicate) is scrolled into view on the page (`LayoutCanvas.useScrollToAdded`); selecting a block already there doesn't move the page. **Revised the same day:** From Estimate moved after Layout (Content, Layout, From Estimate, Preset Blocks, Gallery), and Gallery's Upload takes several files at once: one file is named first as before; several go in one after another, each named from its file (extension dropped), with "Uploading N images..." meanwhile, one reload at the end, and every refusal named under the list ("Uploaded 1 of 2. seal.png: …"; the 50-image cap is checked per upload).
- **Company block in the header, 2026-11-10 (Simon):** the Company block's **Print in** option is Body (the default; blocks saved before it print there) or Page header. Server: `CompanyProps.placement`, at most one in the header (`validate_layout`: "Only one Company block can go in the page header."); the composer writes it into page 1's header when the style base uses one (today's estimate template has a page-1 header holding only the logo placeholder, and a running header on later pages, which is kept), else the every-page header, made with `createHeader` if there's none; the header is cleared and the block written in the first batch, its logo in the last (one logo per segment). Portal: the reducer keeps a header block first and pinned (no drag, up or down; nothing moves above it), a duplicate prints in the body, the Page header option is disabled while another Company block has it, and the canvas draws a "Page header: prints at the top of page 1" line under it. Live spike (`--company-in-header`, Dev Drive): 2 writes, logo placed. **Revised 2026-11-11 (Simon): every page.** The block replaces the every-page header (the template's running company / customer: title header) and the style base's page-1 header is switched off (`useFirstPageHeaderFooter` false, so page 1 also takes the every-page footer); the canvas line reads "Page header: prints at the top of every page". Live spike over two pages: 3 writes, logo placed, the header on both pages.

- **Company block trimmed, 2026-11-11 (Simon):** no heading and no document label (the Standard Estimate's "Estimate" title went with it; a block saved with either prints neither, and its next save drops them). The logo is 40% smaller (fits 108 × 43.2 pt) with 8 pt under it, and the address prints as two lines: the street, then city, province, postal code and country. The readiness bar isn't drawn when there's nothing to check.

- **Text options, 2026-11-11 (Simon):** a Text block and a Preset Block each have Text size (Small 9 / Normal 11 / Large 13 pt), Line spacing (Single / 1.15 / 1.5 / Double) and Paragraph spacing (None / Small 6 pt / Medium 12 pt after each paragraph and list item but the last), set per block. The defaults print as before; a generated version keeps a Preset Block's options. Live spike (`--styled-text`, Dev Drive): 3 writes, Large / Double / Medium printed, the nested list spaced and bulleted.

- **Text options on the other blocks, 2026-11-11 (Simon):** the Company, Customer and Estimate blocks take the same Text size, Line spacing and Paragraph spacing (space after each line, and on both sides of the work items table); the sizes the composer sets itself (company name, tax note, signature labels) move 2 pt with Small or Large. The Signature block takes Text size only; the Image block and a Company block in the page footer take none. The live spike found the work items table's text style was set before the cell's named style, which the real API resets, so the header row had never printed bold; the order is fixed and the fake Docs now models the reset. Live spike (`--styled-blocks`, Dev Drive, two pages): 3 writes, Large / 1.5 / Small printed on every line and the table, the header row bold, the signature labels at 11 pt.
- **Library images are photos in a document, 2026-11-11 (Simon):** in the document editor, adding a library image puts it in the block's Photos (order, size, caption, remove like the others), sent as a new `library` image spec the server copies in; library images a start carries open as photos. Templates keep their Library images list; Save as template turns library photos back into library images.
- **Estimate block trimmed, 2026-11-11 (Simon):** no heading, estimate number, date or division; 12 pt under the title and the description; no "Work requested:" prefix. The tax-included note became a **Tax** option (on by default): the rows print before tax and "Tax: $X" sits just before the total, X being the grand total less the rows as printed so the page adds up. The sample estimate now carries 5% tax ($12,450.00 before tax, $622.50 tax, $13,072.50 total).
- **Customer block trimmed, 2026-11-11 (Simon):** no heading (Standard Estimate's "Customer" heading became medium space above); the property address comes right after the names, the street on its own line, then the phone and email. The editor's Show toggles follow that order. Live spike: 2 writes, printed as described.

- **Documents dialog reworked, 2026-11-11 (Simon):** "Generated versions" is **Versions**; each row has View (was the link on the version's name, now plain text) and **New draft from** before Share and Delete. The Previous Versions column and "Generate a new document" are gone. The draft section is **Draft**: the saved draft's **Continue draft**, as before, and **New draft**, which shows the Available Templates with Start in the footer (the company's default picked). With no draft it reads "No draft yet." beside New draft. Either new draft over a saved one asks first. Maple's documents steps (`out_of_chat.DOCUMENTS_EDITOR`) name New draft and New draft from. **Revised the same day (Simon):** no "Draft" heading; with no draft, New draft sits beside Close in the footer (the draft row keeps New draft beside Continue draft); New draft closes Documents and opens the templates in a "New draft" pop-up (Start, or Cancel, which closes it all); the version icons get an instant hover tooltip (`HoverTip`) in place of the browser's slow `title`. Settings → Documents' **New** opens a blank template with no Blank / Standard chooser; Duplicate builds on Standard Estimate. With no versions and no draft, Documents opens straight on the New draft pop-up.

- **Company block in the footer, 2026-11-11 (Simon):** Print in gains **Page footer** (at most one; one in the header as well is fine). It prints the name (bold), then the address, phone and email on one line, 8 pt and centred, in the every-page footer and page 1's own; no logo or website (their toggles are hidden). The style base's footer text goes but its page number stays ("PAGE n of m": the Docs API can't insert one), and page 1 keeps its own header. The editor pins the block last under a "Page footer" line. Live spike (`--company-in-footer`, Dev Drive, two pages): 3 writes, the footer on both pages with its page number. **Revised the same day (Simon):** left-aligned, and the phone and email on their own line under the address. Live spike: 2 writes, printed so.

- **The page preview fits the width, 2026-11-11 (Simon):** in the template builder and an estimate's document editor, the page zooms (CSS `zoom`, 0.4 to 2) to the width of its pane and follows a resize, so it never needs a sideways scroll. Drags divide their offset by the zoom; the block toolbar and the page's own labels keep their size. A phone already fits and isn't zoomed.

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

*Renamed 2026-11-07 (Simon):* the Settings tabs read **Work Items** (was Templates, the work-item templates) and **Documents** (was Document Templates). Only the labels and headings changed: the tab ids stay `templates` and `document-templates`, so links, Maple's page links and the `/templates` redirect keep working. Maple's link list and the user guide say Work Items; the user guide's Documents section comes with step 5.

## Decisions (2026-11-07)

| # | Question | Decision |
|---|---|---|
| D1 | Where the logo lives | **The Company block only.** It inserts `Company.logo_url` inline. The style base carries no image, so nothing replaces "the first image in the doc" any more. |
| D2 | "Valid until" date | **Not in v1.** Estimates have no such field. |
| D3 | An estimate's division | **Revised 2026-11-08 (Simon): templates aren't tied to divisions.** The hub lists every template the company has; the company default is preselected when the estimate has no versions. Templates have no division lists and the doc context no division ids. (First decided: suggested/default-for-division lists ordering and preselecting templates.) |
| D4 | Deleting a library item a template uses | **Refused with a 409 that names the templates**, for library images and (since D16 was revised) Text Blocks alike. Drafts and versions never block a delete: a version keeps the text it printed, and a draft's link to a deleted Text Block prints nothing. |
| D6 | Who may do what | **Members** start, edit and generate documents in the editor, including adding blocks and inserting saved text and library images. **Owners and Admins** also create and edit templates, manage the two libraries, and use "Save as template" from a document. Members don't see Settings → Document Templates. |
| D7 | Sections | **Dropped.** *(Revised 2026-11-07, Simon: the starter content went too, see D20; owners write their own Text Blocks.)* |
| D8 | Text Blocks | **Managed on Settings → Document Templates, under the templates; inserted from the editor's palette.** *(Revised 2026-11-07, Simon: was "move into the palette".)* With the flag on, the separate Text Blocks tab goes; with it off, the tab stays as it is today. The palette only inserts them. |
| D9 | Images | A company **image library** in the palette. In document mode, an Image block also takes photos: upload, from Notes, from Property, as the dialog does today. |
| D10 | Where block options are set | **In the editor**: on the template as its defaults, and again on each document. *(Revised: was "Builder only".)* |
| D11 | The Note block | **Dropped** *(2026-11-08, Simon)*: a typed Text block does its job. Standard Estimate has an empty Text block headed "Notes" (`std-notes`), typed into per document; empty, it prints nothing. Notes from documents made in today's dialog open there. |
| D12 | Style base | **One fixed system style** (today's template minus its body). Not editable per company in v1. |
| D13 | Layout blocks | **Page break, Divider, Spacer**, plus "Space above / below" on every block. No columns for now. |
| D14 | Generating | **The editor is the generator** (Simon, 2026-11-07). The Documents dialog shrinks to a hub: the versions list, the saved draft, and "Start a document". |
| D15 | Phones | **The same editor, page only.** Below tablet width the palette and the inspector open as bottom sheets ("Add a block", "Edit block"), blocks move with up/down buttons instead of drag, and Save draft / Generate sit in a sticky bottom bar. Template mode stays tablet and desktop only (a phone shows a notice). |
| D16 | Text Blocks in a layout | **Inserting a Text Block links it** (block type `saved_text`, props `{text_block_id}`). *(Revised 2026-11-07, Simon: was "copies it".)* The block can't be edited in the editor; changing the Text Block's wording changes every template that links it. The plain **Text** block, typed into on the page, stays. A document prints the Text Block as it reads at Generate, and the version records that text as a typed Text block, so a later edit or delete never changes a version or "Copy of vN". |
| D17 | Note vs Text | **Superseded by D11's drop** *(2026-11-08)*. Readiness warns about any empty Text block; Save as template keeps typed text and drops only photos. |
| D18 | Template edits and open drafts | **A draft keeps its own copy of the blocks** from the moment it started. Later template edits never reach an open draft or a version. |
| D19 | Preview | **The canvas is the preview.** No server HTML renderer, no preview endpoint, no iframe. The canvas is drawn at the Doc's text width with the Doc's fonts, fed by a context endpoint; readiness is computed on the client. The real check is Generate, then Open. |
| D20 | Starter texts | **Dropped** *(2026-11-07, Simon)*, with the Full Estimate and Agreement built-in made from them. Standard Estimate is the one built-in; owners write their own Text Blocks. |

## The flow

1. **Estimate → Documents** opens the hub. It has three parts:
   - The **versions** (Open / Share / Delete, as today), each labelled with what it started from.
   - The saved **draft**, if any: "Continue draft · saved 2 min ago by Dana".
   - **Start a document**: Blank, the company's templates (the default marked), the built-ins, and "Copy of v2" (any earlier version).

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
| **Company** | Logo (`logo_url`), name, address (street, then the rest), phone, email, website | Show/hide each item; Print in (body / page header / page footer); text size, line spacing, paragraph spacing (not in the footer). No heading or document label since 2026-11-11 | any |
| **Customer** | Contact names; property address (street, then the rest); phone, email | Show/hide each item; text size, line spacing, paragraph spacing. No heading since 2026-11-11 | any |
| **Estimate** | Title, description; the work-items table (summary rows: optional # column, description with its recurrence note, amount before tax when Tax is on); Tax line; grand total. No heading, estimate #, date, division or tax-included note since 2026-11-11 | Show/hide each item (Title, Description, Work items, Tax, Grand total); table style; number the rows; text size, line spacing, paragraph spacing | **at most one** |
| **Text** | Markdown typed in place (`MarkdownDescriptionEditor`), or saved text from the library; merge fields inserted with `{{` autocomplete | — | any |
| **Image** | Library images, then (document mode) photos from upload / Notes / Property | Size per image (large / medium / small, as today), caption | any |
| ~~**Note**~~ | *Dropped 2026-11-08 (D11): use a Text block.* | | |
| **Signature** | Print-and-sign lines (no e-signature) | Customer and/or company; date; printed name; layout; text size (labels) | any |
| **Page break** | Starts a new page | — | any |
| **Divider** | A horizontal rule | Line weight; colour (gray / brand green) | any |
| **Spacer** | Empty vertical space | Height: small / medium / large (12 / 24 / 48 pt) | any |

Caps: a Text block holds up to 5,000 characters (today's Notes cap); a document holds up to 30 photos across all its Image blocks (`MAX_DOC_IMAGES`, which keeps the PDF under Drive's 10 MB export cap and generation inside Render's memory).

Itemised work items (a Plant and Material Schedule) are v2.

Merge fields are grouped Company / Customer / Property / Estimate. They cover every placeholder today's template uses (`{{COMPANY_CONTACT}}`, `{{CATEGORY}}`, `{{GENERATED_DATE}}` …), so Standard Estimate can reproduce today's output. A field with no value shows as a highlighted `[Missing: …]` in the editor and raises a readiness warning.

## v1 scope

### Must
1. **Editor** (`DocumentEditor`), one component in two modes (see Context). On tablet and desktop it has three panes; on a phone, document mode shows the page only (D15):
   - **Palette:** block types; **Text Blocks** (insert as a link, D16; managed on Settings → Document Templates, D8); **Images** (insert; Owners and Admins also upload / rename / delete).
   - **Page canvas:** one column of blocks rendered with real content: live data in document mode, sample data in template mode. Drag in from the palette; reorder by drag, keyboard or up/down; select to edit; duplicate; remove; type into Text and Note blocks in place.
   - **Inspector:** the selected block's options. In document mode, an Image block's inspector also has the photo sources. The **Document** tab holds name and description in template mode, and the starting point plus readiness in document mode. **Revised 2026-11-10 (Simon):** two panes, not three. The left pane has two tabs, **Content** (the palette) and **Block** (the selected block's options; `SidePanel`). Clicking a block on the page opens Block, adding one keeps Content open, and deselecting returns to Content. The Document tab is gone: a template's description is edited under its name in the top bar, and a document's "Started from" was already in its top bar.
   - No separate preview (D19): the canvas is drawn at the Doc's text width (468 pt) with the Doc's fonts and heading sizes, and shows each Page break block as a page edge. Automatic page overflow isn't shown.
2. **Settings → Document Templates** (Owners and Admins, flag on): the list shows name, description, block count and a Default badge. Actions: New (blank or from a built-in), Edit (opens the editor in template mode), Duplicate, Set default, Delete. Saving uses a version check ("Updated by X, reload").
3. **Documents hub** (the slimmed `DocumentsDialog`), as in The flow.
4. **Built-in template:** **Standard Estimate** (= today's output), read-only; it can be duplicated or used to start a document. (Full Estimate and Agreement was dropped with the starter texts, D20.)
5. **Generation** from the editor (The flow, steps 5–6). Open, the edit window, PDF and email don't change.
6. **Flag:** env `DOCUMENT_TEMPLATES_ENABLED` / `VITE_DOCUMENT_TEMPLATES_ENABLED`, plus a per-company `Company.document_templates_enabled`, set by hand like `overage_billing_disabled`. With the flag off, today's dialog, the Text Blocks tab and the template all behave as today. **Revised 2026-11-08 (Simon):** the per-company flag is dropped; every company has the feature while the env flags are on.
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
- *Dropped 2026-11-07 (D20):* Full Estimate and Agreement and the 13 starter texts it was built from.

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
- *(The Note block and its props were dropped on 2026-11-08, D11.)*

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
   - `builtin.py` (Standard Estimate; `starter_texts.py` was dropped, D20).
   - `context.py`: the document context (`DocContext`): the merge-field dictionary, the company / customer / estimate lines and today's summary rows (`_work_item_rows`), built for a real estimate or for the sample one. The composer and the context endpoints both read it, so the canvas and the Doc print the same values.
   - `docs_composer.py`: blocks → batchUpdate requests and named ranges, plus `create_estimate_from_style_base(...)`. This stays out of `google_drive_service.py`, which is already 90 lines over the file-size line.
   - `sample_estimate.py`: the sample `DocContext` for template mode.
   - `legacy.py`: maps a pre-change draft or version (notes, text blocks, photos) onto Standard Estimate's layout.
3. **`routers/document_templates.py`** (modelled on `routers/text_blocks.py`). Template writes and library writes are manager-only; the reads the editor needs are open to every role. All routes return 404 when the flag is off. Register the router in `main.py`.
   - Templates: list / create / get / update / delete / duplicate / set-default.
   - `GET /sample-context`: the sample `DocContext` (template mode), with the merge-field catalogue.
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
   - `DocumentEditor` (mode prop), `BlockPalette`, a Text Blocks list (insert only, D8), `ImageLibrary`
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
  1. Add two Text Blocks on Settings → Document Templates. Duplicate Standard Estimate; insert a Text Block, a typed Text block and a library image; save; set it as default. Edit the Text Block's wording: the template shows the new wording. Try deleting it: refused, naming the template.
  2. On an estimate, open Documents → Start from it. The editor shows the estimate's data and the warnings are listed.
  3. Hide the Website in the Company block, remove a Text Block, type a note in the Notes Text block, add photos to the Image block, then Save draft. Close, reopen and continue the draft.
  4. Generate. Open the doc and check the logo, the block order, the hidden item, the photos and the page breaks. Download the PDF.
  5. Generate a new document from Previous Settings → Version 1 (picked by default): the same layout, with the photos carried.
  6. Save as template; the photos are left out.
  7. As a Member: start, edit and generate. No library writes and no Settings tab.
  8. On a phone: start from a template, type a note, add a photo, move a block with up/down, Generate.
  9. Edit the template while a draft from it is open: the draft doesn't change (D18). Delete a Text Block a template uses: refused, naming the template (D16).
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
  - Image and Text Block ids in a layout go through `dependencies.assert_company_refs` on every write.
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

### Q10 → D20. Don't seed starter texts into the company library (superseded: starter texts dropped, see D20)

Seeding 21 texts into every company's saved-text list, on first open, clutters the library of a company that curated its own, needs a "Starter" badge to tell them apart, and the idempotence rule means a renamed starter comes back on the next open.

*Decided:* the starter wording lives in code (`starter_texts.py`) and shows in the palette as a read-only **Starter texts** group under the company's **Saved text**, inserted as copies like everything else (D16). The built-in Full Estimate and Agreement is built from the same source. Nothing is written to the company until someone inserts one; "Save to my saved text" on a starter copies it into the library for Owners and Admins. No seeding, no badge, no `(company, name)` clashes.

### Checked and fine
- Text block writes are already manager-only (`assert_is_manager` in `routers/text_blocks.py`); the list is open to all roles.
- Photos are staged in memory and sent as multipart files on Save draft and Generate today (`useDocImageDraft`, `docForm`), which is what the editor needs.
- `ESTIMATE_DOC_GENERATE` and `ESTIMATE_DOC_DRAFT_SAVE` audit actions exist; only the template and library actions are new.
- Open, the edit window, its sweeper, PDF export and email are untouched by any of this.
