import { guarded } from "./Guarded";
import * as Deliberation from "./DeliberationPanel";
import * as Eligibility from "./EligibilityPanels";
import * as Governance from "./GovernancePanels";
import * as Logistics from "./JudgingLogisticsPanels";
import * as Mentorship from "./MentorshipPanels";
import * as Onsite from "./OnsitePanels";
import * as PostEvent from "./PostEventPanels";

export const DeliberationPanel = guarded(
  Deliberation.DeliberationPanel,
  "Deliberation and finalization",
);
export const EligibilityReviewPanel = guarded(
  Eligibility.EligibilityReviewPanel,
  "Eligibility review",
);
export const ProjectEligibilityPanel = guarded(
  Eligibility.ProjectEligibilityPanel,
  "Eligibility review",
);
export const RulesPanel = guarded(Governance.RulesPanel, "Event rules");
export const PublicationGovernancePanel = guarded(
  Governance.PublicationGovernancePanel,
  "Publication approval and corrections",
);
export const ExceptionRequestsPanel = guarded(
  Governance.ExceptionRequestsPanel,
  "Deadline exception requests",
);
export const ProjectExceptionPanel = guarded(
  Governance.ProjectExceptionPanel,
  "Deadline exception",
);
export const SubmissionReceipt = guarded(
  Governance.SubmissionReceipt,
  "Submission receipt",
);
export const JudgeAssignmentsPanel = guarded(
  Logistics.JudgeAssignmentsPanel,
  "Your assignments",
);
export const JudgeRoutePanel = guarded(
  Logistics.JudgeRoutePanel,
  "Your judging route",
);
export const OrganizerJudgingLogisticsPanel = guarded(
  Logistics.OrganizerJudgingLogisticsPanel,
  "Judging logistics",
);
export const ArtifactInspector = guarded(
  Logistics.ArtifactInspector,
  "Submitted artifacts",
);
export const MentorDeskPanel = guarded(
  Mentorship.MentorDeskPanel,
  "Mentor desk",
);
export const ProjectMentorshipPanel = guarded(
  Mentorship.ProjectMentorshipPanel,
  "Mentorship",
);
export const OnsiteOperationsPanel = guarded(
  Onsite.OnsiteOperationsPanel,
  "On-site operations",
);
export const MyOnsitePanel = guarded(Onsite.MyOnsitePanel, "Attending");
export const PortfolioPanel = guarded(PostEvent.PortfolioPanel, "My portfolio");
export const ProjectContinuationPanel = guarded(
  PostEvent.ProjectContinuationPanel,
  "After the event",
);
export const ContinuationsAdminPanel = guarded(
  PostEvent.ContinuationsAdminPanel,
  "Post-event continuation",
);
export const ChallengesPanel = guarded(
  PostEvent.ChallengesPanel,
  "Sponsor challenges",
);
