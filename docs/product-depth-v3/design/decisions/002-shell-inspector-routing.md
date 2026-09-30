# D-002 · Shell, inspector, routes
- Organizer/admin: top bar 44 + rail 216/52 + right inspector. Participant/judge/mentor/volunteer: top bar only (participant/judge) or bottom nav (mobile).
- Rail: ≤6 default items per role; "Advanced" group collapsed; features not enabled are absent, not disabled.
- Inspector is non-modal, keeps list scroll + selection; Esc closes and returns focus to the row. Below 1024px it becomes a sheet/detail page.
- Every screen state is URL-addressable (route + saved-view id or serialized query + selected row id) — spec 005 PROG.
- Event state tag lives in the top bar only. Role switcher and "Preview as" (read-only, persistent banner, no impersonation) live in the account menu.
