"""Features of participation (completeness contract, PD-F003-B01)."""

from core.features import Feature, Lifecycle, provided, register_feature

register_feature(
    Feature(
        key="team",
        label="Team",
        model="participation.Team",
        claims={
            "identity": provided("field:public_id"),
            "validation": provided(
                "check:participation.services.join_team",
                "constraint:participation.Team.unique_team_name_event",
                "test:tests/integration/test_team_lifecycle.py::test_a_team_cannot_exceed_the_maximum_size",
            ),
            "authorization": provided(
                "route:my-team",
                "route:my-team-leave",
                "route:my-team-transfer-captain",
                "route:my-team-invite-list",
                "route:team-invite-redeem",
                "scope:event",
                "readers:members",
                "writers:members",
                "own:team_member",
                "test:tests/integration/test_team_lifecycle.py::test_only_the_captain_can_transfer_captaincy",
                "test:tests/integration/test_feature_authorization.py::test_every_matrix_gate_holds_for_a_wrong_role_a_stranger_and_a_signed_out_caller",
                "test:tests/integration/test_feature_authorization.py::test_a_non_member_of_a_project_can_never_change_it_or_what_hangs_off_it",
                "test:tests/integration/test_feature_authorization.py::test_objects_of_another_workspace_or_event_are_not_found",
            ),
            "audit": provided(
                "write:my-team:POST=team.created",
                "write:my-team-leave:POST=team.member_left",
                "write:my-team-transfer-captain:POST=team.captain_transferred",
                "write:my-team-invite-list:POST=team.invite_created",
                "write:team-invite-redeem:POST=team.invite_redeemed",
                "test:tests/integration/test_feature_audit.py::test_each_declared_change_records_its_audit_action",
                "test:tests/integration/test_feature_audit.py::test_a_refused_change_leaves_no_audit_row",
            ),
            "idempotency": provided(
                "mode:my-team:POST=natural",
                "mode:my-team-leave:POST=natural",
                "mode:my-team-transfer-captain:POST=natural",
                "mode:my-team-invite-list:POST=none@each call issues a new bearer link and a "
                "stored response would keep the invite token; the captain can revoke the "
                "extra link",
                "mode:team-invite-redeem:POST=token@participation.TeamInvite.token",
                "test:tests/integration/test_feature_idempotency.py::test_a_repeated_change_does_what_its_declared_mode_says",
            ),
            "rest": provided(
                "list:my-team-invite-list",
                "detail:my-team",
                "paging:unpaged@bounded: a team has a few invite links",
                "test:tests/integration/test_feature_rest.py::test_every_refusal_of_a_claimed_route_uses_the_shared_error_shape",
                "test:tests/integration/test_feature_rest.py::test_every_claimed_list_returns_what_its_schema_says",
            ),
            "sdk": provided(
                "generated:python",
                "generated:typescript",
                "test:tests/integration/test_feature_sdk.py::test_every_claimed_operation_works_through_the_generated_python_sdk",
            ),
            "search": provided(
                "no_query@a person reads their own team through my-team; teams are searched "
                "through the projects entity",
            ),
            "ui_base": provided(
                "component:src/web/features/teams/TeamPanel.tsx",
                "test:src/web/features/teams/TeamPanel.test.tsx",
            ),
            "ui_advanced": provided(
                "no_advanced@a team is made, joined and led from one screen; there is no query, "
                "comparison or preview beyond it",
            ),
            "bulk": provided(
                "no_bulk@a team is formed and led by its captain; an organizer does not change "
                "teams in a batch",
            ),
            "cli": provided(
                "no_cli@teams are formed and led by their members; the CLI is an organizer tool "
                "for events only",
            ),
            "mcp": provided(
                "no_mcp@teams are formed and led by their members; no agent task needs to read "
                "or change them",
            ),
            "event_as_code": provided(
                "no_eac@teams are runtime participant data formed by the participants themselves",
            ),
            "webhook": provided(
                "silent:team.captain_transferred@no event type exists for team membership yet; "
                "teams are not announced to subscribers",
                "silent:team.created@no event type exists for teams yet; they are formed by "
                "participants and are not announced to subscribers",
                "silent:team.invite_created@an invitation carries a secret token and is private "
                "to the team that sent it",
                "silent:team.invite_redeemed@no event type exists for team membership yet; "
                "teams are not announced to subscribers",
                "silent:team.member_left@no event type exists for team membership yet; teams "
                "are not announced to subscribers",
                "test:tests/integration/test_feature_webhook.py::test_each_audited_change_writes_the_outbox_event_its_claim_names",
            ),
            "archive": provided(
                "table:participation.team",
                "test:tests/integration/test_feature_archive.py::test_each_claimed_table_is_restored_with_its_rows",
            ),
            "analytics": provided(
                "section:teams",
                "measure:teams.total",
                "measure:teams.with_members",
                "measure:teams.project_creation",
                "test:tests/integration/test_feature_analytics.py::test_every_claimed_measure_and_breakdown_is_in_the_summary_of_a_real_event",
            ),
            "privacy": provided(
                "retained:team_memberships",
                "test:tests/integration/test_feature_privacy.py::test_a_real_subject_is_exported_and_erased_as_every_claim_says",
            ),
            "extension": provided(
                "no_extension@teams have no extension point; their membership rules are fixed "
                "in the domain",
            ),
        },
        lifecycle=Lifecycle(
            "none",
            note="Edited in place; joining and leaving are membership rows (TeamMembership).",
        ),
    )
)
