# Browser journeys, screenshots and clips

`tests/e2e` holds Playwright specs that run against a live, demo-seeded stack (`scripts/demo-reset`, see [DEMO.md](DEMO.md)).

```sh
E2E_BASE_URL=http://localhost:8080 npx playwright test -c tests/e2e/playwright.config.ts
# one scene set only (desktop, video on): ... scenes
```

Env: `E2E_BASE_URL`, `E2E_DEMO_SEED` (7), `E2E_DEMO_PASSWORD` (demo-pass-7). Chromium must be installed (`npx playwright install chromium`).

- `signin`, `public`, `roles`: sign-in/out, public pages, organizer/judge/participant workspaces at 1280×800 and 390×844 — no console errors or failed requests, no horizontal overflow, axe WCAG 2 A/AA clean, skip-link and focus-ring keyboard checks. Loading states must resolve before assertions.
- `scenes` (desktop): deterministic screenshots in `tests/e2e/artifacts/scenes/` and one video per scene under `artifacts/results/*/video.webm`. Failures keep traces (`npx playwright show-trace`).
- `lifecycle` (desktop, serial, successful videos retained): the recorded demo lifecycle through the UI only — participant creates team and project, uploads a technical brief, submits and receives a signed receipt; organizer requests changes, participant remediates, organizer clears; three judges inspect artifacts and score; organizer publishes results, finalizes in the deliberation room, publishes the award; the public results page shows it. Needs a fresh `scripts/demo-reset submitted` (it consumes participant-24); if the demo was not reset the first step fails within 10 s with a message saying so.
- `pvs`: mentor desk, volunteer check-in by pass, participant RSVP/office hours/mentor request, deadline-exception request and decision, rules publish and acknowledge, and a layout/axe check of every organizer operations panel (also at 390×844). Workflows run on desktop only; run after a reset.
- Addressing: people by username, the event through the API; the event's public ID is also stable across resets.

- `extended-embed`: loads the built gallery Web Component against the live
  public API without cookies; included by `make verify-dogfood-extended`.
- Media handoff: `scripts/package-demo-media submitted` after a successful
  submitted run; repeat with `published` after its scene run, then use
  `scripts/package-demo-media --zip`. See [DEMO.md](DEMO.md).

- `pdv3-baseline-census` (opt-in, `E2E_CENSUS=1`, run after `scripts/demo-reset`): measurement-only tour that writes full-page JPEGs and a `manifest.json` (console/HTTP problems, horizontal overflow, axe counts) for every role at 1280×800 and 390×844 to `docs/verification/PD-B00/ui-census/`. It asserts nothing about layout and is skipped in normal runs.

## Isolated browser fixture contract (PD-B03-T01)

Normal mutable specs must not depend on the one long-lived `demo-hackathon-7` event. The contract below is what `PD-B03-T02…T11` implement; evidence is in `docs/verification/PD-B03/`.

**Canonical primitive.** A fixture is one generated demo scenario: `manage.py demo_scenario create --seed N …` then `manage.py demo_showcase demo-hackathon-N` (exactly what `scripts/demo-reset` runs). Built through the real API, so invariants/audit/permissions apply. No new model or seed path. Seed `N` fixes the workspace slug `demo-hackathon-N`, the workspace/event public IDs and every account (`demo-hackathon-N-<label>`); `support.ts` already selects it via `E2E_DEMO_SEED`/`E2E_DEMO_PASSWORD`.

**Fixture handle** (what a factory returns to specs and storage-state setup; one per worker/shard/test as the tier needs):

```ts
type Fixture = {
  seed: number;
  slug: string; // demo-hackathon-<seed>
  workspace: string;
  event: string; // public IDs (derived from seed)
  password: string; // per fixture; accounts share it
  profile: "iso-min" | "iso-judged" | "iso-published" | "canary";
  account(label: string): string; // demo-hackathon-<seed>-<label>
  dispose(): Promise<void>; // purge via demo_scenario purge <slug>
};
```

**Seeds.** `7` is the shared _reference_ (read-only tier; rebuilt only by `scripts/demo-reset`). `1…999999` belong to people/demos (e.g. 81–83) and are never touched. Factory seeds are `10_000_000 + nonce·1000 + slot` (`nonce` 0–9999 per run, `slot` 0–999 per fixture within the run; fits the `PositiveIntegerField`). A taken seed is refused by the generator (`already exists; purge it first`), so the factory picks a new nonce and never reuses or purges a seed it did not create; `dispose` and sweeps only act on seeds ≥ 10_000_000.

**Profiles** (sizes from labels the specs actually use: `participant-05`, `judge-03`; `participant-24` only in the lifecycle; `mentor/volunteer/sponsor` come from `demo_showcase`). Times are measured on the shared stack including ~1.3 s `docker compose exec` overhead.

| profile                    | size / checkpoint             | create + showcase | used by                         |
| -------------------------- | ----------------------------- | ----------------- | ------------------------------- |
| reference                  | 24p/6j submitted, seed 7      | `demo-reset`      | read-only tier                  |
| iso-min                    | 6p/3j, `--live 2`, submitted  | 3.4 s + 1.9 s     | isolated-mutation tier          |
| iso-judged / iso-published | 6p/3j, `--live 2` / `0`       | ≈3 s + 1.9 s      | specs needing ballots / results |
| canary                     | 24p/6j, `--live 2`, submitted | 8.3 s + showcase  | lifecycle chain (one per run)   |

Boundaries (all produce a diagnostic, none silently degrade): 3–40 participants, 2–12 judges; `--live` ≤ participants−2 (so 3p/2j needs `--live 1`); `published` requires `--live 0`; duplicate seed refused. Four concurrent creations of 4p/2j took 2.8 s wall (same as one), so factories may create per shard in parallel.

**Tiers** (specs run unmodified on an isolated seed; `pvs` 10/10 and event-themes/profiles/participant-workflow/uiv2-judge 26/26 passed on `iso-min`):

- _read-only on reference:_ `workspace-shell`, `roles`, `signin`, `extended-embed`, `uiv2-surfaces`, `uiv2-gate` (logout only), `public`, `showcase`, `foundations`. They move to isolated seeds only if a run needs the reference stable after a mutator.
- _isolated-mutation (iso-min, own seed):_ `event-themes` (PATCHes event brand), `profiles`, `participant-workflow`, `pvs`, `uiv2-judge`.
- _lifecycle canary (serial, `canary` profile, never parallelised or shortened):_ `lifecycle`. Consumes `participant-24`; still the authoritative create→submit→judge→publish→public-results path.
- _post-lifecycle readers:_ `uiv2-organizer`, `uiv2-final-states`, `scenes` read state the canary creates. `uiv2-organizer` fails on a generator-`published` seed (`404 …/awards/<id>/deliberation/`: the generator decides awards but never opens a deliberation), so these run on the canary's fixture after `lifecycle`, or T02 adds a canonical deliberation-finalize step; they must not be pointed at `iso-published` as-is.
- _opt-in measurement:_ `pdv3-baseline-census` (reference).

**Lifecycle.** create in worker/shard setup (before any test), sign-in via T03 storage states, dispose on success, **keep on failure** and print the slug so the failing state can be inspected; a sweep purges leftover seeds ≥ 10_000_000. Open checkpoints use the real clock for the submission window, so deadline-sensitive specs are per fixture.

**Guards.** A fixture's event ID must differ from the reference's; cross-fixture access must be denied (measured: organizer of one seed gets 403 reading/writing another's event) and a mutation on one fixture is invisible to another and to seed 7 (`docs/verification/PD-B03/probe_isolation.py`, 12/12).

**Implementation (T02).** `integrations/e2e_fixtures.py` + `manage.py e2e_fixture create <profile> | dispose <slug> | sweep | list` (one process: generator + showcase, JSON handle on stdout, random per-fixture password, taken seeds skipped, half-built fixtures purged on failure, `dispose`/`sweep` refuse anything below seed 10,000,000). Specs use `tests/e2e/fixtures.ts`: `isolatedTest("iso-min")` gives a worker-scoped `fixture` (created before the worker's first test, disposed after its last unless a test failed or `E2E_KEEP_FIXTURES=1`); `signIn(page, label, fixture)` signs in as its account. `E2E_MANAGE` overrides how `manage.py` is reached. `make e2e-fixture-sweep` purges fixtures older than `E2E_SWEEP_MINUTES` (30). The app container bakes the source, so run `docker compose up -d --build app` after pulling this command. Measured create: iso-min 4.1 s, iso-judged 4.3 s, iso-published 4.8 s, canary 9.0 s; four parallel iso-min 4.2 s wall (`docs/verification/PD-B03/logs/T02-create-timing.log`). `fixture-isolation.spec.ts` proves isolation, cross-fixture denial and scoped disposal.

**Known limits.** Creation scales roughly with account count (8.3 s for 31 accounts, ≈0.25 s each including the API replay), so keep mutation-tier fixtures small. Factory, storage states, tier split and sharding are later tasks (T02–T08).
