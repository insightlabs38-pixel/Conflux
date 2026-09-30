// @vitest-environment happy-dom
import { act } from "react";
import { createRoot } from "react-dom/client";
import { useLocation, useNavigate, useNavigationType } from "react-router";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { withRouter } from "./test-router";
import { carriedSearch, useUrlParam } from "./urlState";

(
  globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }
).IS_REACT_ACT_ENVIRONMENT = true;

let container: HTMLDivElement;
let root: ReturnType<typeof createRoot>;
let api: {
  value: string;
  set: (value: string, change?: { replace?: boolean }) => void;
  back: () => void;
  go: (to: string) => void;
  path: string;
  location: string;
  type: string;
};

function Probe() {
  const [value, set] = useUrlParam("event", { clears: ["stage", "plan"] });
  const location = useLocation();
  const navigate = useNavigate();
  const type = useNavigationType();
  api = {
    value,
    set,
    back: () => void navigate(-1),
    go: (to: string) => void navigate(to),
    path: location.pathname,
    location: location.search,
    type,
  };
  return <p>{value}</p>;
}

beforeEach(() => {
  container = document.createElement("div");
  document.body.appendChild(container);
  root = createRoot(container);
});
afterEach(() => {
  act(() => root.unmount());
  container.remove();
});
const mount = (url: string) =>
  act(() => root.render(withRouter(<Probe />, url)));

describe("useUrlParam", () => {
  it("reads the param", () => {
    mount("/w/w/overview?event=e1&other=x");
    expect(api.value).toBe("e1");
  });

  it("treats a missing param as the empty default", () => {
    mount("/w/w/overview");
    expect(api.value).toBe("");
  });

  it("pushes by default so Back returns to the previous context", () => {
    mount("/w/w/overview?event=e1");
    act(() => api.set("e2"));
    expect(api.location).toBe("?event=e2");
    expect(api.type).toBe("PUSH");
    act(() => api.back());
    expect(api.location).toBe("?event=e1");
  });

  it("replaces on request so a correction adds no history entry", () => {
    mount("/w/w/overview?event=gone");
    act(() => api.set("", { replace: true }));
    expect(api.location).toBe("");
    expect(api.type).toBe("REPLACE");
  });

  it("removes the param for the default value and drops dependent params, keeping unrelated ones", () => {
    mount("/w/w/overview?event=e1&stage=s1&plan=p1&invite=tok");
    act(() => api.set("e2"));
    expect(api.location).toBe("?event=e2&invite=tok");
    act(() => api.set(""));
    expect(api.location).toBe("?invite=tok");
  });

  it("applies a late correction to where the user is now, not where the callback was created", () => {
    mount("/w/w/overview?event=e1&stage=s1");
    const stale = api.set;
    act(() => api.go("/w/w/queue?event=e1&stage=s1"));
    act(() => stale("", { replace: true }));
    expect(api.path).toBe("/w/w/queue");
    expect(api.location).toBe("");
  });

  it("builds on the URL as it is now when a navigation has been issued but not yet rendered", () => {
    mount("/w/w/overview?event=e1&stage=s1");
    act(() => {
      api.go("/w/w/queue?event=e1&stage=s1"); // the user's click
      api.set("e2", { replace: true }); // a correction decided from the previous render
      // (both run before React renders the navigation)
    });
    expect(api.path).toBe("/w/w/queue");
    expect(api.location).toBe("?event=e2"); // built on the queue URL, not the old one
  });

  it("does not navigate when the value is unchanged", () => {
    mount("/w/w/overview?event=e1");
    act(() => api.set("e1"));
    expect(api.type).toBe("POP");
  });
});

describe("carriedSearch", () => {
  it("keeps context params and drops panel state", () => {
    expect(
      carriedSearch(
        "?event=e1&stage=s1&plan=p1&invite=t&project=p&q=ada&page=2",
      ),
    ).toBe("?event=e1&stage=s1&plan=p1&invite=t");
    expect(carriedSearch("?project=p")).toBe("");
    expect(carriedSearch("")).toBe("");
  });
});
