# Plan: Inline Work Item Expansion on Estimate Detail Page

## Context

The estimate detail page currently opens a modal dialog (`WorkItemDialog`) when users click a work item row. The user wants to replace this with an inline expansion — clicking a row expands it in-place to show the full work item form content, with an X to close. Only one item can be expanded at a time. When a work item expands, the Description & Details and Property & Preview collapsible sections auto-collapse to maximize space.

**No Save button inside the inline form.** Edits are live — changes propagate immediately to the parent's `workItems` state via an `onChange` callback. The user clicks "Save Estimate" to persist everything to the API.

## Approach

Extract the form content from `WorkItemDialog.tsx` into a new `WorkItemInlineContent.tsx` component. Refactor `WorkItemDialog` to be a thin Modal wrapper around this shared content. On the estimate page, render the inline content in a full-width `<tr>` below the expanded work item row (same `React.Fragment` pattern used on `MaterialsPage.tsx`).

## Files to Change

1. **`portal/src/components/estimates/WorkItemInlineContent.tsx`** (NEW) — extracted form content
2. **`portal/src/components/estimates/WorkItemDialog.tsx`** — refactor to thin wrapper
3. **`portal/src/pages/NewEstimateWithActivityPage.tsx`** — state changes, inline rendering

## Step 1: Create `WorkItemInlineContent.tsx`

Extract all state management and form JSX from `WorkItemDialog.tsx` (lines 50-918) into a new component.

**Props:** Same as `WorkItemDialogProps` minus `open`. Replace `onSave` with `onChange: (workItem: WorkItemV2) => void` callback. Add optional `readOnly?: boolean`.

**Key design — live editing, no Save button:**
- Internal state for all fields (division, description, materialRows, etc.)
- A `useEffect` watches all form state and calls `onChange(currentWorkItem)` whenever anything changes, updating the parent's `workItems` array immediately
- No Save/Cancel buttons — just an X to close (provided by parent wrapper)
- `isDirty` in the parent gets set to `true` on every `onChange` call
- "Save Estimate" button persists to API

**Key differences from dialog:**
- No Modal wrapper — renders form content directly
- No Save/Cancel footer — live editing via `onChange`
- `useEffect` for rateCards fetch triggers on mount (no `open` dependency — use key-based remount instead)
- Remove the state-reset `useEffect` (key-based remount handles this)
- EffortCalculatorDialog and RecurrenceDialog still render as child modals
- When `readOnly` is true, all form inputs are disabled

**Space optimizations:**
- Division + Recurring toggle on one row (side by side) instead of stacked
- Description textarea `min-h-[60px]` (down from 80px)
- Pricing breakdown stays as-is (already compact)

## Step 2: Refactor `WorkItemDialog.tsx`

Becomes a thin wrapper (~30 lines). The dialog still uses `onSave` — the `WorkItemInlineContent` onChange can feed into a local state snapshot, and Save button in the dialog's footer commits it.

```tsx
export default function WorkItemDialog({ open, onClose, onSave, ...rest }: WorkItemDialogProps) {
  const [current, setCurrent] = useState<WorkItemV2 | null>(null);
  return (
    <Modal open={open} title="Work Item" onClose={onClose} maxWidth="max-w-4xl"
      footer={/* Save/Cancel using current state */}>
      <WorkItemInlineContent
        key={open ? "open" : "closed"}
        onChange={setCurrent}
        {...rest}
      />
    </Modal>
  );
}
```

## Step 3: Update `NewEstimateWithActivityPage.tsx`

### State changes

Replace:
```ts
const [isWorkItemDialogOpen, setIsWorkItemDialogOpen] = useState(false);
const [editingWorkItemIndex, setEditingWorkItemIndex] = useState<number | null>(null);
```

With:
```ts
const [expandedWorkItemIndex, setExpandedWorkItemIndex] = useState<number | null>(null);
```

### Handler updates

```ts
const handleAddWorkItem = () => {
  const newItem = emptyWorkItem(companyDefaults);
  setWorkItems((prev) => [...prev, newItem]);
  setExpandedWorkItemIndex(workItems.length);
  setDescriptionExpanded(false);
  setPropertyExpanded(false);
};

const handleEditWorkItem = (index: number) => {
  setExpandedWorkItemIndex(index);
  setDescriptionExpanded(false);
  setPropertyExpanded(false);
};

// onChange from WorkItemInlineContent — updates workItems in real-time
const handleWorkItemChange = (workItem: WorkItemV2) => {
  if (expandedWorkItemIndex !== null) {
    setWorkItems((prev) =>
      prev.map((item, i) => (i === expandedWorkItemIndex ? workItem : item)),
    );
    setIsDirty(true);
  }
};

const handleCloseInline = () => {
  if (expandedWorkItemIndex !== null) {
    const item = workItems[expandedWorkItemIndex];
    const isEmpty = !item.description.trim() && item.materials.length === 0 && item.activities.length === 0;
    if (isEmpty) {
      setWorkItems((prev) => prev.filter((_, i) => i !== expandedWorkItemIndex));
    }
  }
  setExpandedWorkItemIndex(null);
};
```

### Table rendering

Inside the `<tbody>`, wrap each row in `React.Fragment`:

```tsx
{workItems.map((item, idx) => {
  const isExpanded = expandedWorkItemIndex === idx;
  return (
    <React.Fragment key={idx}>
      <tr className={`... ${isExpanded ? "bg-blue-50" : ""}`}
          onClick={() => isExpanded ? setExpandedWorkItemIndex(null) : handleEditWorkItem(idx)}>
        {/* existing cells */}
      </tr>
      {isExpanded && (
        <tr>
          <td colSpan={canEdit ? 6 : 5} className="p-0">
            <div className="border-t-2 border-blue-200 bg-white px-4 sm:px-6 py-4">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-sm font-semibold text-gray-800">
                  Work Item #{idx + 1}
                </h3>
                <button type="button" onClick={(e) => { e.stopPropagation(); handleCloseInline(); }}
                  className="text-gray-400 hover:text-gray-600" aria-label="Close work item">
                  <X className="w-5 h-5" />
                </button>
              </div>
              <WorkItemInlineContent
                key={expandedWorkItemIndex}
                onChange={handleWorkItemChange}
                initialData={item}
                materials={materials}
                people={people}
                companyId={COMPANY_ID}
                inventoryGaps={getInventoryGapsForWorkItem(inventoryGaps, idx)}
                onDismissGap={handleDismissGap}
                onAddMaterialGap={setMaterialGap}
                onAddRoleGap={setRoleGaps}
                readOnly={!canEdit}
              />
            </div>
          </td>
        </tr>
      )}
    </React.Fragment>
  );
})}
```

### Cleanup

- Remove `<WorkItemDialog>` render at bottom of file (lines 1555-1576)
- Remove `isWorkItemDialogOpen` state and `handleCloseDialog`
- Import `WorkItemInlineContent` and `X` icon
- Add `X` to lucide-react import (or use existing `XCircle`)

### Edge cases

- **Delete while expanded:** In `handleConfirmDeleteWorkItem`, if `expandedWorkItemIndex === removedIdx`, clear it. If `expandedWorkItemIndex > removedIdx`, decrement it.
- **Overflow:** Change table container from `overflow-hidden` to `overflow-visible` so SearchableSelect dropdowns aren't clipped.
- **No unsaved warning needed on switch:** Since changes are live (via onChange), switching to another work item doesn't lose edits.

## Verification

1. `npm run dev` — click a work item row, verify it expands inline with full form
2. Verify edits are immediately reflected in the work items table (e.g., description, total)
3. Verify only one row expands at a time
4. Verify Description & Details and Property & Preview auto-collapse
5. Verify X button closes the expanded area
6. Verify "Add Work Item" adds a row and expands it; closing an empty new item removes it
7. Verify "Save Estimate" persists all work item changes
8. Verify EffortCalculatorDialog and RecurrenceDialog still open as modals
9. Verify Inventory Gaps, AddMaterialGapDialog, and AddRoleGapDialog still work
10. Verify delete button on rows works correctly
11. `npm test` — run existing estimate page tests
12. `npm run lint` — verify no lint issues
