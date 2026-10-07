# D-011 · Organizer rail size and the 11px floor
**Status**: accepted (PD-DESIGN-B00-T03). Clarifies D-002 and V-TYPE-2; no board changes.
- D-002 "at most 6 default rail items" was written for the roles without an Advanced group. The organizer rail is Overview, the Manage event items of `roleDestinations` (seven today) and an Advanced group (Integrations, Operations & audit); Shell-Organizer and Data-Surface show exactly this. Features that are not enabled stay absent. A rail longer than that needs a new decision.
- Avatar initials and small counts that the boards draw at 10px are built at `--fs-11`. The type scale has no 10px step.
