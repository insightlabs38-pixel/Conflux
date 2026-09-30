# Later Product Depth v3 surfaces — design-first assessment
Foundation r2 covers Ledger primitives, dark, responsive and pairwise. Which later systems need their own design pass *before* their implementation batch:

| Surface | Verdict | Why / what the pass must answer |
|---|---|---|
| Assignment optimization / rebalance / dropout simulation | **Design first** | Novel what-if UX: constraint editing, before/after coverage, per-judge load, dropout scenarios, apply-as-plan. Reuses plan→approve→apply but the comparison view is new. |
| Event Doctor + what-if simulator | **Design first** | Finding taxonomy, fix-as-plan flow, simulator inputs/outputs, how "confidence" is shown deterministically (no fake AI affordances). |
| Event-as-Code drift / field ownership / conflicts | **Design first** | Three-way diff, ownership badges per field, conflict resolution beyond the Builder-Plan diff; must stay legible for non-developers. |
| Audit / provenance / replay / evidence graph | **Design first** | Graph vs table, replay timeline, permissions on evidence; risk of decorative graph — needs a table-first equivalent. |
| Floorplan / spatial placement + judge routing | **Design first** | Spatial editor, table placement, route optimisation visualisation, mobile route follow; the only truly spatial surface. |
| RTL / localization stress test | **Design first (before i18n phase)** | Mirror rules for rail/inspector/tables, mixed-direction content, long-string expansion, date/number formats; not needed earlier. |
| Pairwise / adaptive judging | **Done in r2** | D-010. |
| Everything else | Inherit Ledger primitives | No bespoke pass needed. |

Suggested order: assignment optimization → Event Doctor → Event-as-Code drift → floorplan/routing → audit/provenance → RTL.
