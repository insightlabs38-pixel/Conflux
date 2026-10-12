# Release, Demo and Documentation

## Required root docs
README, ARCHITECTURE, DATA-MODEL, JUDGING, LICENSE plus honest limitations/security/operator information.

## Demo path (~5 min)
1. organizer creates/configures event/stages/policies/forms/rubric/public page;
2. participant/team submits typed evidence and sees preflight/finalization;
3. organizer shows assignment health;
4. judge evaluates with isolated score access;
5. organizer shows normalization proof/progress/results;
6. publish public results/gallery;
7. brief portability/operability proof: API/OpenAPI, archive/export, Compose/offline status.

## Acceptance report
Run exact `python3 run.py .dogfood.toml > acceptance-report.txt` against release candidate and commit verbatim. Honest failures must be disclosed; never hand-edit.

## Documentation policy
Permanent docs explain contracts/why, not implementation diary. Generated OpenAPI is authoritative for endpoint shape. Keep operator commands copy-pastable and tested.
