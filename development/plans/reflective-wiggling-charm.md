# Portal UI v2 Facelift Plan

## Context
The two design mockups (`dashboard.png` and `dashboard-maple.png`) show a significantly refreshed UI for the portal. The main changes are: a dark sidebar, redesigned dashboard with summary cards + bar chart + pipeline status, new header branding, colored division badges on estimates, and a purple-accented Maple AI panel. This plan applies the new visual language across all pages while preserving all existing functionality.

---

## Design Analysis (extracted from PNGs)

### Color Scheme
| Token | Current | New (from mockups) |
|---|---|---|
| Sidebar bg | `#ffffff` (white) | `#334155` (slate-700, dark navy) |
| Sidebar text | `#1e293b` | `#ffffff` (white) |
| Sidebar active item bg | `#f1f5f9` | `rgba(255,255,255,0.12)` (white overlay) |
| Sidebar active text | `#334155` | `#ffffff` |
| Sidebar hover | `#f3f4f6` | `rgba(255,255,255,0.08)` |
| Sidebar red accent bar | none | `#dc2626` (red-600, top bar) |
| AI panel input bg | white | `#f0eef6` (light lavender) |
| AI panel send button | slate-700 | `#6c5ce7` (purple/indigo) |
| Dashboard hero card bg | none | `#334155` (Total Pipeline card) |
| Division badge colors | gray | orange (#ea580c), green (#16a34a), yellow (#ca8a04), blue (#2563eb) |
| Pipeline status dots | none | green (#16a34a), blue (#3b82f6), amber (#f59e0b), red (#ef4444), gray (#9ca3af) |

### Layout Changes
- **Sidebar**: Dark background, white text, red accent line at top, user section at bottom
- **Header**: "POWERED BY 3Maples" branding with logo on the right side 
- **Dashboard**: Completely new layout with 3 summary cards, bar chart, pipeline status, recent estimates table
- **AI Panel**: "Maple AI" title, purple/lavender accent on input area, pill-style suggestion chips
- **Nav labels**: Keep "Estimates" as-is

---

## Implementation Phases

### Phase 1: Theme & CSS Variables
**Files:** `portal/src/styles/theme.css`, `portal/src/index.css`

- Update sidebar CSS variables in `:root`:
  - `--sidebar: #334155`
  - `--sidebar-foreground: #ffffff`
  - `--sidebar-primary: #ffffff`
  - `--sidebar-primary-foreground: #334155`
  - `--sidebar-accent: rgba(255,255,255,0.12)`
  - `--sidebar-accent-foreground: #ffffff`
  - `--sidebar-border: rgba(255,255,255,0.1)`
- Add new AI panel variables:
  - `--maple-accent: #6c5ce7`
  - `--maple-accent-light: #f0eef6`
- Add division badge color variables (or use Tailwind directly)

### Phase 2: Sidebar Dark Theme
**File:** `portal/src/components/Layout/PortalLayout.tsx`

- Change sidebar `<aside>` from `bg-white border-r border-gray-200` to `bg-[#334155] border-r border-[#2d3a4a]`
- Add red accent bar `<div className="h-1 bg-red-600" />` at top of sidebar
- Update nav items:
  - Default: `text-white/70 hover:bg-white/10 hover:text-white`
  - Active: `bg-white/12 text-white font-medium`
- Update 3Maples logo section: use white version or invert filter
- Update user section at bottom: white text, avatar stays similar
- Update user menu popover colors for dark background context
- Update collapse/expand button colors
- Keep "Estimates" nav label as-is (no change)
- Apply same dark theme to mobile sidebar

### Phase 3: Header Branding
**File:** `portal/src/components/Layout/PortalLayout.tsx`

- Add "POWERED BY" + 3Maples logo to the right side of header (before the Maple AI button)
- Small text "POWERED BY" in gray, 3Maples logo icon next to it
- Keep the Maple AI sparkles button

### Phase 4: Dashboard Redesign
**File:** `portal/src/pages/DashboardPage.tsx`

- Change title from "Dashboard Overview" to "Dashboard"
- Replace the 6 status summary cards with 3 hero cards:
  1. **Total Pipeline** (dark navy bg, white text, chart icon, total $ of all non-lost estimates)
  2. **Draft Value** (white bg, bordered, clipboard icon, total $ of draft estimates)
  3. **Won This Month** (white bg, bordered, trophy icon, count of won estimates this month)
- Add **Estimated Value by Divisions** bar chart section (using CSS bars, no chart library needed)
- Add **Pipeline Status** section with colored dot indicators and counts
- Replace generic estimates table with **Recent Estimates** section:
  - Show estimate name + ID, address, division badge (colored), status, age, amount
  - "View All Estimates" link at top right
  - Limit to 5-10 most recent

### Phase 5: AI Panel Styling
**File:** `portal/src/components/Layout/PortalLayout.tsx`

- Keep panel title as "Maple" (no change)
- Style the composer input area with lavender background (`bg-[#f0eef6]`)
- Style the send button with purple accent (`bg-[#6c5ce7]`)
- Update suggestion chips styling (rounded-full, outlined, gray border)
- Keep Clear button styling similar

### Phase 6: Extrapolate to Other Pages
**Files:** All page components in `portal/src/pages/`

Apply consistent styling updates across all pages:
- `EstimatesPage.tsx` - Add division badges with colors, update status badges
- `PropertiesPage.tsx`, `ContactsPage.tsx`, `MaterialsPage.tsx`, `PeoplePage.tsx` - Ensure consistent card/table styling with the new design language
- `SettingsPage.tsx` - Consistent with new theme
- `Login.tsx` - Ensure card styling consistent
- `OnboardingPage.tsx` - Consistent styling
- Modals and dialogs - Ensure primary buttons use the updated slate-700 style consistently

### Phase 7: Division Badge Component
**File:** New utility or inline in components

- Create division/category color mapping:
  - Design/Build: orange (`bg-orange-500 text-white`)
  - Tree Care: green (`bg-green-600 text-white`)
  - Maintenance: yellow (`bg-yellow-500 text-white`)
  - Turf & Plant: blue (`bg-blue-600 text-white`)
  - Default/Other: gray (`bg-gray-500 text-white`)

---

## Files to Modify (ordered)

1. `portal/src/styles/theme.css` - CSS variables
2. `portal/src/index.css` - Base styles cleanup
3. `portal/src/components/Layout/PortalLayout.tsx` - Sidebar, header, AI panel
4. `portal/src/pages/DashboardPage.tsx` - Complete dashboard redesign
5. `portal/src/pages/EstimatesPage.tsx` - Division badges, status badges
6. `portal/src/components/common/EstimatesTable.tsx` - Division badge rendering
7. Other page components as needed for consistency

## Files NOT Modified (no changes needed)
- `portal/src/components/ui/*` - Radix primitives stay as-is (themed via CSS vars)
- `portal/tailwind.config.js` - No changes needed (uses CSS vars)
- Backend files - No backend changes

---

## Verification

1. Run `cd portal && npm run dev` to verify visual changes
2. Run `cd portal && npm test` to ensure all existing test files pass
3. Add new tests as necessary for new functionality (division badges, dashboard summary calculations, etc.)
4. Manual visual check on all pages: Login, Dashboard, Estimates, Properties, Contacts, Materials, People, Settings, Onboarding
4. Verify sidebar collapse/expand still works
5. Verify mobile responsive menu still works
6. Verify Maple AI panel open/close and chat functionality
7. Verify all navigation links work
8. Verify modals (Account, Company, Team Members) render correctly
