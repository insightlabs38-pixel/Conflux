import { apiJson } from "./api";

/**
 * The client half of the approval gate (PD-F002-B01-T06). A gated operation answers 409
 * `approval_required` with the pending request; another person decides it here; the original
 * operation is then repeated and consumes the approval. The server owns every rule (who may decide,
 * expiry, single use); this carries requests and states what is allowed.
 */
export type ApprovalStatus =
  "pending" | "approved" | "rejected" | "cancelled" | "expired" | "executed";

export type Approval = {
  public_id: string;
  action: string;
  label: string;
  subject: { type: string; id: string } | null;
  summary: string[];
  status: ApprovalStatus;
  requested_by: string;
  required_approvals: number;
  approvals: number;
  decisions: {
    actor: string;
    decision: "approve" | "reject";
    note: string;
    at: string;
  }[];
  expires_at: string;
  created_at: string;
  executed_at: string | null;
  can_decide: boolean;
  can_cancel: boolean;
};

export type Gate = {
  action: string;
  label: string;
  description: string;
  deciders: string[];
  min_approvals: number;
  enabled: boolean;
};

const eventBase = (workspaceId: string, eventId: string) =>
  `/api/v1/workspaces/${workspaceId}/events/${eventId}/`;
export const approvalsUrl = (workspaceId: string, eventId: string) =>
  `${eventBase(workspaceId, eventId)}approvals/`;
export const gatesUrl = (workspaceId: string, eventId: string) =>
  `${eventBase(workspaceId, eventId)}approval-gates/`;

export const decideApproval = (
  workspaceId: string,
  eventId: string,
  id: string,
  decision: "approve" | "reject",
  note: string,
) =>
  apiJson<Approval>(
    `${approvalsUrl(workspaceId, eventId)}${id}/decision/`,
    "POST",
    { decision, note },
  );

export const cancelApproval = (
  workspaceId: string,
  eventId: string,
  id: string,
) =>
  apiJson<Approval>(
    `${approvalsUrl(workspaceId, eventId)}${id}/cancel/`,
    "POST",
  );

export const setGate = (
  workspaceId: string,
  eventId: string,
  action: string,
  enabled: boolean,
) =>
  apiJson<Gate>(`${gatesUrl(workspaceId, eventId)}${action}/`, "PUT", {
    enabled,
  });

const WORDS: Record<ApprovalStatus, string> = {
  pending: "Waiting for approval",
  approved: "Approved, not used yet",
  rejected: "Rejected",
  cancelled: "Withdrawn",
  expired: "Expired",
  executed: "Approved and done",
};
export const statusWords = (status: ApprovalStatus) => WORDS[status];
