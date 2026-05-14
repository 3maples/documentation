# Plan — "Look Inside"-style live indicator on the Meet Maple widget

## Context

On `website/index.html`, the **Meet Maple** section (`#maple`, lines 991–1032) embeds a fully-functional React chat widget (`<div id="maple-widget">` mounted by `website/widget/index.tsx`). Visitors can type a question and get a real LLM response — but visually, the widget can read as just a styled screenshot of a chat UI, so most won't try it. We want a small, on-brand visual affordance — modeled on Amazon's "Look Inside" badge — overlaid on the widget to communicate "this is live, click here, try it."

The site is hand-rolled HTML/CSS (no Tailwind, no React for the landing page chrome) with all styles inline in a `<style>` block. There's already a precedent for a live-status pill: the `.coming .chip.live` pattern at `index.html:601–602` uses the brand accent color plus a small dot. We should reuse that visual language so the new badge feels native to the site, not bolted on.

## Recommended approach

Add a small absolutely-positioned **"TRY IT LIVE"** badge anchored to the top-left of the `.maple-try` container, floating slightly over the widget's top edge (Amazon-style — outside the widget on the top, with a small downward arrow tip pointing into it). The badge:

- Uses the existing accent color and pill geometry (`border-radius: 999px`, accent background mix) for visual consistency with `.chip.live`.
- Includes a **pulsing dot** to imply real-time / interactivity (reusing the `::before` dot from `.chip.live`, plus a new `@keyframes pulse` animation — current site has no pulse keyframe, only the caret blink at line 557).
- Has a small **▾ arrow tip** under the pill, pointing down into the widget (the "Look Inside" affordance — communicates "interact with what's below me").
- Is `aria-hidden="true"` since the widget itself is the interactive element; screen-reader users already get the widget's own affordances.
- Disappears (or shrinks/repositions) on mobile (`max-width: 900px`) so it doesn't crowd the widget header when the split collapses to one column.

### Files modified

- **`website/index.html`** — exactly one file. Two small changes:
  1. CSS additions in the `<style>` block near the existing `.maple-sec` rules (~line 480 area).
  2. One markup addition inside `.maple-try` (~line 1026), just before `<div id="maple-widget">`.

No JavaScript changes. No new dependencies. The widget code under `website/widget/` is untouched.

### CSS to add (near `.maple-sec` / `.maple-split` rules, ~line 480)

```css
.maple-try { position: relative; }

.maple-try-tag {
  position: absolute;
  top: -14px;
  left: 24px;
  z-index: 2;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 999px;
  background: color-mix(in oklab, var(--accent) 14%, var(--surface));
  color: var(--accent);
  border: 1px solid color-mix(in oklab, var(--accent) 35%, transparent);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  box-shadow: 0 6px 18px -10px rgba(42, 37, 70, 0.45);
}
.maple-try-tag::before {
  content: '';
  width: 7px; height: 7px; border-radius: 50%;
  background: var(--accent);
  animation: maple-pulse 1.8s ease-in-out infinite;
}
.maple-try-tag::after {
  /* Small downward arrow tip — the "Look Inside" affordance */
  content: '';
  position: absolute;
  bottom: -5px;
  left: 18px;
  width: 10px; height: 10px;
  background: inherit;
  border-right: 1px solid color-mix(in oklab, var(--accent) 35%, transparent);
  border-bottom: 1px solid color-mix(in oklab, var(--accent) 35%, transparent);
  transform: rotate(45deg);
}
@keyframes maple-pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50%      { opacity: 0.45; transform: scale(0.85); }
}
@media (max-width: 900px) {
  .maple-try-tag { top: -12px; left: 12px; font-size: 10px; padding: 5px 10px; }
}
```

### Markup change (`index.html:1026`)

```html
<div class="maple-try">
  <span class="maple-try-tag" aria-hidden="true">Try it live</span>
  <div id="maple-widget" data-signup-url="https://app.3maples.ai"></div>
</div>
```

### Why not other options

- **Ribbon across the top corner** — visually heavier, harder to make on-brand without redesign work.
- **Arrow + "Try it →" text floating beside the widget** — uses horizontal space we don't have inside the 3fr/7fr split, and shifts layout on mobile.
- **Full-width banner above the widget** — looks like a system notice, dilutes the chat's primacy as the section's focal point.

The chosen badge keeps the widget itself as the hero, adds minimal visual chrome, and mirrors the affordance language users already understand from Amazon's "Look Inside."

## Verification

1. Open `website/index.html` in a browser (open the file directly, or `cd website && python3 -m http.server`).
2. Scroll to the **Meet Maple** section — confirm the "TRY IT LIVE" pill sits on the top-left of the widget with the green dot pulsing and a small arrow tip pointing down into it.
3. Resize to <900px wide — confirm the badge shrinks slightly and stays anchored to the widget; widget remains usable and badge doesn't overlap interactive controls.
4. Type a real message into the widget to confirm interactivity is unaffected (no `pointer-events` regressions from the absolute overlay — the badge uses `z-index: 2` but only covers a small corner outside the widget's input area).
5. Visual sanity-check in light mode; the site has no dark-mode toggle so a single theme pass is sufficient.

## Out of scope

- No changes to the React widget itself (`website/widget/`).
- No copy changes elsewhere on the page.
- No analytics event for "saw badge" — can be added later if engagement data is wanted.
- No changelog entry (per house rule, only when the user explicitly asks).

## Critical files

- `/Users/simon/Development/Tangz/3maples/website/index.html` — the only file modified.
  - CSS block: insertion point near line 480, after the `.maple-split` rule.
  - Markup: insertion point at line 1026 inside `.maple-try`.
- `/Users/simon/Development/Tangz/3maples/website/widget/MapleWidget.tsx` — referenced only to confirm the widget is genuinely interactive; **not modified**.
