# PD-F002-B02 verification matrix (T90)

Every one of the eight shared primitives has an executable proof for each dimension. `i:` is `tests/integration/`, `w:` is `src/web/`, `e:` is `tests/e2e/` (each browser spec runs at 390 and 1440 with axe and an overflow check). Test names are checked to exist by `tests/integration/test_shared_primitives_b02_regression.py` and by the commands below. Seven of the eight primitives are stateless; the one stored thing (a notification choice, T04) is the only mutation of the batch.

## SCHEMA_EDITOR (T01)

- **Positive:** `i:test_schema_subset` `test_every_block_schema_validates_exactly_as_before`, `test_every_setting_schema_of_the_registry_is_inside_the_subset`; shared fixtures `tests/fixtures/schema_cases.json` run in pytest and vitest.
- **Negative and boundary:** `test_a_schema_outside_the_subset_is_named`, `test_platform_caps_apply_when_a_schema_gives_no_bound`, `test_a_validation_never_raises_on_hostile_input`; `w:lib/schema.test.ts` "never throws on hostile input".
- **Authorization:** the editor only renders and validates; the server re-validates every save (`test_normalising_is_pure_and_the_api_error_shape_is_keyed_by_path`).
- **Lifecycle and compatibility:** block catalogue and settings registry validate exactly as before (no stored value changes); `make block-schema-check`.
- **Concurrency:** stateless, pure functions.
- **UI states:** `w:components/SchemaForm.test.tsx` (controls per type, enum arrays, row caps, disabled, unsupported type, linked problems), `w:features/event-builder/ConfigurationPanel.test.tsx`, `e:schema-form.spec.ts`.

## RICH_DOC (T02)

- **Positive:** `i:test_rich` `test_the_story_profile_renders_exactly_as_the_old_renderer_did`, `test_the_page_profile_is_the_presentation_sanitiser`; shared `rich_cases.json`.
- **Negative and boundary:** `test_hostile_input_never_leaves_the_node_set`, `test_text_that_looks_like_markup_stays_text`, `test_a_source_over_the_limit_is_refused_and_not_truncated`, `test_a_tree_with_too_many_parts_is_refused`, `test_html_nested_too_deep_is_refused`, `test_random_input_renders_or_is_refused_with_a_code`.
- **Authorization:** `test_every_workspace_member_can_preview`, `test_a_preview_is_for_members_only`; cross-cutting route refusal below.
- **Lifecycle and compatibility:** `test_stored_content_keeps_rendering_whatever_its_length`, `test_the_one_intended_difference_is_that_only_three_schemes_are_links`.
- **Concurrency and idempotency:** `test_a_preview_stores_and_audits_nothing`, `test_a_preview_is_the_same_every_time`; `w:components/RichEditor.test.tsx` "sends only the last text after a burst of edits".
- **UI states:** `w:lib/rich.test.tsx`, `w:components/RichEditor.test.tsx` (refusal, blank, closed preview), `w:features/artifacts/ProjectStoryEditor.test.tsx`, `e:rich-preview.spec.ts`.

## ARTIFACT_PREVIEW (T03)

- **Positive:** `i:test_previews` `test_text_and_data_show_a_bounded_redacted_excerpt`, `test_images_video_and_documents_carry_facts_and_the_existing_download`, `test_an_archive_lists_its_entries_up_to_the_cap`.
- **Negative and boundary:** `test_content_that_can_run_is_withheld_with_a_reason_and_no_download`, `test_a_failed_checksum_is_withheld_too`, `test_everything_in_a_descriptor_is_bounded_scalar_text`, `test_a_bad_request_names_what_is_missing`.
- **Authorization:** `test_who_may_preview_follows_the_reviewer_rules`, `test_job_output_visibility_is_the_jobs`, `test_blocked_and_purged_artifacts_get_no_download`.
- **Lifecycle and compatibility:** `test_a_project_artifact_is_pending_until_inspected_then_ready`; the reviewer inspector keeps its download contract.
- **Concurrency:** `test_a_preview_never_inspects_stores_audits_or_fetches`, `test_the_same_subject_always_gives_the_same_descriptor`.
- **UI states:** `w:components/ArtifactPreview.test.tsx` (excerpt as text, withheld, pending, failure with retry, not shown), `w:features/pvs/pvs.test.tsx`, `e:artifact-preview.spec.ts`.

## NOTIFICATIONS (T04)

- **Positive:** `i:test_notifications` `test_a_person_reads_every_category_with_its_channels`, `test_a_broadcast_still_emails_everyone_who_has_not_chosen`.
- **Negative and boundary:** `test_choices_that_may_not_change_or_make_no_sense_are_refused_with_the_field`, `test_unknown_categories_and_channels_are_refused`, `test_the_inbox_and_essential_notices_cannot_be_turned_off_even_by_a_stored_row`.
- **Authorization:** `test_a_person_changes_only_their_own_choice_and_gets_the_new_list`, `test_only_workspace_members_have_preferences_there`, `test_a_choice_in_another_workspace_does_not_stop_this_workspaces_email`.
- **Lifecycle and migration:** additive `core/0006`; `test_without_a_choice_everyone_gets_the_category_default`; an opted-out person keeps the inbox copy (`test_an_opted_out_person_keeps_the_inbox_copy_but_gets_no_email`).
- **Concurrency and idempotency:** `i:concurrency/test_notification_races` `test_simultaneous_first_choices_leave_one_row_and_one_audit_per_real_change`; `test_a_choice_is_idempotent_and_audited_with_before_and_after_only`.
- **UI states:** `w:features/profile/NotificationPreferences.test.tsx` (fixed rows explained, saved, refused keeps the old value, load failure), `e:notifications.spec.ts`.

## VERSION_DIFF (T05)

- **Positive:** `i:test_version_diff` `test_two_form_versions_are_compared_by_field_identity`, `test_rubric_versions_compare_by_criterion_id`, `test_a_configuration_change_carries_the_diff_of_every_changed_field`; shared `diff_cases.json`.
- **Negative and boundary:** `test_the_number_of_changes_is_capped_but_still_counted`, `test_large_values_are_clipped_and_flagged`, `test_very_deep_values_are_compared_as_one_value_not_recursed_into`, `test_text_beyond_the_limits_is_refused_with_a_code`, `test_diffing_never_mutates_or_raises_on_hostile_json`, `test_bad_requests_name_the_parameter_or_are_simply_not_found`.
- **Authorization:** `test_only_organizers_of_the_workspace_may_compare_and_others_learn_nothing`.
- **Lifecycle and compatibility:** `test_a_diff_of_equal_values_is_empty_and_applying_a_diff_rebuilds_the_after_value`, configuration history keeps its entries and gains per-field diffs.
- **Concurrency:** `test_a_comparison_reads_only_and_audits_nothing`, `test_keyed_lists_survive_hundreds_of_items_quickly`.
- **UI states:** `w:components/DiffView.test.tsx`, `w:components/VersionCompare.test.tsx` (fewer than two versions, failures with retry), `w:features/audit/ConfigHistoryPanel.test.tsx`, `e:version-diff.spec.ts`.

## POLICY_EXPLAIN (T06)

- **Positive:** `i:test_explain` `test_the_policy_debugger_explains_a_grant_and_a_missing_policy`, `test_readiness_and_its_legacy_surfaces_carry_the_same_explanation`, `test_consequence_previews_carry_the_explanation_beside_their_blockers`; shared `explain_cases.json` (29 real traces).
- **Negative and boundary:** `test_a_malformed_policy_is_explained_not_raised`, `test_unknown_outcomes_and_severities_are_programming_errors`, `test_a_reason_and_an_explanation_are_bounded_scalar_text`.
- **Authorization and visibility:** `test_hidden_facts_never_appear_for_a_reader_who_may_not_see_them`.
- **Lifecycle and compatibility:** `test_the_policy_debugger_adds_the_explanation_and_keeps_every_existing_key`.
- **Determinism:** `test_the_explanation_always_agrees_with_the_decision_over_random_policies` (600 random policies against the real evaluator); explanation never decides.
- **UI states:** `w:components/ExplanationView.test.tsx`, `w:components/ConsequenceDialog.test.tsx`, `w:features/policy-builder/PolicyDebugger.interaction.test.tsx`, `e:explanations.spec.ts`, `e:event-consequences.spec.ts`, `e:event-readiness.spec.ts`.

## AUDIT_PROVENANCE (T07)

- **Positive:** `i:test_provenance` `test_an_export_says_what_it_was_made_from_and_the_file_matches_its_digest`, `test_a_restore_records_where_it_came_from_and_what_it_changed`.
- **Negative and boundary:** `test_everything_is_bounded_text_and_no_content_is_stored`, `test_attach_keeps_the_rest_of_the_metadata_and_problems_names_what_is_wrong`, `test_a_downloaded_file_is_checked_offline_against_its_record` (an altered file does not match).
- **Authorization:** the envelope lives on the job result and the audit row, so it follows their visibility (`i:test_jobs` `test_who_sees_which_jobs`, configuration history organizer-only).
- **Lifecycle and compatibility:** `test_a_job_kind_that_gives_no_provenance_is_unchanged`, `test_a_signed_export_is_described_by_the_bytes_that_were_downloaded`; rows without an envelope read as `null`.
- **Concurrency and idempotency:** `test_canonical_json_and_its_digest_do_not_depend_on_key_order_or_machine`; stateless over `record_mutation`.
- **UI states:** `w:components/ProvenanceView.test.tsx`, `w:features/operations/JobsPanel.test.tsx`, `e:provenance.spec.ts` (real export and restore, file check; made deterministic in T08 by waiting for the new restore row).

## EXTENSION_MANIFEST (T08)

- **Positive:** `i:test_extension_manifest` `test_the_deployments_manifests_agree_with_the_live_registries` (also `manage.py check`), `test_every_live_entry_is_claimed_by_exactly_one_manifest`, `test_the_inventory_reads_the_registries_that_exist_today`, `test_the_six_sdk_families_and_the_archive_formats_are_all_described`.
- **Negative and boundary:** `test_each_kind_of_disagreement_is_reported_with_a_code_and_the_manifest`, `test_an_incomplete_manifest_is_reported`, `test_a_registered_entry_nobody_declares_is_a_warning_not_an_error`, `test_the_django_system_check_turns_errors_into_a_startup_failure`.
- **Authorization:** `test_organizers_and_admins_read_the_inventory`, `test_nobody_else_reads_it_and_nobody_writes_it`.
- **Lifecycle and compatibility:** `test_registration_is_idempotent_and_never_silently_replaced`; `api_version` is the lever; no migration.
- **Concurrency:** stateless, derived at start.
- **UI states:** `w:features/operations/ExtensionsPanel.test.tsx` (consistent, errors as alert, warnings as status, load failure), `e:extensions.spec.ts`.

## Cross-cutting proofs (`test_shared_primitives_b02_regression.py`)

- `test_the_primitive_registry_marks_the_eight_owners_implemented`: `PRIMITIVE_REGISTRY.yaml` agrees with the code.
- `test_core_still_depends_on_no_domain_app`: the eight new core modules import no domain app.
- `test_the_registries_hold_exactly_what_production_registers` and `test_the_extension_inventory_describes_every_registry_of_the_batch_and_the_batch_before`: preview sources, version sources, notification categories and rich profiles are exactly the intended sets and the manifest inventory agrees with them and with batch one's.
- `test_every_route_refuses_signed_out_callers_and_people_outside_the_workspace`: nine routes of the batch; `test_a_participant_gets_the_member_tools_and_nothing_organizer_only`.
- `test_reading_and_previewing_write_nothing_and_are_never_cached`: no audit row from a preview, a read of preferences, the inventory or version history.
- `test_the_one_mutation_of_the_batch_is_audited_with_before_and_after_only`: the notification choice.

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

No schema authoring UI, WYSIWYG editor or per-property conditional rules (T01, T02); no preview of types beyond the descriptors listed, nothing is rendered from a submitted file on the server (T03, by design); no push notifications, per-event preferences or digest scheduling (T04); the compare views cover form and rubric versions only (T05); policy explanations cover the debugger, consequences and readiness only (T06); only the archive export and configuration restore record an envelope and there is no server-side file verification (T07); archive exporter/importer/converter and assignment strategy are declared only and nothing can be installed or enabled from the inventory (T08).
