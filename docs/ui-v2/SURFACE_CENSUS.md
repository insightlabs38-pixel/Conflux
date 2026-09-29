# UI-v2 surface census — baseline cf367cb

Architecture: Django/DRF with React 19/Vite workspaces; URL query workspace/event
selection in `src/web/app/App.tsx`; role fetched from accounts/me before dispatch.
Public `/events/<id>/` uses `presentation/site_urls.py`, `site_views.py`, Django
templates; `?event=` also exposes React EventSite. Both share tokens/components.
Public templates load presentation.css; React loads main.css. Do not confuse them.
PVS panels use Guarded boundaries; individual request/error/retry behavior stays.

Coverage key: R=roles.spec, P=public.spec, S=scenes.spec, L=lifecycle.spec,
V=pvs.spec, A=signin.spec, U=nearby Vitest, I=integration tests.
All listed existing behavior/APIs remain untouched except additive theme (B03)
and identity (B04). No new API is implied by an API-only capability below.
Paths under `src/web/features/` unless a full prefix is given.

| Surface / role                                | Current entry point                                                                 | Baseline issue → batch                                       | Existing coverage |
| --------------------------------------------- | ----------------------------------------------------------------------------------- | ------------------------------------------------------------ | ----------------- |
| Event landing / public                        | presentation/templates/presentation/event_landing.html; public/event-site/EventSite | generic centered hero, tiny header → B03                     | P,S,I,U           |
| Tracks/prizes/resources/sponsors/FAQ / public | presentation/blocks.py; event_landing.html                                          | same plain sections, little hierarchy → B03                  | P,I               |
| Schedule/agenda / public                      | onsite/templates/onsite/agenda.html                                                 | repetitive cards, sparse time hierarchy → B03/B08            | P,S,I             |
| Announcements / public                        | event_landing.html; presentation/public.py                                          | plain bullet list → B03                                      | P,S,I             |
| Gallery/search / public                       | presentation/gallery.html; site_views.gallery                                       | all-text cards, weak identity → B05                          | P,S,I             |
| Project detail / public                       | presentation/project_detail.html, project_story.html                                | title/metadata/text only → B05                               | P,S,I             |
| Results / public                              | presentation/results.html, award_story.html; awards/PublicAwards                    | tiny link lists → B05                                        | P,S,L,I,U         |
| Expo/map / public                             | onsite/templates/onsite/map.html                                                    | raw placement table → B08                                    | P,S,I             |
| Sign in / global                              | app/SignIn                                                                          | small raw form on empty canvas → B01                         | A,S,U             |
| Workspace selector / global                   | app/WorkspaceSelector                                                               | bullet buttons without context hierarchy → B01/B02           | R,S,A,U           |
| App header/navigation / global                | components/AppShell; app/App                                                        | header links, no persistent IA → B02                         | R,S,U             |
| Account/profile / identity                    | accounts.User, accounts/me; no general profile UI                                   | missing reusable profile → B04                               | I (auth)          |
| Portfolio / identity                          | pvs/PostEventPanels.PortfolioPanel; portfolio/views                                 | table substitutes for identity → B04                         | R,S,I,U           |
| Event overview / participant                  | teams/TeamWorkspace                                                                 | unrelated panels in long column → B02/B06                    | R,S,L,V,U         |
| Team/invitations / participant+organizer      | teams/TeamPanel                                                                     | roster bullets and equal-weight actions → B06                | L,R,U,I           |
| Team marketplace / participant                | teams/MarketplacePanel                                                              | skills fields and listings without person identity → B04/B06 | U,I               |
| Project/artifacts / participant               | artifacts/ProjectWorkspace, ArtifactUpload, PreflightChecklist                      | raw stacked controls/evidence → B06                          | L,U,I             |
| Submission lifecycle / participant            | submissions/SubmissionPanel                                                         | weak staged progress; technical hashes dominate → B06        | L,U,I             |
| Eligibility/remediation / participant         | pvs/EligibilityPanels.ProjectEligibilityPanel                                       | terse list, poor issue timeline → B06                        | L,V,U,I           |
| Rules/exceptions / participant+organizer      | pvs/GovernancePanels                                                                | text and forms mixed, raw receipt JSON → B06/B08             | L,V,U,I           |
| Challenges/resources / participant            | pvs/PostEventPanels.ChallengesPanel                                                 | generic lists → B06                                          | V,U,I             |
| Onsite participation / participant            | pvs/OnsitePanels.MyOnsitePanel                                                      | RSVP/session controls undifferentiated → B06                 | V,U,I             |
| Messages / participant+staff                  | communications/Inbox                                                                | inline list → B06/B09                                        | L,V,U,I           |
| Mentorship / participant+mentor               | pvs/MentorshipPanels                                                                | forms/queue lack person context → B04/B06/B09                | V,U,I             |
| Continuation / participant+organizer          | pvs/PostEventPanels                                                                 | another appended panel → B06/B09                             | U,I               |
| Invitations/expertise / judge                 | judging/JudgeInvitationInbox, JudgeExpertisePanel                                   | raw form before primary work → B04/B07                       | R,U,I             |
| Assignment queue/progress / judge             | judging/JudgeWorkspace.ReviewQueue; pvs/JudgeAssignmentsPanel                       | long candidate bullets → B07                                 | R,S,L,U,I         |
| Route/schedule / judge                        | pvs/JudgeRoutePanel; judging/JudgeCalendarPanel                                     | disconnected from queue → B07                                | R,S,U,I           |
| Rubric/scoring / judge                        | judging/JudgeWorkspace.BallotForm                                                   | scoring/artifacts vertically separated → B07                 | L,U,I             |
| Recusal/conflict / judge                      | JudgeWorkspace; evaluations API                                                     | terse action, preserve blind/COI semantics → B07             | U,I               |
| Artifact inspector / judge                    | pvs/JudgingLogisticsPanels.ArtifactInspector                                        | raw facts dominate safe preview → B07                        | L,U,I             |
| Event overview/setup / organizer              | event-builder/EventDashboard                                                        | extremely long form/panel column → B02/B08                   | R,S,U,I           |
| Stages/policy/forms/pages / organizer         | stage-builder, policy-builder, form-builder, page-builder                           | walls of controls, weak save/preview hierarchy → B03/B08/B09 | U,I               |
| Registration/participants / organizer         | event-builder/RegistrationPanel                                                     | flat review list → B08                                       | R,U,I             |
| Eligibility / organizer                       | pvs/EligibilityReviewPanel                                                          | queue/detail stacked, evidence/action confusion → B08        | L,V,U,I           |
| Judging setup/directory/workload / organizer  | judging/EvaluationBuilder, JudgeDirectoryPanel, JudgeWorkloadPanel                  | raw criterion table/forms → B08                              | S,L,U,I           |
| Judging logistics / organizer                 | pvs/OrganizerJudgingLogisticsPanel                                                  | dense unstructured route table → B08                         | S,V,U,I           |
| Deliberation/finalization / organizer         | pvs/DeliberationPanel                                                               | compact table loses comparison hierarchy → B08               | L,S,U,I           |
| Awards/publication / organizer                | awards/AwardsPanel; pvs/PublicationGovernancePanel                                  | calculation/approval/finalization unclear → B08              | L,U,I             |
| Communications / organizer                    | communications/CommunicationsPanel                                                  | bare editor/list → B09                                       | U,I               |
| Onsite/check-in / staff+organizer             | pvs/OnsitePanels; pvs/StaffWorkspace                                                | small actions, table-heavy layout → B08                      | V,S,U,I           |
| Sponsor/resource operations / organizer       | AwardsPanel; challenges/resource APIs                                               | configuration subordinate to award form/API → B08/B09        | U,I               |
| Analytics / organizer                         | analytics API; operations/OperatorConsole                                           | mostly API-first; do not invent metrics → B08/B09            | I                 |
| Integrations/webhooks / organizer+developer   | integrations/WebhooksPanel                                                          | ungrouped status/config → B09                                | U,I               |
| Moderation / organizer                        | moderation API + API explorer                                                       | API-first, no dedicated panel → B09 explorer                 | I                 |
| Audit/operations / organizer                  | audit/ConfigHistoryPanel; operations/OperationsCenter, OperatorConsole              | dense lists and technical controls → B09                     | R,U,I             |
| API explorer / developer                      | features/api-explorer/ApiExplorer; app/main                                         | giant select, weak request/response hierarchy → B09          | S,U,I             |

Models: Page.theme is default/dark/minimal; PageBlock uses safe clean_config and
fixed 12-kind registry. Theme addition must retain this contract, serializers,
archives/importers, static templates, page-builder schemas and conformance checks.
User extends AbstractUser without reusable profile; event MarketplaceProfile already
owns skills/roles/interests/availability/visibility. JudgeExpertiseProfile is
workspace-scoped; portfolio derives memberships/submissions/published awards.
Reuse scoped data without widening directory visibility or identity in blind judging.
Demo seed: integrations/demo_scenarios.py plus demo_showcase management command;
reset submitted/published is documented in operations/DEMO.md.

Verification: pnpm --filter @conflux/web test/lint/build; nearby Vitest interaction
and SSR tests; tests/integration page-builder, accessibility audit/conformance,
portfolio/auth, public presentation and all touched domains; `make verify` is
standard gate. Existing tests/e2e/playwright.config.ts is sequential, desktop
1280 and mobile390, axe/overflow/focus checks in support/roles/public/pvs. Extend
this harness; lifecycle consumes participant24 and requires a fresh submitted reset.
Prior release reports are prior evidence, never a rerun claim.

B01 boundary: semantic tokens and shared controls/type/layout primitives, prove on
SignIn and WorkspaceSelector; no backend changes, no workspace regrouping until
B02, no safe template/theme contract change until B03. Responsive native semantics,
field association, disabled/error state and light/dark/minimal consumers verified.
