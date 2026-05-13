# Plan: WYSIWYG Markdown Editor for Estimate & Work Item Descriptions

## Context

Today the estimate description (`NewEstimateWithActivityPage.tsx` line 1046) and the work item description (`WorkItemInlineContent.tsx` line 370) are plain `<textarea>` inputs. The end users are landscapers — not technical — so the editor must show formatted text visually (bold actually looks bold) rather than expose raw markdown syntax. The persisted value stays a markdown string so the backend (`Estimate.description`, `WorkItem.description`) is unchanged.

Requested toolbar: text style (Normal / H1–H6), bold, italic, strikethrough, inline code, clear-all, bullet list, numbered list, link.

## Library: `@mdxeditor/editor`

WYSIWYG markdown editor for React: renders the document like a word processor, but `markdown` in / `onChange` out are plain markdown strings. Toolbar is plugin-based, so we include only the features the user listed. Has a built-in `readOnly` prop for non-editable contexts. Ships its own CSS (one stylesheet import).

The toolbar primitives that map directly onto the user's requirements:
- `BlockTypeSelect` — single "Paragraph / Heading 1–6" dropdown (covers "normal + headings").
- `BoldItalicUnderlineToggles` (configured for Bold + Italic only).
- `StrikeThroughSupSubToggles` (configured for Strikethrough only).
- `CodeToggle` — inline code.
- `ListsToggle` — bullet + numbered.
- `CreateLink` — link insertion dialog.
- Custom "Clear all" button — calls the editor ref's `setMarkdown('')`.

Plugins required: `headingsPlugin()`, `listsPlugin()`, `linkPlugin()`, `linkDialogPlugin()`, `markdownShortcutPlugin()`, `toolbarPlugin({ toolbarContents })`. No `codeBlockPlugin` — only inline code is wanted.

## Files to Modify

### New
- **`portal/src/components/common/MarkdownDescriptionEditor.tsx`** — shared wrapper around `MDXEditor` that:
  - Props: `value: string`, `onChange: (v: string) => void`, `onBlur?: () => void`, `placeholder?: string`, `readOnly?: boolean`, `minHeight?: number`, `autoFocus?: boolean`.
  - Forwards a ref to the underlying `MDXEditor` (for `setMarkdown` access from the Clear-all toolbar button).
  - Toolbar order: **BlockTypeSelect** · separator · **Bold / Italic** · **Strikethrough** · **CodeToggle** · **Clear-all** · separator · **ListsToggle (bullet, number)** · separator · **CreateLink**.
  - Imports `@mdxeditor/editor/style.css` once at module top.
  - Wrapper div applies the existing Tailwind border/rounded/padding look so it visually matches the surrounding inputs; min-height passed through.
  - `readOnly` is forwarded to `MDXEditor`'s `readOnly` prop (toolbar hidden, content not editable but still rendered WYSIWYG).
- **`portal/src/components/common/MarkdownDescriptionEditor.test.tsx`** — vitest + RTL coverage for: value renders, `onChange` fires with a markdown string on edit, `onBlur` fires when focus leaves, `readOnly` hides the toolbar, the Clear-all button empties the value.

### Edited
- **`portal/src/pages/NewEstimateWithActivityPage.tsx`**
  - Lines ~1046–1054 (edit branch): replace `<textarea ref={descriptionInputRef} … />` with `<MarkdownDescriptionEditor value={description} onChange={setDescription} onBlur={handleDescriptionBlur} placeholder="Enter estimate description..." minHeight={140} autoFocus />`.
  - Lines ~1066–1075 (read-only branch): keep using `MapleMarkdown` for display when not editing — replace the `whitespace-pre-wrap` div with `<MapleMarkdown>{description}</MapleMarkdown>` (retain the empty-state placeholder when `description` is blank). Reason: faster paint than spinning up an editor instance, and visual output matches.
  - `descriptionInputRef` becomes unused — drop the ref and the focus-on-edit `useEffect` (the editor accepts `autoFocus`).
  - `handleDescriptionBlur` keeps its dedup-via-`lastSavedDescriptionRef` logic unchanged.
- **`portal/src/components/estimates/WorkItemInlineContent.tsx`**
  - Lines ~368–377: replace `<textarea … />` with `<MarkdownDescriptionEditor value={description} onChange={setDescription} placeholder="Describe this work item..." readOnly={readOnly} minHeight={140} />`. The parent-propagating `useEffect` (lines ~109–120) keeps working unchanged.
- **`portal/package.json`** — add `@mdxeditor/editor` to `dependencies`.

## Reused Existing Code

- `portal/src/components/Layout/MapleMarkdown.tsx` — already configured with `react-markdown` + `remark-gfm`; used for the estimate description read-only branch.
- `handleDescriptionBlur` / `autoSaveField` in `NewEstimateWithActivityPage.tsx` (lines 760–782) — unchanged; mdxeditor's `onBlur` fires when focus leaves the editor surface.

## Out of Scope

- No backend / model changes — `Estimate.description` and `WorkItem.description` remain `str`.
- The estimate **title** (`EstimateTitleBar.tsx`) stays a plain textarea — only descriptions were requested.
- No code blocks, tables, images, headings beyond H6, or thematic breaks — the user's toolbar list is the full feature set.

## Verification

1. `cd portal && npm install` (pulls in `@mdxeditor/editor`).
2. `cd portal && npm test -- MarkdownDescriptionEditor` — new unit tests pass.
3. `cd portal && npm run dev`, then in the browser:
   - **Estimate description**: open an estimate, click into the description, exercise every toolbar control (BlockTypeSelect through each heading level + paragraph, bold, italic, strikethrough, code, bullet list, numbered list, link, clear-all). Tab out — confirm `PATCH /estimates/{id}` fires once and the markdown round-trips on reload; the non-editing read-only view shows formatted output via `MapleMarkdown`.
   - **Work item description**: open a work item in the inline panel, exercise the same toolbar controls, save the work item, re-open — formatting round-trips. Open the work item in a read-only context and confirm the toolbar is hidden but content still renders WYSIWYG.
4. `cd portal && npm run lint && npm run build` — no new type or lint errors.
