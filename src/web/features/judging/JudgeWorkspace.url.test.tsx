// @vitest-environment happy-dom
import { act } from "react";
import { createRoot } from "react-dom/client";
import { useLocation } from "react-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { JudgeWorkspace } from "./JudgeWorkspace";
import { withRouter } from "../../lib/test-router";
import { jsonResponse } from "../../lib/test-http";

(
  globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }
).IS_REACT_ACT_ENVIRONMENT = true;

let container: HTMLDivElement;
let root: ReturnType<typeof createRoot>;
let search = "";
function Where() {
  search = useLocation().search;
  return null;
}

beforeEach(() => {
  container = document.createElement("div");
  document.body.appendChild(container);
  root = createRoot(container);
  search = "";
});
afterEach(() => {
  act(() => root.unmount());
  container.remove();
  vi.unstubAllGlobals();
});

async function waitFor(check: () => boolean) {
  for (let attempt = 0; attempt < 400; attempt++) {
    if (check()) return;
    await act(async () => new Promise((resolve) => setTimeout(resolve, 5)));
  }
  throw new Error("Judge workspace did not update");
}

function stubApi(plans = [{ public_id: "p1", name: "Final review" }]) {
  const fetchMock = vi.fn(async (input: unknown) => {
    const url = String(input);
    const body = url.endsWith("judge-events/")
      ? [
          { public_id: "e1", name: "First" },
          { public_id: "e2", name: "Second" },
        ]
      : url.endsWith("judge-calendar/")
        ? { windows: [], assignments: [] }
        : url.endsWith("/e1/stages/")
          ? [{ public_id: "s1", name: "Final" }]
          : url.endsWith("/s1/evaluation-plans/")
            ? plans
            : url.endsWith("candidates/")
              ? [
                  {
                    project: "pr",
                    name: "Deep-linked project",
                    status: "pending",
                  },
                ]
              : url.endsWith("publish-rubric/")
                ? { number: 1, criteria: [] }
                : [];
    return jsonResponse(200, body);
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

const mount = (url: string) =>
  act(() =>
    root.render(
      withRouter(
        <>
          <Where />
          <JudgeWorkspace workspaceId="w" />
        </>,
        url,
      ),
    ),
  );

describe("judge workspace URL state", () => {
  it("reopens the review queue from a deep link without any interaction", async () => {
    stubApi();
    mount("/w/w/queue?event=e1&stage=s1&plan=p1");
    await waitFor(
      () => container.textContent?.includes("Deep-linked project") ?? false,
    );
    const selects = [...container.querySelectorAll("select")];
    // A single plan needs no selector of its own.
    expect(selects.map((select) => select.value)).toEqual(["e1", "s1"]);
    expect(search).toBe("?event=e1&stage=s1&plan=p1");
  });

  it("writes the choice to the URL and clears the levels below it", async () => {
    stubApi();
    mount("/w/w/queue?event=e1&stage=s1&plan=p1");
    await waitFor(
      () => container.textContent?.includes("Deep-linked project") ?? false,
    );
    await act(async () => {
      const select = container.querySelector("select")!;
      select.value = "e2";
      select.dispatchEvent(new Event("change", { bubbles: true }));
    });
    expect(search).toBe("?event=e2");
    expect(container.textContent).not.toContain("Deep-linked project");
  });

  it("selects the only plan by itself and records it with a replace", async () => {
    stubApi();
    mount("/w/w/queue?event=e1&stage=s1");
    await waitFor(() => search === "?event=e1&stage=s1&plan=p1");
  });

  it("treats an event the judge is not on as no selection", async () => {
    const fetchMock = stubApi();
    mount("/w/w/queue?event=nope&stage=s1&plan=p1");
    await waitFor(() => search === "");
    expect(
      fetchMock.mock.calls.some(([url]) => String(url).includes("/nope/")),
    ).toBe(false);
    expect(container.querySelector("select")?.value).toBe("");
  });

  it("drops a stage that does not belong to the event, keeping the event", async () => {
    stubApi();
    mount("/w/w/queue?event=e1&stage=other&plan=p1");
    await waitFor(() => search === "?event=e1");
  });
});
