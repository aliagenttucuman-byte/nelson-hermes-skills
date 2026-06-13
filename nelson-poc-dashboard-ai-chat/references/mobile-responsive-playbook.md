# Mobile-responsive playbook for dashboard + chat (Nelson pattern)

Use this when converting an existing desktop-first dashboard into a mobile-usable operator UI.

## Trigger signals
- User asks "hacela responsive" / wants phone usability.
- UI has dense desktop cards, sidebars, or modal/chat patterns that break on small screens.
- Chat opens wrong route or nested layout instead of actual conversation view.

## Implementation pattern
1. Layout shell
   - Add a mobile top bar with hamburger + chat actions.
   - Keep desktop sidebar for `md+`; use drawer + overlay under `md`.
   - Close drawer on route change and on outside tap.

2. Navigation simplification
   - Remove low-value tabs from primary nav (for this workflow: hide Tasks/Router).
   - Keep only operational screens (Dashboard, PM Summary, Budget, Orchestrator, Docs, Settings if needed).

3. Chat UX
   - Keep desktop floating chat panel.
   - On mobile, render chat as near-fullscreen panel with safe insets.
   - Use dedicated route/view for popup content (e.g., `/chat-popup`) to avoid nested-menu behavior.

4. Density and spacing
   - Replace fixed desktop paddings with responsive paddings: `p-3 md:p-6`.
   - Convert stats/summary grids to `grid-cols-1 sm:grid-cols-2 lg:grid-cols-4`.
   - For mission-control sections, start at one column on mobile, then expand with breakpoints.

5. Config hygiene
   - Avoid hardcoded localhost API targets; use env vars (`ORCH_API_URL`, `ORCH_WS_URL`) or relative proxy paths.

## Validation checklist
- Build succeeds (`npm run build`).
- Mobile smoke test (real device or narrow viewport):
  - Drawer opens/closes reliably.
  - No horizontal overflow on key pages.
  - Chat opens conversation directly and remains usable at small heights.
  - Main actions in Orchestrator reachable without zoom.
- Tunnel/proxy test (if remote demo): API health and at least one full flow endpoint works.

## Pitfalls
- Keeping desktop fixed widths in cards causes clipped content in 360px screens.
- Floating chat button can overlap mission controls on mobile; move to top bar or resize.
- Catch-all routes can accidentally mount menu layout inside chat unless popup route is isolated.
