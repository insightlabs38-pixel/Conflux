# PD-F002-B03 verification matrix (T90)

The batch has one primitive, `PREVIEW_CONTEXT` (T01). `i:` is `tests/integration/`, `w:` is `src/web/`, `e:` is `tests/e2e/` (the browser spec runs at 390 and 1440 with axe and an overflow check). Test names are checked to exist by script. The primitive is stateless, so there is no migration and nothing to race.

## PREVIEW_CONTEXT (T01)

- **Positive (realistic persisted data):** `i:test_preview_context` `test_each_role_sees_what_the_form_shows_that_role` (a real form with two published versions, a draft and a conditional field), `test_the_live_view_is_what_participants_get_and_names_its_version`, `test_as_of_a_time_shows_the_version_in_force_then` (published times set to real instants), `test_a_surface_that_is_not_a_form_previews_through_the_same_primitive`, `test_as_of_picks_the_latest_version_kept_at_or_before_that_time`.
- **Negative and boundary:** `test_each_bad_context_part_is_named` (role, time without offset, out of range, before the first version, unknown version, both version and time, unknown key, non-object), `test_an_unversioned_or_roleless_surface_refuses_what_it_cannot_do`, `test_a_surface_input_is_validated_by_the_schema_subset_and_normalised`, `test_a_surface_without_an_input_schema_takes_none`, `test_bad_requests_name_the_part_to_fix`, cross-cutting `test_a_forged_context_is_data_and_never_authority`.
- **Authorization and visibility:** `test_only_organizers_and_admins_preview_and_everything_else_is_404_or_403`, `test_what_the_source_hides_or_the_surface_declines_is_not_visible`, `test_a_role_never_sees_more_than_the_organizer_and_follows_the_forms_own_rule` (40 random forms against `forms.validation.field_in_scope`), cross-cutting `test_only_organizers_and_admins_are_admitted_and_everyone_else_is_refused` (admin, organizer, participant, judge, sponsor, another workspace, signed out) and `test_asking_to_preview_as_a_role_never_changes_what_the_caller_may_do`.
- **Lifecycle, migration, compatibility:** `test_a_pinned_version_does_not_move_when_the_form_is_published_again`, `test_registration_is_idempotent_and_never_silently_replaced` (a unregistered version source is refused), `forms.validation.field_visible` keeps its behavior through the split (the 96 tests selected by `-k form` pass unchanged); no migration, no endpoint changed.
- **Concurrency and idempotency:** stateless and read-only: `test_a_preview_writes_nothing_acts_as_nobody_else_and_is_never_cached`, cross-cutting `test_a_preview_leaves_no_trace` (no audit row, no form or version row, 405 for every other method), repeat calls return the same answer (`test_as_of_picks_the_latest_version_kept_at_or_before_that_time`).
- **No impersonation, one source of truth:** `test_no_domain_code_reads_a_preview_context` and cross-cutting `test_no_context_is_read_by_a_header_cookie_session_or_a_domain_write`: only core, the form surface and the manifest read a context; no header, cookie or session carries one.
- **Extension boundary and inventory:** `test_the_inventory_lists_the_surface_and_the_forms_manifest_claims_it`, cross-cutting `test_the_surfaces_are_exactly_what_production_registers_and_the_inventory_agrees` and `test_the_primitive_registry_marks_the_owner_implemented`.
- **UI states and viewports:** `w:components/PreviewBar.test.tsx` (sentence, controls, version and time clear each other, back to live, notices, busy, absent controls, time round trip), `w:features/form-builder/FormPreviewAs.test.tsx` (live, person, time before any version with the controls kept, retry on first failure, empty states, refresh after save, notice), `w:features/form-builder/FormBuilder.previewas.test.tsx` (closed by default, asks only once opened), `w:lib/primitives.b03.contract.test.ts`, `e:preview-context.spec.ts` at 390 and 1440 with a real form, three people, two versions and times.

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

Only forms are previewable (rubric and page surfaces are not registered); a preview is not kept in the URL so it cannot be shared as a link; the saved-form preview lists fields and their conditions but does not evaluate answers; the form builder's live editor preview of unsaved edits stays local by design.
