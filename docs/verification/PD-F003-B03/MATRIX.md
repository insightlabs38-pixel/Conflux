# PD-F003-B03 verification matrix (T90)

The batch adds the five platform properties to the registry of PD-F003-B01 (`core.features`): analytics dimensions (T01), retention and privacy (T02), extension hooks (T03), version and migration (T04) and test fixtures and scenarios (T05). With it all 21 properties of the contract are landed and verified for the fifteen features. `i:` is `tests/integration/`, `w:` is `src/web/`, `e:` is `tests/e2e/` (the browser spec runs at 390 and 1440 with axe and an overflow check). Each verifier has a unit suite with a failure code per defect and a proof suite that runs the real subsystem. Test names are checked to exist by script. The batch adds no model, route or migration and changes no product behavior.

## Positive behavior (realistic persisted data)

- **T01 analytics:** `i:test_feature_analytics` `test_every_claimed_measure_and_breakdown_is_in_the_summary_of_a_real_event` (every claimed measure is in the answer for a real event, the status breakdown has exactly the field's choices, the numbers match the rows), `test_every_summary_section_and_counted_model_is_claimed_or_named_as_outside`.
- **T02 privacy:** `i:test_feature_privacy` `test_a_real_subject_is_exported_and_erased_as_every_claim_says`, `test_judging_evidence_appeals_eligibility_and_message_receipts_follow_their_claims`, `test_the_export_lists_exactly_the_buckets_the_service_has`, `test_every_bucket_of_the_privacy_service_is_claimed_by_exactly_one_feature_or_named_outside`.
- **T03 extension:** `i:test_feature_extension` `test_every_hook_pair_is_claimed_once_and_the_manifests_agree_with_the_live_registries`, `test_each_claimed_kind_has_live_entries_that_its_manifest_declares`, `test_the_sdk_has_a_typed_contract_for_the_kinds_it_describes_and_says_so_in_the_report`.
- **T04 versioning:** `i:test_feature_versioning` `test_each_claimed_version_model_refuses_an_edit_and_a_delete` (seven version models written, then refused), `test_a_stale_writer_is_refused_by_the_submission_counter`, `test_every_numbered_immutable_model_is_claimed_once_or_named_outside`.
- **T05 fixtures:** `i:test_feature_fixtures` `test_the_demo_scenario_creates_exactly_the_features_the_claims_say` (the demo event is generated and every feature's model counted in both directions).

## Negative and boundary

- **Every verifier has a code per defect:** `test_each_analytics_failure_has_a_code`, `test_each_privacy_failure_has_a_code`, `test_each_extension_failure_has_a_code`, `test_each_versioning_failure_has_a_code`, `test_each_fixture_failure_has_a_code`.
- **A claim held to the system, not remembered:** cross-cutting `test_a_system_that_changes_makes_a_platform_claim_fail` (a model the analytics module starts counting, a privacy bucket nobody claims, a version model under an in-place feature, a scenario the generator no longer builds); `test_an_entry_registered_without_a_manifest_and_a_claim_nobody_backs_are_noticed`.
- **Adversarial privacy cases:** `test_erasing_one_event_leaves_the_same_person_in_another_untouched`, `test_a_person_who_only_acted_in_a_role_leaves_what_they_decided_in_place`, `test_erasing_twice_is_a_no_op_and_the_second_report_still_names_what_is_kept`, `test_the_report_names_buckets_and_fates_and_never_a_person` (zero queries, no subject, note or file key); the existing retention suite (`i:test_retention_privacy`) passes unchanged.
- **Bulk-write bypass:** `test_no_code_bypasses_the_guard_with_a_bulk_write_on_a_version_model` (accepted residual: the database does not refuse it).

## Authorization and visibility

The properties add no authority. The privacy claims are proved through the service functions the organizer-only endpoints call, and the retention endpoints keep their 403 and 404 paths (`test_only_organizers_reach_privacy_endpoints`, `test_foreign_and_unrelated_subjects_are_not_found`); the report endpoint stays organizer and admin only (B01 suite); the fixtures claim never seeds a subscription secret (`webhook` is not applicable).

## Lifecycle, migration and compatibility

No migration. The only edits outside the registry are tests: the generic claim tests add a temporary property in the isolated registry now that none is left unlanded, and the planned-claim ratchet became a per-property ceiling. The version models, the privacy service, the manifests, the analytics module and the demo generator are read, not changed.

## Concurrency and idempotency

The registry is stateless and read-only. The submission counter's stale-writer refusal is proved directly (`test_a_stale_writer_is_refused_by_the_submission_counter`) and through the idempotency suite; a replayed erasure removes nothing more and keeps its evidence.

## Whole-registry regression (new in T90)

`i:test_completeness_regression`: `test_every_one_of_the_21_properties_is_landed_and_nothing_is_pending`, `test_no_measure_bucket_hook_version_counter_or_source_is_claimed_by_two_features`, `test_the_platform_properties_count_what_the_documents_say` (15 measures, 13 claimed buckets, 18 hook pairs, 7 version models, 2 counters, 2 comparison sources, 9 seeded and 5 planned features), `test_the_bucket_hook_and_person_claims_cover_what_the_services_hold`, `test_a_system_that_changes_makes_a_platform_claim_fail`; the B01 and B02 whole-registry tests (sensitivity per property, zero-query report, every proving test exists, the planned-claim ratchet) now run over all 21 properties.

## UI states and viewports

`w:features/operations/CompletenessPanel.test.tsx` (derived facts for every property, loading, error with retry, empty, findings alert, closed details) and `e:completeness.spec.ts` at 390 and 1440 with axe and an overflow check, opening the Analytics dimensions, Retention and privacy, Extension hooks, Version and migration and Test fixtures columns of a real event and asserting that no property is left pending. The properties add no screen of their own beyond these columns.

## Gaps the proofs found

Form answers (`forms.FormAnswer`) can hold personal data and are in no export or erasure bucket (recorded in the form claim, owner PD-S013-B02-T05); five features are not created by the demo scenario (owner PD-S061-B02-T01); version models are immutable in the model and not in the database (QUESTIONS.md, default A); five privacy buckets, three extension pairs and the voting analytics section have no owning feature and are named outside.

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

The form-answer privacy gap, the five unseeded features, the database-level immutability decision, the features outside the registry named in each `OUTSIDE`, the CLI table check that runs in CI only (B02), and the independent review that is by the same tooling account (T95).
