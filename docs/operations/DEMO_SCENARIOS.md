# Synthetic demo scenarios

```sh
python src/api/manage.py demo_scenario create --scenario hackathon --seed 1 --participants 8 --judges 4
python src/api/manage.py demo_scenario list
python src/api/manage.py demo_scenario purge demo-hackathon-1
```

`create` builds one workspace (`demo-<scenario>-<seed>`) through the real API: imported event configuration, participants with teams and projects, finalized submissions, seeded judge bias/noise ballots, normalization, published results, and published track and grand awards. The event ends `closed` and private unless `--public`.

- Deterministic: the same scenario, seed and counts reproduce identical names, tracks, scores, results and winners (ids differ). The synthetic clock defaults to 2026-01-10 12:00 UTC; override with `--at`.
- Isolated: nothing is written outside the generated workspace. An existing slug is refused, not merged.
- Accounts are `demo-<scenario>-<seed>-<role>-<nn>` and locked (no usable password) and hold no sessions. `--password` sets one shared login password for training.
- Bounds: 3–40 participants, 2–12 judges.
- `purge` only accepts a workspace carrying the generator's marker, deletes it including immutable result evidence, and removes synthetic accounts that belong to no other workspace.
