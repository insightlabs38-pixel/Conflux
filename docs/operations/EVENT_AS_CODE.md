# Event-as-Code

A declarative, human-editable description of an event's configuration that you can validate, plan and apply repeatedly.

```sh
python src/api/manage.py eventascode export  <event> > event.yaml
python src/api/manage.py eventascode validate <event> event.yaml
python src/api/manage.py eventascode plan     <event> event.yaml   # prints the digest to approve
python src/api/manage.py eventascode apply    <event> event.yaml --digest <digest> [--prune]
```

API (organizer): `GET .../as-code/` (document + digest), `POST .../as-code/validate/`, `POST .../as-code/plan/`, `POST .../as-code/apply/` with `{document, prune?, expected_digest}`.

## Document

`eventascode: 1`, `event` (`description`, `timezone`, `starts_at`, `ends_at` only) and the sections `tracks`, `base_prizes`, `stages`, `stage_transitions`, `forms` (draft schema), `policies`, `temporal_gates`, `policy_bindings`, `evaluation_plans` (with `rubric_versions`), `awards` (with `components`) and `page`. Everything is identified by **name**, so a document is portable between events; no database ids appear. Optional fields left out are left unchanged.

## Semantics

- A section that is absent is unmanaged; a present one is managed. Missing resources are reported under `unmanaged` and only deleted with `prune`.
- `plan` is a rolled-back trial apply: it lists every create/update/delete with field changes **and** every model rule that would reject the change. `apply` is atomic, refuses to run if the event changed since the reviewed plan (`409`, digest mismatch), and audits `event.config_applied` with the before-digest.
- Protected: published rubric versions (append a higher number instead), published or decided awards, tracks that projects use, evaluation plans (never pruned), archived events. Operational data (projects, submissions, ballots, results, registrations) is never touched.
- Applying an exported document to an empty event rebuilds the same configuration.
