# Verification evidence

Conflux claims DOGFOOD T1–T4. The organizer-supplied acceptance checker
contains automated assertions for T1/T2 only; T3/T4 are evaluated manually.
The untouched checker receipt is [acceptance-report.txt](../../acceptance-report.txt).
Its “claimed but not verified” T3/T4 note means there are no automated
assertions for those tiers; it does not decide the manual assessment.

Conflux's separate [extended report](dogfood-extended.txt) reruns existing
regression tests for T3/T4 and advanced capabilities. Reproduce with:

```sh
make up
make demo-reset
make verify-dogfood-extended
```

It runs the official checker as supplied, disposable API/model regression
suites, validated OpenAPI and SDK checks, and a live gallery embed browser
check. Each PASS names its test source or command. SKIP and MANUAL-EVIDENCE
never count as a machine PASS; prior expensive release receipts are labeled
explicitly. A source commit identifies the implementation under test;
committing its receipt afterward does not change the tested implementation.

[Final targeted pass](final-pass/report.md) records current regression and
media counts. [PVS-H06](PVS-H06/report.md) contains prior cold/offline,
backup/restore, chaos, artifact portability, load and Dex evidence.

## Remaining limits

- T3 identity modes, single-use ballots, throttling and duplicate signals
  provide concrete abuse controls, not proof against all Sybil identities.
- Records are signed event/project/judge claims, not a PDF certificate designer.
- Hosted OIDC providers, refresh tokens and logout propagation are not covered
  by the Dex smoke; see [SSO](../operations/SSO.md).
- Judges' deliberation notes/stances and technical operator features remain
  API/CLI-first; see [UI map](../operations/PVS_UI.md).
- After uploading evidence, re-open the project to refresh the submission artifact picker.
- Final archives carry sponsor resources in v3. v1 config/full and
  Event-as-Code have narrower configuration scope. Stored artifact bytes
  need the separate artifact portability/backup path.
- Normalization assumes additive judge bias and overlapping assignments;
  see [JUDGING.md](../../JUDGING.md) for statistical limits.
