# Developer and builder surfaces

**API explorer**: searchable operation list (method chips, monospace path, first 200
matches with a refine hint) beside the selected operation: endpoint bar with method and
auth state, request form, explicit write confirmation, colour-coded response status and a
pretty-printed JSON viewer. Non-JSON bodies stay literal text (never interpreted). Schema
and response contract remain in disclosures. Credentials stay in page memory.

**Event setup** is grouped into task tabs (Settings, Stages, Policies, Rules, Forms, Public
page). Creating an event / templates moves into a collapsible section (open when the
workspace has no events).

**Public page builder** separates Content (block outline, one selected block editor,
reorder, unsaved/saved state, two-step removal), Appearance (Brand / Style / Layout groups,
accent preview, unsaved state) and Accessibility (audit warnings). "Preview public page"
opens the real page. The constrained block/theme schema is unchanged.

**Operations** sections form a card grid; older raw-label forms use a shared responsive
layout (class-less forms in `.cx-shell__main`). Communications fields are paired and stack.

No API or model changes.
