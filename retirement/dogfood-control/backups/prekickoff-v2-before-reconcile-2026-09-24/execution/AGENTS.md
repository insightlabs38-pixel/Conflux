# Agent Operating Contract

1. Reconstruct current state narrowly from canonical control files plus your exact task/batch.
2. **Search before broad reading:** use `rg` first; then `grep`/`git grep`, `sed -n` targeted ranges, `git show`, `git diff`, and path-scoped history. Whole-file reads are for short files or when complete semantics are genuinely required.
3. Respect owned paths and active leases. Never change another active owner's surface without an explicit integration task.
4. **Session isolation:** implementation/review workers never message, call, resume, terminate, inspect private interactive state from, or type into another running agent session/pane. Coordination occurs through Git, control state, receipts and the orchestrator/human.
5. Frozen architecture is a constraint. Do not invent generic workflow engines, microservices, plugin runtimes, arbitrary organizer code, or new identity semantics.
6. Never weaken tests, acceptance criteria, permissions, deadline checks, migrations or security invariants.
7. Implementation agents add focused semantic tests. Freebuff verification owns most matrices/property/fuzz/adversarial breadth in parallel.
8. No worker starts or mutates the shared application runtime. Integration/runtime owner alone updates it.
9. Do not merge directly unless your role owns integration. Emit a concise receipt.
10. If blocked by architecture/security/concurrency/math/unexplained behavior, minimize and escalate rather than expanding scope.
11. Reports are evidence indexes, not implementation diaries. Git/tests are the detailed record.
