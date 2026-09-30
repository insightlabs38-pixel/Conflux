# PD-B03-T01 — isolated fixture contract evidence

Contract: `docs/operations/E2E.md#isolated-browser-fixture-contract-pd-b03-t01`. Stack: the one shared `conflux` compose stack; probe seeds 92xx/93xx/94xx purged afterwards (`logs/T01-final-scenario-list.log`: only 7, 81–83 remain; seed 7 untouched).

| Check                                                                         | Command                                                           | Result                                                                                                                                      |
| ----------------------------------------------------------------------------- | ----------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| Isolation, cross-seed denial, duplicate/boundary refusals, purge independence | `python3 docs/verification/PD-B03/probe_isolation.py`             | 12/12 pass (`logs/T01-probe-isolation.log`)                                                                                                 |
| Create time by size/checkpoint/concurrency                                    | `python3 docs/verification/PD-B03/probe_timing.py`                | 4p/2j 2.7–3.1 s, 24p/6j 8.3 s, 4 concurrent 2.8 s wall (`logs/T01-probe-timing.log`)                                                        |
| Mutating specs unmodified on `iso-min` (6p/3j)                                | `E2E_DEMO_SEED=9401 … playwright --project=desktop pvs`           | 10/10 pass                                                                                                                                  |
| event-themes, profiles, participant-workflow, uiv2-judge on `iso-min`         | same, five specs                                                  | 26 pass; `uiv2-organizer` 4 fail (`logs/T01-spike-mutators-iso-6p3j.log`)                                                                   |
| `uiv2-organizer` on generator-`published` 6p/3j                               | `E2E_DEMO_SEED=9402 …`                                            | 4 fail: 404 `…/awards/<id>/deliberation/` (`logs/T01-spike-uiv2-organizer-published.log`) — generator decides awards without a deliberation |
| Canary chain on isolated 24p/6j seed                                          | `E2E_DEMO_SEED=9403 … lifecycle uiv2-organizer uiv2-final-states` | 16 passed, 1m57s (`logs/T01-spike-lifecycle-chain-iso.log`)                                                                                 |

The two `uiv2-organizer` failures are a finding, not a defect: it is a post-lifecycle reader and is classified as such in the contract.
