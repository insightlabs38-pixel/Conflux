import { describe, expect, it } from "vitest";
import { resolveOperation } from "./api";
import { approvalsUrl, gatesUrl } from "./approvals";
import { bulkUrl } from "./bulk";
import { artifactUrl, jobUrl, jobsUrl } from "./jobs";
import { threadUrl, type Subject } from "./threads";
import { timelineUrl } from "./timeline";

// Every request the shared-primitive clients make must be an operation the checked OpenAPI
// contract documents (PD-F002-B01-T91), so the web goes through the generated client and cannot
// drift from the API.
const W = "00000000-0000-4000-8000-000000000001";
const E = "00000000-0000-4000-8000-000000000002";
const ID = "00000000-0000-4000-8000-000000000003";
const path = (url: string) => url.split("?")[0];
const subject: Subject = {
  workspaceId: W,
  eventId: E,
  type: "project",
  id: ID,
  audience: "organizers",
};

const REQUESTS: [string, string][] = [
  ["GET", jobsUrl(W)],
  ["GET", jobUrl(W, ID)],
  ["POST", `${jobUrl(W, ID)}cancel/`],
  ["GET", artifactUrl(W, ID, "archive.json")],
  ["POST", `/api/v1/workspaces/${W}/events/${E}/archive/export-jobs/`],
  ["GET", approvalsUrl(W, E)],
  ["GET", `${approvalsUrl(W, E)}${ID}/`],
  ["POST", `${approvalsUrl(W, E)}${ID}/decision/`],
  ["POST", `${approvalsUrl(W, E)}${ID}/cancel/`],
  ["GET", gatesUrl(W, E)],
  ["PUT", `${gatesUrl(W, E)}message_send/`],
  ["GET", threadUrl(subject)],
  ["POST", threadUrl(subject)],
  ["PATCH", `/api/v1/workspaces/${W}/events/${E}/thread-comments/${ID}/`],
  ["DELETE", `/api/v1/workspaces/${W}/events/${E}/thread-comments/${ID}/`],
  ["GET", timelineUrl(W, E, { from: "2027-03-06T00:00:00Z", limit: 5 })],
  ["POST", bulkUrl(W, E)],
  ["GET", `${bulkUrl(W, E)}receipts/`],
];

describe("shared-primitive clients and the OpenAPI contract", () => {
  it.each(REQUESTS)("%s %s is a documented operation", (method, url) => {
    expect(resolveOperation(method, path(url))).not.toBeNull();
  });
});
