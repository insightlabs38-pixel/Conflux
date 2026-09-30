---

# Part IX — Utility-Filtered Missed Opportunity Pass

**Second-pass date:** 2026-09-29

This pass deliberately uses a stricter inclusion test than the first feature atlas.

The goal is **not** to maximize the number of features. The goal is to find capabilities that:

1. eliminate a real spreadsheet/form/chat/manual workflow organizers already perform;
2. remove repeated work or a common source of event failure;
3. materially improve participant, judge, mentor, sponsor, volunteer, or organizer experience;
4. satisfy a feature people reasonably expect from serious event software;
5. strengthen an existing Conflux subsystem through a natural adjacent workflow; or
6. create a reusable primitive that makes several high-value workflows cheaper.

A feature should generally **not** be added when its primary justification is:

- “the architecture can support it”;
- “it sounds enterprise”;
- “it would be technically impressive”;
- adding verification to already-verifiable verification;
- wrapping an ordinary database fact in another digest/signature/ledger without changing a human workflow;
- adding AI where a deterministic operation is faster and more trustworthy;
- recreating a full external product category when a clean integration solves the problem;
- surveillance or analytics that collect data without a clear operator/participant benefit.

The practical ceiling is therefore not “everything an event could theoretically track.” It is **everything that makes running, participating in, judging, or extending a hackathon materially better.**

## 72. Findings from the second research pass

Several useful gaps stand out after comparing Conflux against current hackathon products, active organizer guidance, and recent participant complaints.

### A. Conflux is deeper than most platforms in competition mechanics, but real-world event operations are still underrepresented

Major League Hacking's organizer guide treats the following as normal hackathon operations:

- food and dietary restrictions;
- swag and prize distribution;
- transportation and travel reimbursement;
- hardware;
- emergency planning;
- help desks;
- detailed run-of-show;
- volunteer duties;
- judge communication and briefing;
- participant reminders;
- code-of-conduct acknowledgement;
- minor forms where needed;
- event closeout.

These are not novelty features. They are exactly the categories that often end up in spreadsheets, Google Forms, Discord channels and paper checklists.

### B. Judging trust is a current participant problem

Recent public hackathon discussions show frustration not merely with scores, but with uncertainty over whether projects were actually reviewed, demos were watched, and judges left any feedback at all.

The useful response is **review process evidence**:

- Was every project assigned enough independent reviews?
- Were all required rubric fields completed?
- Did a judge actually open the frozen project evidence before finalizing?
- Was a required demo artifact marked reviewed?
- Were judge dropouts repaired before results?
- Was feedback captured and released according to policy?

The useful answer is *not* invasive activity surveillance or publishing judges' private behavior.

### C. Current smaller competitors emphasize workflow simplicity around judging

HackHQ's 2026 additions include:

- parallel judging rooms;
- track/challenge scoring;
- top-picks voting;
- custom judge assignment;
- live completion views;
- CSV participant import;
- accountless submission links;
- embedded demo video;
- organizer announcements.

Conflux already has more sophisticated primitives than many of these, but some of the **simple workflow affordances** remain valuable. Sophisticated backend models should make ordinary cases easier, not require advanced configuration.

### D. Sponsors and recurring programs want measurable outcomes

Current platforms increasingly pitch:

- sponsor onboarding;
- challenge adoption;
- participant engagement;
- recruiting pipelines;
- sponsor ROI;
- repeat-event reuse.

This suggests a useful layer above Conflux's sponsor challenges/resources: deliverables, engagement, opt-in talent discovery, and repeat-program reporting.

### E. Event organizers still use separate software for operational tasks

MLH's own software guide references tools for:

- applications;
- RSVPs;
- buses;
- travel reimbursement;
- mentorship queues;
- expo/table assignment;
- judging.

Conflux already owns many of these domains. The remaining useful opportunity is to close the high-friction gaps while resisting the temptation to become a full accounting, travel-booking, messaging, HR, or ticket-commerce suite.

---

# Part X — High-value missed opportunities

## 73. Personalized participant event pass / “My Event” hub

This is one of the most useful missing unification layers.

Instead of making a participant hunt through team, project, resources, schedule and check-in surfaces, provide one compact **My Event** page that answers:

- Am I accepted/confirmed?
- What do I need to do next?
- Who is on my team?
- What stage is my project in?
- When is the next deadline?
- What room/table am I assigned?
- What sessions did I RSVP to?
- What is my QR check-in pass?
- Which rules/waivers still need acknowledgement?
- Do I have unresolved eligibility findings?
- Do I have a mentor booking?
- When/where do I present?
- Has my submission finalized successfully?
- When will judging/results happen?
- Where are venue/travel instructions?

Useful depth:

- BASE — generated checklist ordered by urgency.
- BASE — exact next deadline with event/local timezone.
- BASE — QR event pass.
- BASE — team/project status.
- BASE — venue and check-in information.
- BASE — “you are ready” state when nothing remains.
- ADV — personalized schedule.
- ADV — meal/room/table/badge entitlements where enabled.
- ADV — travel/reimbursement status.
- ADV — accommodation request status.
- ADV — emergency/event contact.
- ADV — offline-friendly mobile version.
- ADV — wallet/pass export if easy to implement cleanly.
- PROG — hub is derived from canonical state; it should not introduce another workflow truth source.

**Why include:** It reduces navigation cost across almost every participant workflow and makes the large feature count feel simpler.

## 74. Staff, judge, mentor, speaker and volunteer recruitment/onboarding

Conflux has role workspaces, but there is value in the workflow *before* someone becomes an active staff member.

- BASE — public/private interest form for judge/mentor/volunteer/speaker.
- BASE — invitation and acceptance/decline.
- BASE — role-specific onboarding checklist.
- BASE — event date/time/location expectations.
- BASE — Code of Conduct/rules acknowledgement.
- ADV — availability windows.
- ADV — expertise/track preferences.
- ADV — role capacity/needed-count target.
- ADV — organizer review/approval.
- ADV — bulk invite.
- ADV — reminder sequence for unconfirmed invitees.
- ADV — waitlist/backup pool.
- ADV — previous-event role history.
- ADV — “confirmed / tentative / declined / no response” dashboard.
- EXPERT — reusable cross-event staff directory.
- EXPERT — suggested judge/mentor candidates from prior events, never automatic outreach.
- PROG — invitation state should feed staffing and judging-readiness calculations.

**Why include:** Judge/mentor recruitment happens before the sophisticated assignment features can help.

## 75. Judge briefing, training and readiness gate

Conflux's judging math is sophisticated enough that judge readiness deserves first-class support.

- BASE — organizer briefing page containing rubric, timing, event philosophy and logistics.
- BASE — judge acknowledgement before first ballot.
- BASE — example scorecard.
- BASE — clear conflict/recusal instructions.
- BASE — judging-location or remote-call instructions.
- ADV — short calibration/example project.
- ADV — “score this example, then compare with anchors.”
- ADV — required briefing completion if organizer enables it.
- ADV — rubric-change acknowledgement when a published judging configuration changes before judging.
- ADV — judge FAQ.
- ADV — one-click report-a-problem/help request from judging workspace.
- ADV — briefing completion/readiness dashboard.
- EXPERT — organizer can require calibration tolerance before assignments are released.
- EXPERT — different briefing modules per judge pool/award.

**Why include:** MLH explicitly recommends a judging debrief because day-of judge process quality is a major failure mode.

## 76. Judge staffing and capacity planner

Conflux can turn its assignment knowledge into pre-event planning.

- BASE — estimate judge count needed from expected projects, reviews/project, minutes/review and judging window.
- BASE — compare required vs confirmed judges.
- BASE — show capacity shortage before judging begins.
- ADV — incorporate track-specific judge requirements.
- ADV — incorporate physical walking/travel time.
- ADV — incorporate judge availability windows.
- ADV — incorporate sponsor/award pools.
- ADV — scenario slider: 100 / 150 / 200 expected projects.
- ADV — no-show reserve recommendation.
- ADV — forecast latest likely completion.
- ADV — “what if 20% more projects submit?” scenario.
- EXPERT — use historical submission/check-in ratio as an optional forecast input.
- EXPERT — Monte Carlo-style dropout sensitivity only if it produces clear staffing recommendations.

**Why include:** This converts existing solver sophistication into a pre-event decision tool organizers can actually use.

## 77. Review coverage and judging-completeness evidence

This is a strong trust feature with a clear use.

For organizers:

- BASE — every project shows required reviews vs completed reviews.
- BASE — every ballot shows complete/incomplete without exposing peer scores to judges.
- BASE — missing rubric criteria highlighted.
- BASE — project with zero completed reviews is impossible to overlook.
- ADV — required demo/evidence checklist marked reviewed.
- ADV — stale/in-progress ballot detection.
- ADV — judge no-show/dropout warnings.
- ADV — deadline projection from current completion rate.
- ADV — auto-suggest rebalancing when coverage is at risk.
- ADV — “unreviewed for X minutes” operations view.
- ADV — finalist cannot silently advance while required coverage is missing unless an authorized override is recorded.
- EXPERT — evidence graph showing which independent completed reviews support each official ranking/award.

For participants, optionally after judging:

- BASE — show number of completed official reviews.
- ADV — show whether required demo/artifact evidence was included in the official frozen review package.
- ADV — release rubric feedback according to event policy.
- ADV — never expose private judge activity timelines or identities unless the event explicitly publishes them.

**Why include:** It directly addresses a common participant trust complaint without adding performative cryptography.

## 78. Judge no-show and live reassignment mode

Normal assignment planning is not enough for real events.

- BASE — mark judge unavailable/no-show.
- BASE — immediately show impacted projects.
- BASE — suggest safe replacement assignments.
- BASE — preserve completed ballots.
- ADV — reserve judge pool.
- ADV — reassign only unfinished obligations.
- ADV — physical-route recalculation.
- ADV — notify affected judge/organizer.
- ADV — restore judge if they return.
- ADV — explain any resulting coverage/connectivity degradation.
- EXPERT — rapid repair plan that minimizes movement and workload disruption while preserving hard constraints.

**Why include:** High-value use of existing assignment algorithms during the exact period organizers are under maximum pressure.

## 79. Demo/pitch queue and presentation timer

Many events have live pitches, finals or scheduled demos in addition to science-fair judging.

- BASE — create demo session/room.
- BASE — ordered team queue.
- BASE — visible current/next team.
- BASE — configurable presentation and Q&A timer.
- BASE — presenter “ready/not ready.”
- ADV — multiple parallel rooms.
- ADV — judge panel per room.
- ADV — delay/reorder controls.
- ADV — screen/projector display mode.
- ADV — participant mobile queue position.
- ADV — automatic “report to staging area” notification.
- ADV — no-show handling.
- ADV — recording/video link attached to presentation slot.
- ADV — finalist queue built directly from deliberation result.
- EXPERT — room balancing from projected duration and judge availability.

**Why include:** It replaces the common spreadsheet + stopwatch + Discord message workflow.

## 80. Event run-of-show and live control timeline

A schedule tells attendees what happens. A **run-of-show** tells organizers what needs to happen behind the scenes.

- BASE — operational timeline separate from public schedule.
- BASE — tasks with owner, due time and status.
- BASE — dependencies.
- BASE — role/team assignment.
- BASE — “happening now / next 30 minutes / overdue.”
- ADV — reusable templates: doors open, meal arrival, submission freeze, judge briefing, judging start, finalists, closing.
- ADV — private notes and contingency instructions.
- ADV — attach runbook/checklist.
- ADV — confirm critical milestones.
- ADV — bulk “mark ready.”
- ADV — last-minute delay shifts downstream target times with preview.
- ADV — communication action linked to milestone.
- ADV — incident linked to timeline.
- EXPERT — rehearsal mode / dry run.
- PROG — timeline hooks can fire deterministic reminders, never autonomous irreversible operations.

**Why include:** This is core event management work and prevents Conflux from stopping at the competition boundary.

## 81. Volunteer shift and duty management

Avoid becoming workforce-management software; solve the event-specific problem.

- BASE — volunteer roles/duties.
- BASE — shifts and availability.
- BASE — assign volunteers.
- BASE — check-in/out of shift.
- BASE — instructions/location.
- ADV — min staffing per duty.
- ADV — shortage warnings.
- ADV — swap/reassignment.
- ADV — mobile “my shift.”
- ADV — role-specific checklists.
- ADV — meal/break windows.
- ADV — emergency-contact escalation.
- ADV — history of completed duties for organizer reference.
- EXPERT — automatically propose assignments from availability/skills.
- PROG — shift state appears in live operations dashboard.

**Why include:** MLH explicitly tells organizers to confirm volunteer duties; large in-person events often run these from sheets.

## 82. Help desk / organizer support queue

Mentor help and operational help are different.

- BASE — attendee can ask a logistics/event question.
- BASE — categories: registration, team, submission, venue, accessibility, technical platform, prize, other.
- BASE — triage/claim/resolve.
- BASE — participant sees status.
- ADV — priority/urgency.
- ADV — location/room.
- ADV — internal note vs participant-visible response.
- ADV — canned answers linked to FAQ.
- ADV — convert repeated issue into announcement/FAQ suggestion.
- ADV — handoff to mentor queue when question is actually technical.
- ADV — organizer SLA and backlog dashboard.
- ADV — Discord/Slack intake adapter if desired.
- EXPERT — outage/banner mode when many tickets share one incident.

**Why include:** This is a real event workflow and naturally reuses the mentor queue primitive.

## 83. Code of Conduct acknowledgement and incident workflow

Conflux has moderation/governance, but event-safety incidents are a distinct operational domain.

- BASE — published Code of Conduct.
- BASE — required acknowledgement at registration/check-in when configured.
- BASE — private incident-report form.
- BASE — named or anonymous reporting depending on event policy.
- BASE — restricted incident visibility to authorized safety staff.
- BASE — status: received / investigating / resolved.
- ADV — severity/category.
- ADV — incident assignment.
- ADV — evidence attachments.
- ADV — protective action notes.
- ADV — attendee restriction/ban integrated with check-in.
- ADV — internal immutable history.
- ADV — emergency contacts/resources.
- ADV — separate public communication from private case record.
- EXPERT — cross-event restriction lists only where the organization has an appropriate policy/legal basis.
- SECURITY — this domain should have stricter access/audit/retention than ordinary moderation.

**Why include:** MLH explicitly requires a clear incident-reporting system and Code of Conduct acknowledgement.

## 84. Minor/guardian forms and participant consent records

Do not build a legal-document platform. Build a clean evidence/requirements workflow.

- BASE — organizer-defined required acknowledgement/consent documents.
- BASE — versioned text/PDF.
- BASE — participant acknowledgement timestamp and document version.
- ADV — guardian-required flag based on configured age rules.
- ADV — guardian contact and completion state.
- ADV — upload externally signed form where required.
- ADV — expiration/re-sign if the document changes materially.
- ADV — check-in blocks only when organizer explicitly configures the document as required.
- ADV — media/photo consent as a separate opt-in/out record.
- ADV — privacy notice acknowledgement.
- EXPERT — external e-signature provider integration instead of implementing legal signatures in core.

**Why include:** Minor forms and participant acknowledgements are common at student events; workflow state matters even when legal signing is external.

## 85. Accessibility accommodation requests

Accessibility should include operational accommodation, not only WCAG.

- BASE — optional accommodation request during registration.
- BASE — free-text and organizer-defined categories.
- BASE — private visibility to designated staff.
- BASE — participant can update request until a configured cutoff.
- ADV — request status and organizer note.
- ADV — accessible seating/location assignment.
- ADV — interpreter/captioning requirement.
- ADV — dietary request linkage where relevant.
- ADV — mobility/access route notes.
- ADV — session-level accommodation needs.
- ADV — individualized check-in instructions.
- EXPERT — aggregate planning counts that hide sensitive details from staff who do not need them.

**Why include:** It improves an actual participant workflow and extends accessibility beyond visual frontend compliance.

## 86. Dietary needs, meal planning and distribution

Do not become catering software; solve the organizer counts and participant entitlement problem.

- BASE — dietary/allergy fields during registration.
- BASE — aggregate counts for authorized organizers.
- BASE — meal schedule.
- ADV — meal entitlement by checked-in status/role.
- ADV — QR/badge meal claim.
- ADV — count remaining/served.
- ADV — dietary label shown only to appropriate distribution staff, not publicly.
- ADV — meal vendor count export.
- ADV — shortage warning from RSVP/check-in counts.
- ADV — organizer can mark special meal pickup.
- ADV — unused/overage estimate for post-event analysis.
- SECURITY — allergy/dietary data gets restricted visibility and retention controls.

**Why include:** Food and dietary planning is explicitly ordinary hackathon work and currently falls outside most competition platforms.

## 87. Travel, buses and reimbursement

This should be bounded and optional.

- BASE — event travel instructions and venue directions.
- BASE — parking/transit information.
- BASE — travel-assistance eligibility policy.
- ADV — attendee reimbursement request.
- ADV — amount/cap based on organizer rules.
- ADV — receipt upload.
- ADV — submitted/approved/paid/rejected status.
- ADV — organizer export to actual finance/payment system.
- ADV — bus/shuttle route and RSVP.
- ADV — seat capacity/waitlist.
- ADV — arrival/departure manifest for organizer.
- ADV — carpool interest as an opt-in discovery field; do not expose exact home addresses.
- ADV — hotel/accommodation instructions and externally managed booking reference.
- EXPERT — external finance provider integration for reimbursement payment.
- DO NOT BUILD — airline/hotel booking engine, payment processor, tax platform.

**Why include:** Hackathon software historically includes travel reimbursement and bus coordination; MLH has explicit travel/reimbursement guidance.

## 88. Hardware lab, loaner and equipment checkout

Especially valuable for hardware, robotics and sponsor-device events.

- BASE — inventory item/type and quantity.
- BASE — checkout/return to participant/team.
- BASE — item identifier/QR.
- BASE — current availability.
- ADV — reservation queue.
- ADV — item condition.
- ADV — due/return reminder.
- ADV — consumable vs returnable.
- ADV — restricted equipment requiring approved training.
- ADV — equipment location.
- ADV — missing/damaged status.
- ADV — per-team quota.
- ADV — sponsor-owned inventory.
- ADV — setup/tutorial linked to equipment.
- EXPERT — lab capacity/time-slot reservation for machines such as laser cutters/3D printers.
- EXPERT — safety acknowledgement before restricted tool use.
- DO NOT BUILD — general asset-management/ERP system.

**Why include:** Hardware resources are a real differentiator for physical events and fit naturally with sponsor resources, check-in and team state.

## 89. Swag, prize inventory and distribution

Prizes already have fulfillment. The same simple inventory primitive can handle event materials.

- BASE — item, variant/size, stock.
- BASE — eligibility group.
- BASE — claimed/unclaimed.
- ADV — size preference at registration.
- ADV — QR/badge claim.
- ADV — prevent duplicate claim.
- ADV — low-stock warning.
- ADV — role-specific packs.
- ADV — sponsor swag allocation.
- ADV — leftover/undistributed count.
- ADV — winner physical prize handoff.
- ADV — shipping-needed flag for remote winners.
- EXPERT — external fulfillment/shipping integration.
- DO NOT BUILD — warehouse management.

**Why include:** Organizers repeatedly track shirts, stickers, packs and physical prizes manually.

## 90. Badge, signage and print center

The onsite subsystem already has enough structured data to generate useful physical artifacts.

- BASE — badge templates by role.
- BASE — participant name + QR + role.
- BASE — print single/reprint.
- BASE — table/project number cards.
- ADV — sponsor/judge/mentor badge styles.
- ADV — session/room signs.
- ADV — judging table labels.
- ADV — dietary/accessibility indicator only where appropriate and privacy-safe.
- ADV — print queue.
- ADV — batch PDF.
- ADV — parking pass templates.
- ADV — emergency/contact cards.
- EXPERT — label-printer adapter.
- PROG — print layouts use canonical event/person/project data.

**Why include:** MLH literally lists badges/lanyards, parking passes, minor forms and table numbers as things organizers prepare.

## 91. Event emergency and incident operations

Separate emergency operations from Code-of-Conduct case management.

- BASE — emergency contact/runbook page for staff.
- BASE — venue emergency instructions.
- BASE — organizer “critical announcement” channel.
- ADV — incident type: medical, fire/alarm, weather, building, network/power, security, other.
- ADV — incident commander/owner.
- ADV — staff-only timeline.
- ADV — impacted rooms/sessions.
- ADV — attach emergency procedure.
- ADV — trigger public/role-scoped announcement with explicit human confirmation.
- ADV — post-incident notes.
- EXPERT — offline printable/exportable emergency pack.
- DO NOT BUILD — emergency dispatch or medical record system.

**Why include:** Emergency planning is ordinary live-event responsibility; Conflux already has communications and onsite state to make it useful.

## 92. Venue readiness / setup checklist

A small feature with large day-of value.

- BASE — reusable event setup checklist.
- BASE — owner/status.
- BASE — room/location.
- BASE — due-by time.
- BASE — items such as Wi-Fi, power, tables, signage, check-in station, judging area, food, AV.
- ADV — photo/evidence attachment where useful.
- ADV — issue/blocker flag.
- ADV — template based on event mode/features.
- ADV — “all critical venue items ready” gate.
- ADV — teardown checklist.
- ADV — post-event venue handback checklist.

**Why include:** It replaces a mundane but high-risk checklist with almost no conceptual overhead.

## 93. Budget, sponsor commitments and event expenses — deliberately narrow scope

A lightweight event budget can remove a major spreadsheet without becoming accounting software.

- BASE — planned budget categories.
- BASE — committed vs actual.
- BASE — sponsor cash/in-kind commitments.
- BASE — event expenses.
- BASE — receipt/document attachment.
- ADV — vendor/expense status: planned/ordered/invoiced/paid.
- ADV — reimbursement linkage.
- ADV — sponsor commitment due date.
- ADV — per-attendee cost.
- ADV — budget variance.
- ADV — category export.
- ADV — read-only finance role.
- EXPERT — accounting/payment integrations via export/API.
- DO NOT BUILD — double-entry accounting, payroll, bank reconciliation, tax preparation.

**Why include:** Every hackathon has a budget, and MLH's own organizer model treats finance as a core organizing function.

## 94. Sponsor pipeline and deliverable tracker

Conflux's sponsor resources/challenges begin after sponsorship exists. Organizers also need to ensure promised deliverables happen.

- BASE — sponsor organization/contact.
- BASE — sponsorship tier/package.
- BASE — committed cash/in-kind value.
- BASE — promised deliverables checklist.
- BASE — challenge/prize/resource links.
- ADV — logo/content deadline.
- ADV — workshop/office-hours slot.
- ADV — judge/mentor seats.
- ADV — booth/table placement.
- ADV — included announcement/email obligations.
- ADV — attendee data-sharing terms represented explicitly; never assumed.
- ADV — fulfillment owner/status.
- ADV — post-event sponsor report.
- ADV — renewal/follow-up reminder.
- EXPERT — import/export to external CRM instead of turning Conflux into Salesforce.
- DO NOT BUILD — full sales CRM pipeline unless later demand proves it belongs.

**Why include:** It connects sponsorship promises to actual event operations and sponsor ROI.

## 95. Sponsor ROI and challenge adoption report

A practical post-event artifact.

- BASE — challenge page views.
- BASE — challenge opt-ins.
- BASE — eligible/submitted projects.
- BASE — awarded projects.
- BASE — workshop attendance.
- ADV — resource link engagement.
- ADV — mentor/office-hours usage for sponsor challenge.
- ADV — project technologies used, based on participant-declared data.
- ADV — participant feedback about sponsor tools.
- ADV — sponsor feedback survey.
- ADV — public result/project links.
- ADV — configurable report branding/export.
- EXPERT — recruiting/product-adoption metrics only with participant consent and clear data provenance.
- DO NOT BUILD — invasive browser/user tracking merely to inflate sponsor metrics.

**Why include:** Current hackathon platforms explicitly market sponsor ROI; this makes sponsorship easier to renew.

## 96. Participant recruiting / talent opt-in

This can be useful if participant-controlled.

- BASE — optional “open to opportunities” profile setting.
- BASE — participants choose which profile fields can be shared.
- BASE — event-specific consent.
- ADV — sponsor/recruiter can filter only consenting participants.
- ADV — bookmarks/shortlists.
- ADV — participant can see which organizations received their profile if the event chooses transparent sharing.
- ADV — follow-up status is optional and private to authorized recruiting staff.
- ADV — opt-out/revoke where legally feasible.
- EXPERT — export to external ATS/CRM.
- DO NOT BUILD — full applicant tracking system.
- DO NOT BUILD — automatic “candidate quality” scoring from hackathon judging results.

**Why include:** Recruiting is a common sponsor/organizer goal, but it should not compromise the competition experience.

## 97. Participant surveys and event feedback

A small general form use can produce high-value event learning.

- BASE — post-event participant survey.
- BASE — judge/mentor/volunteer/sponsor survey variants.
- BASE — anonymous or identified mode.
- BASE — reminder.
- BASE — simple results/CSV.
- ADV — NPS-style question if organizer wants it.
- ADV — session/workshop feedback.
- ADV — sponsor-tool feedback.
- ADV — segment aggregate results by role/track without exposing small sensitive groups.
- ADV — recurring-event comparison.
- ADV — turn common complaints into next-event tasks/templates.
- EXPERT — survey templates attached to event presets.

**Why include:** Serious recurring programs need feedback, and Devpost/competitors explicitly advertise survey/reporting.

## 98. Event closeout workflow

Closing results is not the same as closing the event operationally.

- BASE — winners published.
- BASE — prizes/fulfillment outstanding.
- BASE — reimbursement outstanding.
- BASE — sponsor report outstanding.
- BASE — survey sent.
- BASE — volunteer/judge thank-you communications.
- BASE — archive/export complete.
- ADV — equipment returned.
- ADV — swag/prize leftovers accounted for.
- ADV — incident/helpdesk cases closed.
- ADV — post-event project continuation policy activated.
- ADV — static archive snapshot generated.
- ADV — event metrics frozen into final report.
- ADV — lessons/retrospective notes.
- ADV — clone-next-year action after closeout.
- EXPERT — generated closeout packet for partner organizations.

**Why include:** MLH explicitly treats event closeout as a separate workflow; Conflux has enough source data to make it automatic.

## 99. Participation certificates and verifiable event credentials

This is useful if kept simple.

- BASE — participation certificate for checked-in participants under configured eligibility.
- BASE — winner/finalist/judge/mentor/volunteer certificate templates.
- BASE — unique public verification URL or code.
- BASE — PDF generation.
- ADV — certificate eligibility from canonical attendance/submission/judging state.
- ADV — organizer revoke/correct/reissue.
- ADV — badge/credential metadata export.
- ADV — LinkedIn-friendly share link.
- EXPERT — Open Badges-compatible export if it remains low-complexity.
- DO NOT BUILD — blockchain credentials.
- DO NOT BUILD — layers of signatures over a simple verification URL unless a partner explicitly needs signed portable credentials.

**Why include:** Certificates are commonly requested, easy to derive from state Conflux already owns, and useful to participants/staff.

## 100. Marketing attribution and registration-source tracking

A modest feature, not an ad-tech stack.

- BASE — optional registration-source field.
- BASE — UTM/referral capture.
- ADV — campaign/source funnel: visit → register → confirm → check in → submit.
- ADV — partner/referral link.
- ADV — outreach channel comparison.
- ADV — recurring-event invite cohort.
- ADV — public event page conversion.
- EXPERT — privacy-preserving aggregate reporting.
- DO NOT BUILD — cross-site tracking/fingerprinting.
- DO NOT BUILD — marketing automation suite.

**Why include:** Organizers need to know whether outreach worked; recurring programs especially benefit.

## 101. Referral / ambassador links

This is useful only as a thin layer over attribution.

- BASE — organizer can issue a referral link to a club/community/ambassador.
- BASE — count registrations and confirmed attendees from that source.
- ADV — optional referral leaderboard if event culture benefits from it.
- ADV — source-specific landing copy.
- ADV — prevent incentives from altering admission/judging.
- DO NOT BUILD — multi-level referral/affiliate system.

**Why include:** It can help campus/community hackathons grow without becoming marketing-tech bloat.

## 102. Rules and originality disclosure package

The existing eligibility system can absorb a practical challenge that has become more important with AI tools and reuse.

- BASE — participant explicitly declares whether project work began before the allowed window.
- BASE — framework/library/tool disclosure.
- BASE — AI-tool usage disclosure when event requires it.
- BASE — third-party assets/data/API disclosure.
- BASE — cross-submission/cross-posting declaration.
- BASE — license/permission acknowledgement.
- ADV — structured “what existed before vs what we built during the event.”
- ADV — per-component provenance note.
- ADV — pre-existing repository commit/reference.
- ADV — organizer clarification request.
- ADV — disclosure frozen with submission.
- ADV — check disclosed tools against track/sponsor eligibility rules.
- EXPERT — optional code/repository diff evidence from a declared starting commit.
- EXPERT — plagiarism/similarity scanners only as review signals, never automatic guilt.
- DO NOT BUILD — invasive developer surveillance or IDE monitoring.

**Why include:** MLH's current rules explicitly discuss prior work, frameworks and AI disclosure. A structured workflow is better than burying this in README text.

## 103. Contribution roles / team contribution record

Useful for judging and recruiting when participant-controlled.

- BASE — team members list roles/contributions.
- BASE — contribution statement frozen with submission.
- ADV — per-member technical/design/research/demo contributions.
- ADV — participant confirmation that team statement is accurate.
- ADV — organizer clarification if a prize is individual or role-restricted.
- EXPERT — repository contribution metadata can be shown only as supporting evidence; do not equate commit count with contribution quality.
- DO NOT BUILD — algorithmic “who really did the work” scoring.

**Why include:** Helps judges understand team composition and reduces ambiguity for prizes/recruiting.

## 104. Demo evidence checklist and pitch readiness

The project authoring system can help teams present the work judges actually need to see.

- BASE — event-defined required demo duration/format.
- BASE — upload/link video.
- BASE — project preflight says whether demo evidence is present.
- ADV — checklist from judging criteria: core flow, technical architecture, limitation disclosure, sponsor requirement.
- ADV — video duration validation.
- ADV — transcript/captions supplied by participant/provider where available.
- ADV — judge can mark demo artifact reviewed.
- ADV — exact demo URL/version frozen with submission.
- EXPERT — participant “judge preview” mode that shows exactly what a judge sees.

**Why include:** MLH recommends short demo videos specifically to improve judging; recent participant complaints show why evidence visibility matters.

## 105. Live result incident / correction playbook

Results publication is high-stakes enough for a dedicated recovery workflow.

- BASE — pre-publish preview.
- BASE — atomic publish.
- BASE — rollback visibility if publication fails before becoming official.
- BASE — correction workflow after official publication.
- ADV — affected award/project list.
- ADV — correction reason.
- ADV — participant notification plan.
- ADV — public correction notice.
- ADV — archive retains previous result version.
- ADV — prize-fulfillment hold when result is disputed/corrected.
- EXPERT — rehearse publication against a demo/rehearsal event.

**Why include:** Prevents the worst possible “live projector + wrong winners” scenario and reuses existing publication/audit primitives.

## 106. Event change impact and notification assistant

When organizers change dates, rooms, requirements or rules, the system should identify affected people/workflows.

- BASE — configuration change preview says what operational state is impacted.
- ADV — identify participant cohorts affected by deadline/location/schedule change.
- ADV — suggest audience for notification.
- ADV — show existing scheduled communications that became stale.
- ADV — identify Event-as-Code docs/public pages that reference old value.
- ADV — require explicit acknowledgement for high-impact live-event change.
- ADV — create draft announcement from structured change facts; human edits/sends it.
- EXPERT — dependency graph across event config, pages, schedule, policies and integrations.

**Why include:** MLH explicitly emphasizes communicating major event changes quickly; Conflux has the domain data to automate the tedious impact discovery.

## 107. Recurring event edition / year-over-year comparison

Conflux already has cloning and cross-event history; add a practical recurring-program workflow.

- BASE — “create next edition from this event.”
- BASE — explicit carry-over selection.
- BASE — preserved sponsor/judge/template references where appropriate.
- ADV — compare registration, attendance, submission and judging metrics across editions.
- ADV — compare sponsor challenge adoption.
- ADV — reused vs changed rules/rubrics.
- ADV — copy public pages as drafts with stale-date/link warnings.
- ADV — invite prior judges/mentors/participants selectively.
- ADV — prior-year project archive stays separate.
- EXPERT — organization program dashboard for a recurring series.

**Why include:** Repeat events are common, and recurring setup is where deep configuration can repay itself.

## 108. Public event changelog

A small transparency feature for events with evolving rules/schedule.

- BASE — important organizer changes can optionally be published as a changelog entry.
- BASE — date/time and summary.
- ADV — link to affected rule/schedule/page.
- ADV — “substantive” vs “minor wording” classification.
- ADV — participants can subscribe to changes.
- ADV — auto-draft from a semantic configuration diff.
- DO NOT BUILD — publish every internal audit event.

**Why include:** Participants care when rules/deadlines change, not about internal CRUD logs.

## 109. Participant-facing notification center with actionability

The first pass included notifications; this adds a stronger usefulness requirement.

Every notification should preferably answer:

- What happened?
- Does it require me to act?
- By when?
- Where do I act?
- Can it be safely dismissed?

Useful types:

- team invite;
- application decision;
- waitlist promotion;
- missing RSVP;
- rule acknowledgement;
- submission issue;
- eligibility remediation;
- mentor booking;
- room/table assignment;
- schedule/location change;
- judge assignment;
- feedback released;
- prize fulfillment action.

Avoid:

- noisy “someone viewed your project” activity;
- meaningless engagement gamification;
- duplicated email + banner + inbox messages with no preference controls.

## 110. Calendar and reminder integration

A practical cross-cutting feature.

- BASE — add event and key deadlines to calendar.
- BASE — event timezone embedded correctly.
- ADV — personal schedule iCalendar feed.
- ADV — judge assignment/calendar feed.
- ADV — mentor office-hours calendar.
- ADV — organizer run-of-show calendar.
- ADV — change/cancel updates propagate.
- ADV — configurable reminder preference.
- EXPERT — Google/Microsoft calendar integration only if needed beyond standards-based iCalendar.

**Why include:** Deadlines, sessions and judging windows are time-driven; calendar export is an expected convenience.

## 111. Searchable event knowledge base / FAQ with operational linkage

Conflux already has public Q&A/resources; connect them more tightly to operations.

- BASE — searchable FAQ.
- BASE — organizer-authored canonical answer.
- BASE — public/private audience.
- ADV — help-desk response can link/promote an answer.
- ADV — repeated help requests suggest FAQ gap.
- ADV — sponsor challenge FAQ belongs to sponsor context.
- ADV — rules FAQ links to exact rule.
- ADV — version/update timestamp.
- ADV — participant sees relevant FAQs based on current workflow.
- EXPERT — semantic search can be optional, with deterministic full-text search remaining baseline.

**Why include:** Reduces organizer support load without building a chatbot as the primary answer surface.

## 112. Announcement acknowledgement for critical operational messages

Not every announcement needs it, but sometimes organizers need to know who received a venue/deadline/safety change.

- ADV — announcement can be marked “acknowledgement required.”
- ADV — target audience snapshot.
- ADV — completion list.
- ADV — reminder only to unacknowledged recipients.
- ADV — deadline.
- ADV — used sparingly for rules/safety/location changes.
- DO NOT BUILD — read receipts for every message.

**Why include:** Turns critical communication into a closed-loop workflow.

## 113. Event-specific document/resource center

Useful resources should not be scattered across FAQ, pages, sponsor blocks and messages.

- BASE — organized resources by category.
- BASE — visibility by role/stage.
- BASE — file/link/title/description.
- ADV — version/update timestamp.
- ADV — pin critical resources.
- ADV — acknowledgement requirement when appropriate.
- ADV — downloadable offline event pack.
- ADV — resource health/link checker.
- ADV — archive resources with event.
- ADV — per-track/sponsor resources.

**Why include:** Simplifies event resource discovery and naturally reuses page/resource primitives.

## 114. Speaker/workshop operator workflow

Schedule already covers sessions; add the practical management layer.

- BASE — speaker profile/contact.
- BASE — session assignment.
- BASE — confirmation status.
- BASE — arrival/check-in information.
- ADV — slide/resource upload.
- ADV — AV requirements.
- ADV — room capacity.
- ADV — host/moderator assignment.
- ADV — reminder.
- ADV — recording/publication permission.
- ADV — session feedback.
- DO NOT BUILD — full conference speaker management suite.

**Why include:** Hackathons routinely run technical workshops, sponsor demos and opening/closing talks.

## 115. Prize claim and winner support inbox

Prize fulfillment can become a participant-friendly workflow.

- BASE — winner sees prize, status and required next action.
- BASE — secure contact/update form.
- ADV — required shipping/payment info fields determined by prize type.
- ADV — document request through external provider where sensitive.
- ADV — claim deadline.
- ADV — organizer/sponsor note.
- ADV — missing information reminder.
- ADV — support ticket linked to award.
- ADV — shipped/sent/claimed status.
- ADV — correction/alternate winner handling.
- SECURITY — minimize storage of sensitive financial/tax data; integrate rather than retain when possible.

**Why include:** Winning should not drop users into an email thread maze.

## 116. Event “doctor” and operator readiness diagnostics

This should go beyond deployment health.

One command/page could inspect:

- missing event dates;
- contradictory deadlines;
- no published rules;
- no registration path;
- prize without selection method;
- award with no eligible projects;
- judge capacity shortage;
- disconnected assignment graph;
- judge conflicts unresolved;
- unpublished rubric;
- required submission field not exposed;
- broken public links/media;
- page block with inaccessible contrast;
- venue rooms over capacity;
- checked-in attendees without necessary consent;
- scheduled announcement with empty audience;
- webhook failures;
- backup too old;
- stale sponsor resource;
- results publication approval incomplete.

**Why include:** This is the useful version of “verification depth”: it catches actual event failures.

## 117. What-if simulator for event operations

A generalized “what if?” surface can reuse existing planning primitives.

Useful questions:

- What if submissions are 30% higher than expected?
- What if 4 judges cancel?
- What if registration capacity changes from 500 to 600?
- What if judging shrinks from 180 to 120 minutes?
- What if we move the deadline by 30 minutes?
- What if a sponsor challenge requires a new artifact?
- What if one room becomes unavailable?
- What if a track has twice the expected projects?
- What if we prohibit projects from winning more than one sponsor award?

The output should show:

- affected people/projects;
- infeasible constraints;
- extra staffing/capacity;
- changed communication audience;
- expected judging workload;
- resulting award/eligibility changes where deterministic.

**Why include:** Conflux already has the underlying models; this makes them decision support rather than configuration machinery.

## 118. Saved operational playbooks

For recurring organizers, capture proven procedures without building a generic workflow engine.

Examples:

- “open registration”;
- “one week before event”;
- “doors open”;
- “submission deadline”;
- “start judging”;
- “judge no-show”;
- “publish winners”;
- “event closeout.”

A playbook can include:

- checklist tasks;
- links to Conflux actions/views;
- draft communications;
- required approvals;
- responsible roles;
- expected evidence.

**Why include:** Converts tacit organizer knowledge into reusable operating procedure.

## 119. Lightweight organizer decision log

Not every important event decision is a configuration mutation.

- ADV — organizer can create a short decision record.
- ADV — question/context, decision, reason, owner and date.
- ADV — link affected rule/config/page/incident.
- ADV — internal only by default.
- ADV — mark decision as temporary / revisit after event.
- ADV — include in event retrospective.
- DO NOT BUILD — force documentation of trivial actions.

**Why include:** Useful for multi-person organizing teams and reduces “why did we do this?” confusion.

## 120. Event retrospective and next-edition handoff

A practical closeout artifact.

- BASE — what worked / what failed / metrics.
- ADV — incidents and bottlenecks automatically linked.
- ADV — judge staffing actual vs plan.
- ADV — submission surge actual vs forecast.
- ADV — sponsor/mentor utilization.
- ADV — help-desk top categories.
- ADV — participant survey themes.
- ADV — unresolved tasks carried into next edition.
- ADV — recommended template/config updates as *drafts*, not auto-applied.
- ADV — create next-edition backlog.

**Why include:** Makes Conflux valuable between events, not just during one.

---

# Part XI — Workflow optimizations to deepen existing systems

These are generally more valuable than adding a new top-level module.

## 121. Progressive-disclosure organizer mode

Given Conflux's eventual feature depth:

- default navigation only shows enabled systems;
- setup wizard asks intent, then enables relevant modules;
- advanced controls remain under explicit “Advanced” disclosure;
- expert features can be pinned by frequent users;
- settings search jumps directly to hidden configuration;
- command palette exposes power operations without cluttering every page;
- documentation/help links are contextual.

**Outcome:** extreme capability without intimidating first-time organizers.

## 122. Context-preserving deep links

Every high-frequency organizer/judge state should be linkable:

- event;
- selected tab/view;
- filter;
- selected project/participant;
- stage;
- judging plan;
- audit event;
- saved view.

Avoid encoding volatile unsaved sensitive data in URLs.

**Outcome:** easier collaboration, support and incident response.

## 123. “Open in split view” everywhere it saves navigation

Useful examples:

- participant table → profile/application;
- project table → submission/evidence;
- judge table → workload/conflicts;
- awards table → candidate evidence;
- help desk → participant/project;
- sponsor challenge → eligible projects.

**Outcome:** operator throughput without huge screen redesigns.

## 124. Safe undo / compensate where the domain supports it

Not every change can be rolled back, but many can:

- wrong application decision before downstream action;
- wrong tag;
- accidental team assignment;
- schedule move;
- hidden project;
- notification draft;
- unpublished page edit.

Where irreversible, say so *before* execution.

**Outcome:** users move faster when small mistakes are recoverable.

## 125. Smart default views

Instead of dumping all entities:

- participants → “Needs action” first;
- projects → “Incomplete / eligibility issue / finalized” status;
- judging → “At risk / incomplete” first;
- awards → “Unresolved” first;
- mentor queue → “Unclaimed urgent” first;
- webhooks → “Failing” first.

**Outcome:** Conflux becomes an operations tool rather than a database browser.

## 126. Batch setup from CSV with mapping preview

Useful for:

- participants;
- judges;
- mentors;
- sponsors;
- tracks;
- rooms;
- inventory;
- staff.

Must have:

- mapping preview;
- validation;
- duplicate strategy;
- dry-run;
- error CSV;
- idempotent re-import strategy.

**Outcome:** migration from spreadsheets becomes frictionless.

## 127. Clone-and-edit instead of recreate

Apply consistently to:

- rubric;
- award;
- form;
- policy;
- communication;
- page;
- session;
- sponsor challenge;
- view;
- template;
- check-in list.

**Outcome:** repeated event configuration becomes much faster.

## 128. Inline validation at the point of configuration

Examples:

- impossible deadline order;
- award with no eligible scope;
- judge pool too small;
- contrast failure;
- empty communication audience;
- room capacity exceeded;
- form condition referencing nonexistent field;
- Event-as-Code unmanaged/prune hazard.

**Outcome:** errors are fixed where they are created rather than discovered at launch.

## 129. Default presets for sophisticated systems

Complexity should arrive with good presets:

- judging: weighted rubric, top-picks, pairwise, hybrid;
- assignment: balanced, expertise-aware, physical science-fair;
- admissions: open, approval, waitlist;
- event: online, hybrid, in-person;
- publication: immediate, scheduled, approval-required;
- feedback: private, anonymous release, named release;
- page: simple, sponsor-heavy, technical challenge.

**Outcome:** advanced backend features become usable by ordinary organizers.

## 130. Human-readable explanations everywhere a solver/policy decides something

Not giant proofs. Useful explanations:

- “Assigned because this judge matches AI track, has capacity, and no conflict.”
- “Project cannot enter award because challenge opt-in was not finalized.”
- “Event-as-Code apply would remove 3 unmanaged pages only with prune.”
- “Participant is blocked from check-in because required waiver v3 is incomplete.”
- “This judge route is infeasible because two assigned projects overlap the same 10-minute window.”

**Outcome:** algorithmic depth creates trust instead of opacity.

---

# Part XII — Useful features to explicitly *not* prioritize

The existence of a powerful architecture makes restraint important.

## 131. Low-value verification recursion

Avoid:

- hash of an already immutable hash merely to produce another layer;
- multiple redundant signatures over data that already has an authenticated canonical source;
- blockchain/notarization for ordinary submissions;
- cryptographic ceremony that no participant, organizer, auditor or integration consumes;
- permanent proofs for ephemeral UI state.

Add cryptographic machinery only when it enables:

- offline verification;
- portable audit;
- tamper-evident external handoff;
- signed credential/archive required by a real consumer.

## 132. Built-in generic chat

Conflux needs:

- announcements;
- inbox/direct operational messages;
- Q&A;
- mentor/help queues.

It does not need to reproduce:

- Discord;
- Slack;
- threaded community servers;
- voice/video rooms.

Integrate with those systems.

## 133. Full accounting / banking

Useful:

- event budget;
- sponsorship commitments;
- expense status;
- reimbursement request/export.

Not useful in core:

- bank connections;
- reconciliation;
- payroll;
- bookkeeping ledger;
- tax filing.

## 134. Full travel booking

Useful:

- travel instructions;
- buses/shuttles;
- reimbursement;
- external booking references.

Do not build:

- airfare search;
- hotel inventory;
- booking/payment engine.

## 135. Full recruiting ATS

Useful:

- participant opt-in;
- consented profile access;
- shortlists;
- export/integration.

Do not build:

- interview scheduling suite;
- candidate ranking model;
- employment offer workflow.

## 136. AI for deterministic tasks

Do not use LLMs for:

- calculating scores;
- enforcing deadlines;
- validating required fields;
- assigning permissions;
- applying policy;
- determining official winners.

AI can assist with:

- drafting organizer communication;
- summarizing open help-desk themes;
- translating or reformatting content;
- proposing configuration from a natural-language brief;
- helping inspect a large event through permissioned MCP.

Official state remains deterministic and reviewable.

## 137. Participant surveillance

Avoid:

- keystroke logging;
- IDE tracking;
- screen recording;
- arbitrary browser fingerprinting;
- judging “effort” from commit counts;
- covert sponsor/recruiter tracking.

Use explicit evidence and declarations.

## 138. Gamification without an event purpose

Avoid adding:

- organizer XP;
- participant streaks;
- arbitrary badges for clicking around;
- engagement scores;
- leaderboards unrelated to event goals.

Useful gamification can exist only when the event deliberately wants it, such as optional referral or mini-event mechanics.

## 139. Generic no-code workflow engine

Conflux already has stages, policies, forms, approvals, Event-as-Code and extensions.

Do not add a second free-form Zapier-like internal workflow engine unless real use cases cannot be represented by those primitives.

## 140. Feature duplication across UI/API/CLI/MCP

A command/tool is not a new feature if the domain capability already exists.

Prefer:

- one canonical service/domain operation;
- multiple interfaces over it.

Avoid:

- UI-only behavior;
- CLI-only mutation semantics;
- MCP-only shortcuts that bypass normal validation.

---

# Part XIII — Strongest second-pass additions

If the goal is to choose the additions with the best ratio of usefulness to complexity, these stand out.

## Tier A — high-value, natural Conflux extensions

1. Personalized participant “My Event” hub.
2. Judge/staff recruitment, invitation and readiness.
3. Judge capacity planner.
4. Review coverage / judging completeness evidence.
5. Judge no-show live repair.
6. Demo/pitch queue + timer.
7. Live run-of-show.
8. Volunteer shift management.
9. Organizer help desk.
10. Accessibility accommodation requests.
11. Code of Conduct / incident workflow.
12. Event closeout.
13. Event doctor/readiness diagnostics.
14. What-if simulator.
15. Rules/originality/AI-use disclosures.
16. Event change impact + notification assistant.
17. Calendar integration.
18. Recurring-edition workflow.

These either reuse existing Conflux primitives heavily or directly eliminate a high-friction hackathon workflow.

## Tier B — extremely useful for in-person/student events

19. Dietary/meal planning.
20. Travel/bus/reimbursement workflow.
21. Hardware checkout.
22. Swag inventory/distribution.
23. Badge/signage print center.
24. Minor/guardian consent state.
25. Venue readiness checklist.
26. Emergency operations.
27. Speaker/workshop management.

These should be modular so an online event never sees them.

## Tier C — valuable for mature sponsors/programs

28. Sponsor deliverable tracker.
29. Sponsor ROI report.
30. Participant recruiting opt-in.
31. Participant/staff/sponsor surveys.
32. Lightweight event budget.
33. Participation certificates/credentials.
34. Marketing attribution/referral.
35. Retrospective + next-edition handoff.

These improve recurring-program economics and professionalism but should not dominate the core competition UI.

---

# Part XIV — Revised strategic interpretation

After the second pass, the strongest possible Conflux is broader than “advanced hackathon judging software” but narrower than “generic event ERP.”

A useful boundary is:

> **Conflux should own workflows whose meaning depends on hackathon state.**

Examples:

- travel reimbursement is worth owning when eligibility depends on event attendance and attendee status;
- meal distribution is worth owning when it uses check-in and dietary state;
- volunteer shifts are worth owning when they operate event desks, judging rooms and mentorship;
- sponsor ROI is worth owning when it comes from challenge participation, projects, workshops and awards;
- certificates are worth owning when eligibility comes from attendance/submission/role state;
- recruiting opt-in is worth owning when it connects participants/projects to sponsor relationships;
- run-of-show is worth owning when milestones are submission deadlines, judging, results and event operations.

By contrast, Conflux should generally **integrate rather than own** generic domains such as payroll, airline booking, accounting, Slack-style chat, ATS pipelines and payment processing.

That boundary produces a product that can become exceptionally deep without becoming incoherent.

---

# Research basis for this pass

The following current sources materially informed the pass:

- MLH Hackathon Organizer Guide — operational coverage including registration, food/dietary needs, travel, hardware, emergency planning, judging, scheduling, mentorship, help desk and after-event work:
  https://github.com/MLH/mlh-hackathon-organizer-guide
- MLH Judging Plan — science-fair judging, judge-capacity planning, judging debrief and help path:
  https://github.com/MLH/mlh-hackathon-organizer-guide/blob/master/general-information/judging-and-submissions/judging-plan.md
- MLH Community Values — Code of Conduct, incident reporting, minors/safeguarding, food and event safety expectations:
  https://github.com/MLH/mlh-hackathon-organizer-guide/blob/master/overview/mlh-community-values.md
- MLH Registration guidance — dietary and participant fields:
  https://github.com/MLH/mlh-hackathon-organizer-guide/blob/master/general-information/managing-registrations/registrations.md
- MLH Rules guidance — prior work, crossposting, code/framework and AI-use disclosure:
  https://github.com/MLH/mlh-hackathon-organizer-guide/blob/master/general-information/judging-and-submissions/rules-for-your-hackathon.md
- MLH software guide — existing hackathon tools historically cover buses, travel reimbursement, mentorship queues and expo/judging:
  https://github.com/MLH/mlh-hackathon-organizer-guide/blob/master/organizer-resources/software-for-hackathons.md
- HackHQ 2026 updates/features — judging rooms, top-picks voting, custom assignments, announcements, CSV participant import and submission/video workflows:
  https://hackhq.io/updates
  https://hackhq.io/features
- TAIKAI — current platform emphasis on team matching, event timeline, internal communication, livestreaming and MCP:
  https://taikai.network/
- Devpost for Teams — organizer reporting, team formation, judging, external guests and enterprise access controls:
  https://info.devpost.com/product/devpost-for-teams
- BuilderBase — sponsor onboarding/ROI, live ops, recruiting and repeat-program positioning:
  https://builderbase.com/
- Recent participant discussion about opaque judging and missing review/feedback evidence:
  https://www.reddit.com/r/Devvit/comments/1vrvai6/everything_wrong_with_the_reddit_games_hackathons/

