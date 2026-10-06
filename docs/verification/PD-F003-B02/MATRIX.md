# PD-F003-B02 verification matrix (T90)

The batch adds the eight surface properties to the registry of PD-F003-B01 (`core.features`): base UI (T01), advanced UI (T02), bulk (T03), CLI (T04), MCP (T05), Event-as-Code (T06), webhooks and the outbox (T07) and archive (T08). `i:` is `tests/integration/`, `w:` is `src/web/`, `e:` is `tests/e2e/` (the browser spec runs at 390 and 1440 with axe and an overflow check). Each verifier has a unit suite with a failure code per defect and a proof suite that runs the real surface. Test names are checked to exist by script. The batch adds no model, route or migration; the product changes are the single `COMMANDS` table of the CLI (behavior unchanged) and the `SECTION_MODELS` table of Event-as-Code (format unchanged).

## Positive behavior (realistic persisted data)

- **T01 base UI:** `i:test_feature_contract` `test_a_real_ui_base_claim_names_a_screen_a_test_and_what_it_reads`; CI `check_static` over the real tree (`test_every_landed_property_is_claimed_and_verified_for_all_fifteen_features`).
- **T02 advanced UI:** `i:test_feature_contract` `test_a_real_advanced_ui_claim_names_the_shared_component_and_the_screen_that_uses_it`; the CI check finds each named component imported and read.
- **T03 bulk:** `i:test_feature_bulk` `test_the_audit_actions_the_claims_name_are_what_a_real_apply_records` (all five planner actions previewed and applied; the audit rows equal the claims), `test_every_registered_bulk_action_belongs_to_exactly_one_claimed_feature`.
- **T04 CLI:** `i:test_feature_cli` `test_each_claimed_command_sends_the_request_its_operation_describes` (list, get, create, update and status through the real API), `test_every_cli_command_is_claimed_by_exactly_one_feature_or_named_as_outside`; `tests/test_admin_cli.py` unchanged.
- **T05 MCP:** `i:test_feature_mcp` `test_each_claimed_tool_reaches_its_own_route_with_a_credential_limited_to_it` (five tools through the endpoint), `test_every_mcp_tool_is_claimed_by_exactly_one_feature_or_named_as_outside`.
- **T06 Event-as-Code:** `i:test_feature_eac` `test_every_section_writes_exactly_the_rows_it_declares` (a full document applied to an empty event changes exactly the declared tables), `test_every_document_section_is_claimed_by_exactly_one_feature_or_named_as_outside`.
- **T07 webhooks:** `i:test_feature_webhook` `test_each_audited_change_writes_the_outbox_event_its_claim_names` (40 audited changes sent as the role that makes them; the outbox holds the claimed event or nothing).
- **T08 archive:** `i:test_feature_archive` `test_each_claimed_table_is_restored_with_its_rows` (a real archive restored, row counts per table), `test_the_event_is_the_root_and_restores_as_a_new_draft_event`.

## Negative and boundary

- **Every verifier has a code per defect:** `test_each_advanced_ui_failure_has_a_code`, `test_each_bulk_failure_has_a_code`, `test_each_cli_failure_has_a_code`, `test_each_mcp_failure_has_a_code`, `test_each_event_as_code_failure_has_a_code`, `test_each_webhook_failure_has_a_code`, `test_each_archive_failure_has_a_code`, and for the base UI `test_the_ui_ci_check_finds_a_missing_screen_one_that_reads_nothing_and_an_unrelated_test`.
- **CI checks against a temporary tree:** `test_the_advanced_ui_ci_check_finds_an_unimported_component_and_a_screen_that_reads_nothing`, `test_the_ci_check_holds_each_command_to_the_feature_and_the_client`, `test_the_ci_check_reports_an_unreadable_table`, `test_the_ci_check_finds_a_proof_that_does_not_exist`.
- **A claim held to the system, not remembered:** cross-cutting `test_a_system_that_changes_makes_a_surface_claim_fail` (a tool added, a bulk action removed, a document section added, a change that starts emitting, a table leaving the archive).
- **Refusals leave no trace:** `i:test_feature_webhook` `test_a_refused_change_leaves_nothing_in_the_outbox` (40 changes refused for a stranger).

## Authorization and visibility

The surfaces add no authority. MCP write tools are held to the feature's audit claim and to a role-gated matrix row (`test_a_write_tool_must_reach_an_audited_role_gated_route`); each tool succeeds with a credential limited to its own route and is refused with one limited to another; the CLI keeps its 403 and 404 paths (`tests/test_admin_cli.py`); the report endpoint stays organizer and admin only (B01 suite).

## Lifecycle, migration and compatibility

No migration. `COMMANDS` is read by `execute` (the CLI suite passes unchanged), `SECTION_MODELS` sits beside the apply code (the Event-as-Code and final-archive suites pass unchanged), and no archive field, document field, route or event type changed.

## Concurrency and idempotency

The registry is stateless and read-only. The planner's own concurrency suite (`i:test_bulk_operations` `test_concurrent_retry_applies_once`) and the archive and webhook suites pass unchanged; the webhook proof sends each change once and reads the outbox written in the same transaction.

## Whole-registry regression (new in T90)

`i:test_completeness_regression`: `test_no_action_command_tool_section_event_or_table_is_claimed_by_two_features`, `test_the_surfaces_count_what_the_documents_say` (5 actions, 5 commands, 5 tools, 10 sections, 19 emitted changes, 10 tables, 12 advanced uses), `test_the_webhook_and_audit_claims_describe_the_same_changes` (40), `test_every_mcp_write_tool_reaches_an_audited_change_and_every_cli_command_an_sdk_operation`, `test_a_system_that_changes_makes_a_surface_claim_fail`; the B01 whole-registry tests now run over sixteen landed properties (sensitivity per property, zero-query report, every proving test exists).

## UI states and viewports

`w:features/operations/CompletenessPanel.test.tsx` (derived facts for every property, loading, error with retry, empty, findings alert, closed details) and `e:completeness.spec.ts` at 390 and 1440 with axe and an overflow check, opening the Advanced UI, Bulk operations, CLI, MCP, Event-as-Code, Webhooks and outbox and Archive and import columns of a real event, stage, project and track. The surfaces add no screen of their own beyond these columns.

## Gaps the proofs found and the batch fixed

The first webhook scan resolved audit helpers by name across files and marked team and artifact changes as emitting; the real requests failed seven cases and helpers are now resolved per file. The CI check for the project screen and test (B01) and the first CLI draft that tied archive routes to no feature are recorded as `OUTSIDE` entries rather than hidden.

## Commands

```
uv run --frozen pytest -n auto --dist worksteal -q
pnpm --filter @conflux/web test
make format-check lint sdk-check block-schema-check
uv run --frozen python src/api/manage.py makemigrations --check --dry-run
make e2e-fast
```

Results are in the T90 and T91 receipts.

## Unresolved limitations (carried to the batch receipt)

Twenty-one audited changes send nothing to subscribers and say why; the bulk planner is not offered to agents (no MCP plan tool); nine MCP tools call routes no feature claims yet; base prizes and the event page are not features of the registry; `events export` and `events import` run through archive routes no feature claims; the CLI check runs in CI only because the SDK is not in the image; announcements have no screen (planned, PD-S009-B02-T03); the independent review is by the same tooling account (T95).
