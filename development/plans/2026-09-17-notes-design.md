# Notes v2: per-work-item, property and contact notes with attachments

**Date:** 2026-09-17
**Status:** Approved 2026-09-17 (decisions D1–D7 below). Implementation plan: [2026-09-17-notes-plan.md](2026-09-17-notes-plan.md).
**Scope:** `platform/` + `portal/` + `documentation/`

---

## 1. What exists today

"Notes" is three unrelated scalar strings, each edited in a plain textarea and
each carrying no author, no timestamp and no history:

| Field | Written from | Read by |
|---|---|---|
| `Estimate.notes` (`models/estimate.py:534`) | the Notes modal on the estimate page (`NewEstimateWithActivityPage.tsx:1381`), Maple's set/append handler (`agents/estimate/crud_handlers.py:2871`), the AI-generation path | **the generated customer document**, as the `NOTES` section / `{{NOTES}}` placeholder (`services/estimate_doc_generator.py:255,403`), Maple's details read-back |
| `Property.notes` (`models/property.py:16`) | the Property dialog textarea (`PropertyDialog.tsx:521`), Maple's property agent (`agents/property/text_helpers.py:96`) | nothing. `PropertyDetailPanel` does not render it |
| `Contact.notes` (`models/contact.py:27`) | the inline contact form (`ContactsPage.tsx:1055`), Maple's contact agent | `ContactDetailPanel.tsx:126` as plain text |

The card UI in the reference screenshot (heading, **Add note**, dated cards
with pencil and trash) does not exist anywhere in the codebase. It is the
target, not a starting point.

Two structural facts shape the design more than anything else:

1. **Work items have no identity.** `JobItem` (`models/estimate.py:462`) is an
   embedded model addressed only by its position in `Estimate.job_items`, and
   the only write path is `PUT /estimates/{id}` replacing the whole array
   (`routers/estimates.py:1144-1294`). Nothing can point at a work item today,
   which is why `job_item_merge.py` has to re-match LLM output by description
   similarity.
2. **Task media is the attachment precedent.** Tasks store photos and videos
   in MongoDB GridFS (`services/task_photos.py`), validate by magic bytes, build
   thumbnails with Pillow, stream videos in 1 MB chunks under a 50 MB cap, and
   serve bytes back through an authenticated API route rather than a public
   URL. The portal side (`TaskDialog.tsx`, `TaskPhotoGrid.tsx`,
   `TaskMediaButtons.tsx`, `lib/downscaleImage.ts`) already handles staging,
   previews, camera capture and a lightbox.

---

## 2. Decisions for you

Decided 2026-09-17. The design below reflects these answers.

| # | Question | Decision | Notes |
|---|---|---|---|
| D1 | **What happens to `Estimate.notes`?** It is printed on the customer's Google Doc under `NOTES`. Moving it into work items removes that section from every document. | **Leave it completely unchanged for now.** No relabel, no migration, no UI change. Its future is decided once the new notes system is live. | Maple's estimate-notes handler, the Notes modal and the document generator are untouched by this work. |
| D2 | Can a company **Owner** delete another person's note? | **Yes.** An Owner may **delete** any note in the company. **Editing** stays creator-only. Admins get no override. | Covers departed employees. Parent deletion still removes notes regardless of author. |
| D3 | Can notes be added to a work item on an estimate that is **not editable** (Sent, Won, Lost)? | **Yes, on every status, including Archived.** Notes are commentary, not estimate content, so they sit entirely outside the Draft/Review content lock. | Field notes on a won job are the most valuable kind. A hard-deleted estimate simply 404s as a parent. |
| D4 | Does **Duplicate estimate** copy notes? | **No.** The copy gets fresh work item ids and an empty feed. | Notes are conversation about a specific job, not a template. |
| D5 | Attachment storage | **GridFS behind the API, exactly as Tasks.** | Tenancy stays enforced by the same `assert_company_access` as everything else. Firebase Storage tokenized URLs (the support-attachment pattern) would allow inline `![img]` markdown but the token is an unrevocable bearer secret. |
| D6 | Placement in the Work Item dialog | **A collapsible Notes section at the bottom, below the totals ticket.** Collapsed by default; the header shows the count. | See §3.8 for the alternatives considered and the collapse behavior. |
| D7 | Author of migrated legacy property/contact notes | **The company's Owner** (the earliest-created if there are several). | Someone has to be able to edit them; with D2 any Owner can already delete them. |
| D8 | Notes on the **estimate as a whole**? (added after review, 2026-09-17) | **Yes.** A fourth parent type `estimate`, rendered as a Notes section at the bottom of the estimate page. Independent of the per-work-item feeds and of the untouched `Estimate.notes` scalar (D1). | Same components, same rules; only a new enum value and one more mount point. |

---

## 3. Design

### 3.1 One collection, four parents

A single `Note` document serves all four hosts. One model, one service, one
router, one set of portal components, one cascade rule, one cleanup path.

```python
# platform/models/note.py
class NoteParentType(str, Enum):
    WORK_ITEM = "work_item"   # parent_id = Estimate.id, work_item_id set
    ESTIMATE = "estimate"     # parent_id = Estimate.id, the estimate as a whole (D8)
    PROPERTY = "property"     # parent_id = Property.id
    CONTACT = "contact"       # parent_id = Contact.id

class NoteAttachmentKind(str, Enum):
    IMAGE = "image"; VIDEO = "video"; PDF = "pdf"

class NoteAttachment(BaseModel):
    file_id: PydanticObjectId                 # GridFS _id, bucket "note_attachments"
    thumb_file_id: Optional[PydanticObjectId] = None   # images only
    kind: NoteAttachmentKind
    filename: str
    content_type: str
    size_bytes: int
    uploaded_at: datetime

class Note(Document):
    company: PydanticObjectId
    parent_type: NoteParentType
    parent_id: PydanticObjectId
    work_item_id: Optional[str] = None        # required iff parent_type == WORK_ITEM
    body: str = Field(max_length=20_000)      # markdown, stored raw
    attachments: List[NoteAttachment] = []    # max 10 per note
    created_by_email: str                     # authorization key, lowercase
    created_by_name: str                      # display snapshot ("Simon Tang")
    created_at: datetime
    updated_at: datetime

    class Settings:
        name = "notes"
        indexes = [
            [("company", 1), ("parent_type", 1), ("parent_id", 1), ("created_at", -1)],
            [("company", 1), ("parent_type", 1), ("parent_id", 1), ("work_item_id", 1)],
        ]
```

Rejected: embedding `List[Note]` inside `JobItem`, `Property` and `Contact`.
Notes would then ride the whole-array `PUT /estimates` write, which makes
"only the creator may edit" unenforceable (the server cannot tell which note
in the replaced array changed), forces every note write to re-send all work
items, and gives attachments nothing stable to hang off. It would also mean
three copies of the same code.

`created_by_email` joins the protected-field list in `services/sparse_update.py`.
`models/note.py` imports nothing from `services/`
(`tests/test_models_layering.py` enforces this). All datetimes are aware UTC
(`datetime.now(timezone.utc)`), and `updated_at` is carried in every `$set`
because `@before_event` does not fire on `.set()`.

### 3.2 Stable work item ids (prerequisite)

Notes need something to point at, so `JobItem` gains an identity:

```python
class JobItem(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    ...
```

Rules that keep it stable across the whole-array `PUT`:

- `JobItemCreate` accepts an optional `id`. The rebuild at
  `routers/estimates.py:1270` carries it through.
- **Position fallback.** If an incoming item has no `id` and the current
  document has an item at the same position, the server reuses that item's id.
  This protects any portal tab or Maple path still sending id-less payloads
  after deploy, and old clients cannot orphan notes.
- New items with no id and no positional match get a fresh uuid.
- Duplicate (`estimates.py:919`) dumps with `exclude={"id"}` so the copy gets
  new ids (D4). Template-to-work-item and Maple's `_persist_added_job_items`
  construct `JobItem(...)` and get ids from the factory for free.
- **Removed-id cascade.** After the `$set`, the PUT handler computes
  `existing_ids − incoming_ids` and deletes those work items' notes and blobs
  (best-effort, in a background task). This is the only place a work item
  can disappear, so it is the only place the cascade needs to live.

**The backfill is a hard prerequisite.** Beanie's `default_factory` hands a
document loaded without `id` a *new* id on every load; a note created against
one of those would dangle after the next save. `scripts/backfill_job_item_ids.py`
(idempotent, `--apply`) must run on Dev and prod before the notes router is
enabled, and the note-create endpoint verifies `work_item_id` against the
persisted estimate.

Portal: `WorkItemV2` gains `id: string` (`lib/workItemV2.ts:69`), populated by
`jobItemToWorkItemV2` and round-tripped by `workItemV2ToJobItemPayload`.
`emptyWorkItem()` generates one with `crypto.randomUUID()` so a new work item
already carries its id when first saved. Rows keep `key={idx}` until a later
cleanup; nothing else changes.

`WorkItemSummary.job_item_index` is left alone. It is a different feature and
switching it is unrelated work.

### 3.3 API

New router `routers/notes.py`, prefix `/notes`, service `services/notes.py`.
Every route resolves the caller with `require_authenticated_user` and checks
`note.company == user.company`.

| Method | Path | Body / query | Notes |
|---|---|---|---|
| `GET` | `/notes` | `parent_type`, `parent_id`, `work_item_id?` | newest first, capped at 500 |
| `GET` | `/notes/counts` | `parent_type=work_item`, `parent_id=<estimate>` | `{work_item_id: count}` for the work-item list badges. Uses `get_pymongo_collection()` + `async for` (Beanie's `aggregate().to_list()` is broken under the pinned driver) |
| `POST` | `/notes` | `{parent_type, parent_id, work_item_id?, body}` | validates the parent exists, belongs to the company, and (work items) that the id is on the persisted estimate. Stamps `created_by_*` from the resolved user, never from the body |
| `PATCH` | `/notes/{id}` | `{body}` | creator only |
| `DELETE` | `/notes/{id}` | | creator or Owner; deletes blobs after the document (`$pull`-first ordering, as Tasks do) |
| `POST` | `/notes/{id}/attachments` | multipart `file` | creator only; atomic `$push`; 10-attachment cap |
| `GET` | `/notes/{id}/attachments/{att_id}` | `size=full\|thumb` | streams bytes with the stored content type; `thumb` 404s for video and PDF |
| `DELETE` | `/notes/{id}/attachments/{att_id}` | | creator only |

Error shapes follow the existing routers: 403 with a plain message, 404 for
missing or cross-tenant ids, 413 for oversize uploads, 415 for a rejected type.
There is no status-based 409: notes are writable whatever the parent's state.

### 3.4 Authorization

```python
def is_note_author(note: Note, user: User) -> bool:
    return note.created_by_email.strip().lower() == (user.email or "").strip().lower()

def assert_can_edit_note(note: Note, user: User) -> None:      # PATCH, attachment add/remove
    if not is_note_author(note, user):
        raise HTTPException(403, "Only the person who wrote this note can edit it")

def assert_can_delete_note(note: Note, user: User) -> None:    # DELETE
    if not (is_note_author(note, user) or user.role == UserRole.OWNER):
        raise HTTPException(403, "Only the note's author or a company owner can delete it")
```

Same case-insensitive comparison and the same Owner-only escape hatch the
estimate-delete guard uses (`routers/estimates.py:1385`); Admins get no
override (D2). Reading and creating are open to every member of the company.
Notes ignore the estimate's status entirely, including Archived (D3). A
hard-deleted parent 404s on create. Properties and contacts have no archived
state.

### 3.5 Attachments

Extract the reusable half of `services/task_photos.py` into
`services/media_blobs.py`, parameterized by bucket name: image validation and
magic-byte sniffing, thumbnail generation, `store_blobs`, `store_stream` with
the mid-stream cap and `abort()`, `read_blob`, `delete_blobs`. `task_photos.py`
becomes a thin wrapper bound to `task_photos`; `note_attachments.py` binds to
`note_attachments` and adds PDF. Behavior of Tasks is unchanged and its tests
keep passing untouched. This is the one refactor the feature justifies; it
avoids a second copy of 200 lines of validation and streaming code.

| Kind | Types | Cap | Thumbnail | Client pre-processing |
|---|---|---|---|---|
| image | jpeg, png, webp (HEIC normalized client-side) | 10 MB | 320 px JPEG | `downscaleImage()` to 1600 px |
| video | mp4, quicktime, webm | 50 MB | none | size check before upload |
| pdf | application/pdf, `%PDF-` magic | 10 MB | none | none |

Attachments render as a tile strip under the note body, not inline in the
markdown. Images open the lightbox; videos open a `<video controls>` modal;
PDFs open in a new tab from an object URL. Everything is fetched through the
authenticated API and turned into an object URL, exactly as
`usePhotoObjectUrl` does today.

### 3.6 Markdown

- **Editing:** reuse `MarkdownDescriptionEditor` (MDXEditor, already in the
  work item dialog) with `hideToolbarUntilFocus` and a shorter `minHeight`.
- **Rendering:** react-markdown + remark-gfm are installed. A new
  `components/notes/NoteMarkdown.tsx` supplies the light-surface component
  map. (`ChangeLogPanel` and `MapleMarkdown` both render white-on-brand, so
  there is no light map to extract; corrected 2026-09-17 while planning.)
- **Safety:** no `rehype-raw`, so raw HTML in a note renders as text.
  react-markdown's default `urlTransform` already strips `javascript:` URLs;
  links render with `target="_blank" rel="noopener noreferrer"`. The server
  stores the body raw and only enforces the 20,000-character cap. This is the
  first place one user's markdown renders for another user in the same
  company, so the test suite pins the no-HTML rule explicitly.

### 3.7 Shared portal components

```
portal/src/api/notes.ts                 list / counts / create / update / remove /
                                        uploadAttachment / removeAttachment / attachmentBlob
portal/src/hooks/useNotes.ts            fetch + optimistic add/edit/delete for one parent
portal/src/components/notes/
  NotesPanel.tsx        header ("Notes · 3"), Add note button, list, empty state, error line
  NoteCard.tsx          author · date · "edited" · own-note actions; body via NoteMarkdown;
                        attachment strip
  NoteComposer.tsx      MarkdownDescriptionEditor + staged attachments + Save/Cancel;
                        used for both add (inline at top of list) and edit (in place)
  NoteAttachmentStrip.tsx  tiles, add-file buttons (Photo w/ capture, Video, File),
                        upload progress, per-tile remove for own notes
  ConfirmDialog.tsx     (in common/) one shared confirm modal instead of an eleventh copy
```

`NotesPanel` props: `{ parentType, parentId, workItemId?, disabled?, disabledHint?,
maxHeight? }`. It owns its own fetch, so hosts mount it and forget it.
Current user comes from `getCurrentUser()`; a card's pencil renders only when
`note.created_by_email` matches the session email, and its trash renders for
the author or when the session role is `Owner`. The server enforces the same
rules anyway.

Save semantics: notes persist **immediately** on their own endpoints,
independent of whatever host they live in. Cancelling the Work Item dialog
does not undo a note. The composer says so in its footer the first time.

**New-note flow with attachments:** stage files with object-URL previews,
`POST /notes` on Save, then upload each staged file; a failed upload leaves a
retry chip on the tile (the Task create-mode pattern). Editing an existing
note uploads on selection.

### 3.8 UI: the Work Item dialog

Three placements were considered:

- **Collapsible bottom section below the totals ticket (chosen).** The ticket
  is the conclusion of the editing flow; commentary follows it. Nothing above
  it moves when notes expand, and the phone layout is the same stack.
- A second tab, "Details | Notes". Clean, but it hides the ticket while
  writing a note about the numbers, and the dialog has no tab pattern today.
- A collapsible block under Description. Expanding it pushes Materials and
  Activities off-screen mid-edit.

```
┌ Work Item ───────────────────────────────────────────────── ✕ ┐
│ Division ▾                                   Recurring ○      │
│ Description ...                                               │
│ Materials ...                                                 │
│ Activities ...                                                │
│ ┌ totals ticket ─────────────────────────────────────────┐   │
│ └────────────────────────────────────────────────────────┘   │
│                                                               │
│ ▾ Notes · 2                                    [ + Add note ] │
│ ┌───────────────────────────────────────────────────────────┐ │
│ │ Simon Tang · Sep 17, 2026 · edited              ✎   🗑    │ │
│ │ Customer wants the **east bed** done first.               │ │
│ │ [img] [img] [▶ video]                                     │ │
│ └───────────────────────────────────────────────────────────┘ │
│ ┌───────────────────────────────────────────────────────────┐ │
│ │ Ana Reyes · Sep 16, 2026                                  │ │
│ │ Gate code is in the PDF.                     [📎 gate.pdf] │ │
│ └───────────────────────────────────────────────────────────┘ │
│                                        [ Cancel ]  [ Save ]   │
└───────────────────────────────────────────────────────────────┘
```

Behavior details:

- **Collapse.** The header row (chevron, "Notes · N", Add note) is always
  visible; the list below is collapsed by default. Clicking the header
  toggles it; clicking **Add note** expands it and opens the composer. The
  open/closed choice is remembered in `sessionStorage` per estimate, the way
  the activity panel remembers its filter, so it does not snap shut every
  time the dialog reopens. The count is fetched even while collapsed so the
  header is informative.
- Pencil appears only on the caller's own notes; trash appears on own notes
  and, for Owners, on every note.
- **Unsaved work item:** the panel renders its header and the line
  "Save this work item to start adding notes." with the button disabled. The
  dialog's Save persists immediately in edit mode, so this only bites on a
  brand-new item or on the create page before the estimate exists.
- `canEdit=false` (Sent/Won/Lost/Archived) still allows notes (D3). The panel
  is never disabled by estimate status.
- The work-item list rows on the estimate page show a small note-count badge
  fed by `GET /notes/counts`, so notes are discoverable without opening every
  item.

### 3.8a UI: the estimate page (estimate-level notes, D8)

`NewEstimateWithActivityPage` mounts `<NotesPanel parentType="estimate" parentId={estimateId} />`
as the **last section of the page**, below the work items table and the
grand total, inside the same card styling as the work items block. It is
rendered only in edit mode (the estimate exists); the create page has no
estimate id yet and shows nothing. The section is not collapsible: it is
the end of the page, so nothing sits below it to push. Same rules as every
other feed, including writes on Archived estimates (D3). The list is
unbounded in height here (the page scrolls) and each feed is separate: an
estimate-level note never appears inside a work item's section.

### 3.9 UI: Properties

`PropertyDetailPanel` gets `<NotesPanel parentType="property" maxHeight="max-h-80" />`
directly **below the address/map row and above the Activity panel**. Notes
sit with the property's own facts; estimates and tasks, which are other
records, stay last. The panel keeps the detail column bounded the same way
the activity panel does.

Unlike the activity panel, the notes panel **is** mounted in the phone bottom
sheet. Photographing a site from a phone is the primary reason to attach an
image to a property note; leaving it desktop-only would miss the point.

The Notes textarea leaves `PropertyDialog` (§3.12).

### 3.10 UI: Contacts

`ContactDetailPanel.tsx:126` replaces the plain-text `Field label="Notes"` with
the same `NotesPanel`. It is the only rich block in that panel, so it gets no
height cap on desktop and the bottom-sheet treatment on phones. The Notes
textarea leaves the inline contact form in `ContactsPage.tsx`.

### 3.11 Phone

Same components, same stack. Specifics: the Photo button uses
`capture="environment"`; the composer's editor does not autofocus (keyboard
pop); the lightbox and video modal are `fullScreenOnMobile`; cards are
full-width with the action icons top-right at 44 px touch targets.

### 3.12 Migrating the legacy scalars

`scripts/migrate_legacy_notes.py` (idempotent, `--apply`, dry-run by default,
reports per company):

1. For every `Property` and `Contact` with non-empty `notes`, create one
   `Note` with `body` = the text (single newlines converted to markdown hard
   breaks so plain-text line breaks survive), `created_at` = the parent's
   `updated_at`, author = the company's earliest-created Owner (D7);
   companies with no Owner are listed and skipped.
2. Mark migrated parents by clearing the scalar to `null` so a re-run does
   nothing.
3. `Estimate.notes` is not touched (D1).

After the script has run on both environments, the scalar fields, their
request-model members, dialog textareas and Maple field maps are removed in a
follow-up commit, so an accidental early deploy cannot lose data.

### 3.13 Maple

Maple's property and contact agents currently write the scalar
(`agents/property/text_helpers.py:96`, `agents/contact/text_helpers.py:81`).
The phrasing stays supported and its handler switches to
`services/notes.create_note(...)` with the acting user as author, so "add a
note to 123 Main St: gate code 4411" produces a real note. Maple does not
attach files. The phrasing reference (§ Property, § Contact) is updated in the
same change, per CLAUDE.md. Work-item notes via Maple are out of scope for
this iteration; the estimate-notes handler is unchanged (D1).

### 3.14 Cascades and cleanup

| Event | Action |
|---|---|
| `DELETE /estimates/{id}` | delete every note with `parent_id` = estimate, both `work_item` and `estimate` parent types, then blobs, in the existing background cleanup task |
| `PUT /estimates/{id}` removes a work item | §3.2 removed-id cascade |
| `DELETE /properties/{id}`, `DELETE /contacts/{id}` | same cascade, inline (these are Owner/Admin-only and rare) |
| `scripts/cleanup/cleanup_company.py` | add the `notes` collection and the `note_attachments.files/.chunks` buckets, blob ids collected before the documents are deleted, mirroring `_delete_task_photo_blobs` |
| `tests/conftest.py` session cleanup | add `("notes", "company")` to `COMPANY_SCOPED_COLLECTIONS` |

Orphaned blobs from an aborted upload remain an accepted leak, as they are for
Tasks today.

---

## 4. Delivery phases

Each phase is independently shippable and gate-clean. Phases 1 and 2 must be
deployed and backfilled before Phase 4 is enabled.

| Phase | Repo | Content | Key tests |
|---|---|---|---|
| **1. Work item identity** | platform, portal | `JobItem.id`, `JobItemCreate.id`, position fallback, duplicate excludes id, `WorkItemV2.id` round-trip, `scripts/backfill_job_item_ids.py` | `test_estimate_api.py` (id preserved through PUT, fallback by position, duplicate gets new ids), `test_backfill_job_item_ids.py`, `workItemV2.test.ts` |
| **2. Notes backend** | platform | `models/note.py`, `services/media_blobs.py` extraction + `task_photos.py` wrapper, `services/note_attachments.py`, `services/notes.py`, `routers/notes.py`, cascades, cleanup script, conftest `COMPANY_SCOPED_COLLECTIONS` | `test_notes_api.py` (CRUD, tenancy, creator-only edit, Owner delete, archived estimates still writable, parent validation), `test_note_attachments.py` (types, caps, thumbs, streaming abort), `test_media_blobs.py`, existing `test_task_photos_api.py` untouched and green, `test_estimate_api.py` (removed-id cascade, delete cascade) |
| **3. Shared portal components** | portal | `api/notes.ts`, `useNotes`, `components/notes/*` (incl. `NoteMarkdown`), `common/ConfirmDialog.tsx` | `NotesPanel.test.tsx` (list, add, edit own, cannot edit others, delete confirm, empty and disabled states, no raw HTML), `NoteComposer.test.tsx` (staged uploads, retry chip), `NoteAttachmentStrip.test.tsx` |
| **4. Mount in hosts** | portal | Work Item dialog section + list badge, estimate page bottom section (D8), `PropertyDetailPanel` + phone sheet, `ContactDetailPanel` + phone sheet | `WorkItemInlineContent.test.tsx`, `PropertyDetailPanel.test.tsx`, `PropertiesPageMobileActivity.test.tsx`, `ContactDetailPanel.test.tsx` |
| **5. Migration and Maple** | platform, portal, documentation | `scripts/migrate_legacy_notes.py`, run on Dev then prod, remove scalars from models/routers/dialogs, Maple property/contact handlers create notes, phrasing reference + user guide updates | `test_migrate_legacy_notes.py`, `test_property_agent.py` / `test_contact_agent.py` (note phrasing creates a Note), `test_maple_crud_coverage.py` unchanged counts |

Cross-repo ordering: platform Phase 1 ships before portal Phase 1 (the server
must accept and preserve `id` before the client sends it); platform Phase 2
ships and is backfilled before portal Phase 4.

---

## 5. Testing

TDD throughout (CLAUDE.md). Beyond the per-phase files above, the suite pins:

- **Ownership:** a second Member in the same company gets 403 on PATCH,
  DELETE and attachment upload/delete; an Owner gets 403 on PATCH but 200 on
  DELETE; an Admin gets 403 on both; a user in another company gets 404.
- **Identity stability:** a note survives an estimate PUT that reorders,
  edits, and appends work items; it is deleted when its work item is removed;
  an id-less PUT of the same length preserves ids by position.
- **Attachments:** a mislabeled `.exe` with an `image/png` content type is
  rejected by magic bytes; a 51 MB video aborts mid-stream and leaves no
  note metadata; a PDF thumb request 404s.
- **Markdown safety:** `<script>` and `<img onerror>` in a body render as
  text; `javascript:` links render without an href.
- **Migration:** dry-run writes nothing; apply is idempotent; a company
  without an Owner is reported and skipped.
- **StrictMode:** `useNotes` and the composer's object-URL cleanup are
  exercised under `<StrictMode>` (the effect-flag bug that bit twice).
- Gates: `./run_mypy.sh`, `./run_ruff.sh`, `./run_bandit.sh` (B110 count must
  stay at 13), `npm run typecheck`, scoped `npm test`.

---

## 6. Out of scope

- Reactions, replies, @mentions, or notifications on notes.
- Anything to do with the legacy `Estimate.notes` scalar (D1: untouched until the new system is live). Estimate-level notes in the new system are in scope (D8).
- Notes on Tasks, Materials, People; Maple attaching files or writing
  work-item notes.
- Inline image embedding in markdown bodies.
- Migrating the ten existing open-coded delete-confirm modals to the new
  `ConfirmDialog` (a follow-up entry for `code-review-followups.md`).
- Switching `WorkItemSummary.job_item_index` to the new id.

---

## 7. Risks

| Risk | Mitigation |
|---|---|
| A note attached to a transient work item id before the backfill runs | Backfill is a listed prerequisite; the create endpoint validates against the persisted estimate; Phase 4 is not enabled until Phase 1 has run on prod |
| Old portal tab sends id-less `job_items` after deploy | Position fallback in §3.2, pinned by test |
| `media_blobs.py` extraction regresses Tasks | Task tests are run unchanged in Phase 2 and must stay green before the extraction is committed |
| Cross-user markdown becomes an XSS vector | No `rehype-raw`, explicit tests, server length cap |
| Notes on a large property feed grow unbounded | 500-row server cap, `max-h-80` scroll box in detail panels |
| `Estimate.notes` later needs migrating into the new system | The `Note` model and migration script are parent-agnostic; adding an `estimate` parent type or moving values onto work items is a Phase 5-style follow-up with no schema change |
