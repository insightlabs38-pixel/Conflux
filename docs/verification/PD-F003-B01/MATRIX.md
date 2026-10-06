# PD-F003-B01 verification matrix (T90)

The batch builds one registry (T01) and eight property verifiers over the fifteen features of `core.features`. `i:` is `tests/integration/`, `w:` is `src/web/`, `e:` is `tests/e2e/` (the browser spec runs at 390 and 1440 with axe and an overflow check). Each verifier has a unit suite with a failure code per defect and a request suite that sends real requests. Test names are checked to exist by script. The registry is read-only and holds no migration; the only product changes are the gaps the proofs found (below).

## Positive behavior (realistic persisted data)

- **T01 identity and lifecycle:** `i:test_feature_contract` `test_the_fifteen_features_agree_with_the_live_system`, `test_every_feature_resolves_to_its_model_and_a_uuid_public_id`, `test_a_lifecycle_reads_its_states_from_the_models_own_choices`.
- **T02 validation:** `test_a_real_claim_is_enforced_proved_and_derived_from_the_model`; `i:test_feature_validation` `test_a_track_needs_a_name_and_a_unique_one`, `test_a_message_needs_a_known_audience_and_a_subject_and_leaves_nothing_behind`.
- **T03 authorization:** `i:test_feature_authorization` `test_every_matrix_gate_holds_for_a_wrong_role_a_stranger_and_a_signed_out_caller` (every claimed route and method, more than 100 refusals).
- **T04 audit:** `i:test_feature_audit` `test_each_declared_change_records_its_audit_action` (40 changes through the API as the role that makes them: action, workspace, actor, target, no secret).
- **T05 idempotency:** `i:test_feature_idempotency` `test_a_repeated_change_does_what_its_declared_mode_says` (40 changes sent twice), `test_a_keyed_change_runs_once_for_one_key_and_a_different_body_is_refused`.
- **T06 REST:** `i:test_feature_rest` `test_every_claimed_list_returns_what_its_schema_says`, `test_every_claimed_detail_returns_one_record_with_a_public_id`.
- **T07 SDK:** `i:test_feature_sdk` `test_every_claimed_operation_works_through_the_generated_python_sdk` and `test_every_claimed_list_is_read_through_the_generated_python_sdk` (63 operations through the generated client against the real API).
- **T08 search:** `i:test_feature_search` `test_the_catalogue_offers_exactly_the_claimed_fields_to_the_roles_that_may_read`, `test_every_claimed_field_filters_and_sorts_as_declared`.

## Negative and boundary

- **Every verifier has a code per defect:** `test_each_identity_failure_has_a_code`, `test_each_validation_ref_failure_has_a_code`, `test_each_authorization_failure_has_a_code`, `test_each_audit_failure_has_a_code`, `test_each_idempotency_failure_has_a_code`, `test_each_rest_failure_has_a_code`, `test_each_sdk_failure_has_a_code`, `test_each_search_failure_has_a_code`; claims in general: `test_claims_must_be_well_formed_and_honest`, `test_planned_claims_name_a_task_that_exists`.
- **A claim held to the system:** `test_the_blank_probe_catches_a_model_that_accepts_or_crashes_on_a_blank_record`, `test_a_lock_is_found_in_code_that_really_takes_one_and_a_key_in_a_view_that_takes_it`, `test_a_writing_route_the_document_does_not_describe_is_reported`, `test_an_operation_missing_from_the_document_or_duplicated_is_reported`, `test_a_column_the_model_does_not_have_and_one_with_no_event_to_narrow_by_are_refused`, `test_the_sdk_ci_check_compares_the_generated_files_with_openapi`, cross-cutting `test_a_system_that_changes_makes_a_claim_fail` (a new search field, an audit action that disappears).
- **Refusals leave no trace and use one shape:** `i:test_feature_audit` `test_a_refused_change_leaves_no_audit_row`, `test_an_invalid_change_is_refused_and_leaves_no_audit_row`; `i:test_feature_rest` `test_every_refusal_of_a_claimed_route_uses_the_shared_error_shape` (stranger, signed out, unknown id, invalid body), `test_an_invalid_body_is_refused_with_keyed_messages`; `i:test_feature_sdk` `test_a_refusal_through_the_sdk_is_an_api_error_with_the_shared_shape`.

## Authorization and visibility

`test_feature_authorization`: `test_a_non_member_of_a_project_can_never_change_it_or_what_hangs_off_it`, `test_objects_of_another_workspace_or_event_are_not_found`, `test_a_signed_in_caller_of_the_wrong_role_learns_nothing_from_the_refusal`; the report endpoint is organizer and admin only and read-only (`test_organizers_and_admins_read_the_report`, `test_nobody_else_reads_it_and_nobody_writes_it`); search never reaches another event's rows or a role the routes refuse (`test_a_query_never_reaches_another_events_rows`, `test_an_entity_may_not_let_a_role_search_what_the_routes_refuse_it`).

## Lifecycle, migration and compatibility

No migration. The compatibility proofs are the full suites that passed unchanged after each product change: audit rows are additive, `Idempotency-Key` is opt-in on four creates (`test_a_key_belongs_to_its_caller_and_a_failed_change_does_not_keep_it`), the OpenAPI list and field corrections regenerate both SDKs (`make sdk-check`), and an empty 404 body gained `{"detail": "Not found."}` with the same status (`test_a_member_who_may_not_see_a_project_gets_a_json_404_not_an_empty_one`).

## Concurrency and idempotency

`test_the_audit_row_and_the_change_commit_or_roll_back_together`, `test_deciding_an_application_twice_audits_once_and_the_second_is_refused`, `test_the_invite_token_is_never_written_to_the_audit_log`, `test_an_unkeyed_retry_of_an_unprotected_change_is_the_documented_repeat`; the locked services are covered by the existing race suites under `i:concurrency/`. The registry itself is stateless.

## Whole-registry regression (new in T90)

`i:test_completeness_regression`: `test_every_landed_property_is_claimed_and_verified_for_all_fifteen_features`, `test_no_route_change_action_or_entity_is_claimed_by_two_features`, `test_dropping_any_ref_of_a_real_claim_is_noticed_or_leaves_it_equally_true` (sensitivity per property), `test_the_report_is_derived_query_free_and_free_of_secrets` (zero queries), `test_every_proving_test_a_claim_names_exists_and_the_request_proofs_are_all_named`, `test_the_audit_idempotency_and_sdk_proofs_cover_the_same_changes`.

## UI states and viewports

`w:features/operations/CompletenessPanel.test.tsx` (loading, error with retry, empty, findings alert, closed details per claim, derived facts for every property, not-applicable reasons) and `e:completeness.spec.ts` at 390 and 1440 with axe and an overflow check, opening the Validation, Authorization, Audit, Idempotency, REST, Generated SDK and Search columns of a real event and application.

## Gaps the proofs found and the batch fixed

Nineteen unaudited changes (project, form, evaluation plan, artifact, submission draft, application decision, team); four creates that repeated on a retry (message, announcement, project, external artifact; now keyed); ten lists documented as one record in OpenAPI (wrong generated types), an undocumented `offset` and an undocumented awards field; eleven empty-bodied 404s; the upload-intent endpoint validated a body before refusing a non-member; `Submission.clean` crashed on a blank record.

## Commands

```
uv run --frozen pytest -n auto --dist worksteal -q
pnpm --filter @conflux/web test
make format-check lint sdk-check block-schema-check
uv run --frozen python src/api/manage.py makemigrations --check --dry-run
make e2e-fast
```

Results are in the T90 and T91 receipts; the browser log is `T90-e2e-fast.log` in this directory.

## Unresolved limitations (carried to the batch receipt)

Eight features have no record page of their own and lists are unpaged except messages (each says why); thirteen features are not searchable through the query engine (each says why); `my-team` creation is checked but not row-locked; a webhook subscription can be created twice for one URL; the TypeScript client is checked by its generated types, not by a runtime call; the cli, mcp, event_as_code, webhook, archive and analytics surfaces belong to PD-F003-B02 and B03.
