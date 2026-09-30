// @vitest-environment happy-dom
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import {
  QueryClientProvider,
  useMutation,
  useQuery,
  type QueryClient,
} from "@tanstack/react-query";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { apiRequest } from "../lib/api";
import { jsonResponse } from "../lib/test-http";
import { createQueryClient, optimistic, queryKeys } from "../lib/query";
import { useMe, useSignOut } from "./useMe";

(
  globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }
).IS_REACT_ACT_ENVIRONMENT = true;

let container: HTMLDivElement;
let root: Root;
beforeEach(() => {
  container = document.createElement("div");
  document.body.appendChild(container);
  root = createRoot(container);
});
afterEach(() => {
  act(() => root.unmount());
  container.remove();
  vi.unstubAllGlobals();
});

async function until(check: () => boolean, ms = 1500) {
  const start = Date.now();
  while (!check()) {
    if (Date.now() - start > ms) throw new Error("until timed out");
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 5));
    });
  }
}
const response = jsonResponse;
const ME = {
  username: "ada",
  memberships: [{ workspace: "w1", role: "judge" }],
};

function Who({ label }: { label: string }) {
  const me = useMe();
  return (
    <p data-testid={label}>
      {me.isPending
        ? "loading"
        : me.isError
          ? `error:${me.error.message}`
          : me.data === null
            ? "signed-out"
            : me.data.username}
    </p>
  );
}
const text = (id: string) =>
  container.querySelector(`[data-testid="${id}"]`)?.textContent;
function mount(client: QueryClient, children: React.ReactNode) {
  act(() =>
    root.render(
      <QueryClientProvider client={client}>{children}</QueryClientProvider>,
    ),
  );
}

describe("server-state layer", () => {
  it("deduplicates concurrent requests and serves later mounts from cache", async () => {
    const fetchMock = vi.fn().mockImplementation(async () => response(200, ME));
    vi.stubGlobal("fetch", fetchMock);
    const client = createQueryClient({ retry: false });
    mount(
      client,
      <>
        <Who label="a" />
        <Who label="b" />
      </>,
    );
    await until(() => text("a") === "ada" && text("b") === "ada");
    expect(fetchMock).toHaveBeenCalledTimes(1);
    // A screen mounted later (e.g. after navigating) reads the cache without a request.
    mount(
      client,
      <>
        <Who label="a" />
        <Who label="b" />
        <Who label="c" />
      </>,
    );
    await until(() => text("c") === "ada");
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("maps 401/403 to signed-out without retrying, and surfaces other errors", async () => {
    const fetchMock = vi.fn().mockImplementation(async () => response(401, {}));
    vi.stubGlobal("fetch", fetchMock);
    mount(createQueryClient(), <Who label="a" />);
    await until(() => text("a") === "signed-out");
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("does not retry a 404 but retries transient server errors with backoff until they clear", async () => {
    const notFound = vi
      .fn()
      .mockImplementation(async () => response(404, { detail: "Gone." }));
    vi.stubGlobal("fetch", notFound);
    mount(createQueryClient({ retryDelay: 1 }), <Who label="a" />);
    await until(() => text("a")?.startsWith("error:") ?? false);
    expect(notFound).toHaveBeenCalledTimes(1);

    act(() => root.unmount());
    root = createRoot(container);
    const flaky = vi
      .fn()
      .mockImplementationOnce(async () => response(503, {}))
      .mockImplementationOnce(async () => response(500, {}))
      .mockImplementation(async () => response(200, ME));
    vi.stubGlobal("fetch", flaky);
    mount(createQueryClient({ retryDelay: 1 }), <Who label="a" />);
    await until(() => text("a") === "ada");
    expect(flaky).toHaveBeenCalledTimes(3);

    act(() => root.unmount());
    root = createRoot(container);
    const down = vi.fn().mockImplementation(async () => response(503, {}));
    vi.stubGlobal("fetch", down);
    mount(createQueryClient({ retryDelay: 1 }), <Who label="a" />);
    await until(() => text("a")?.startsWith("error:") ?? false);
    expect(down).toHaveBeenCalledTimes(3); // the first attempt plus two retries, then it gives up
  });

  it("refetches on invalidation", async () => {
    const fetchMock = vi
      .fn()
      .mockImplementationOnce(async () => response(200, ME))
      .mockImplementation(async () =>
        response(200, { ...ME, username: "grace" }),
      );
    vi.stubGlobal("fetch", fetchMock);
    const client = createQueryClient({ retry: false });
    mount(client, <Who label="a" />);
    await until(() => text("a") === "ada");
    await act(async () => {
      await client.invalidateQueries({ queryKey: queryKeys.me });
    });
    await until(() => text("a") === "grace");
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it("cancels an in-flight request when its last observer unmounts", async () => {
    let signal: AbortSignal | undefined;
    vi.stubGlobal(
      "fetch",
      vi.fn((_path: string, init?: RequestInit) => {
        signal = init?.signal ?? undefined;
        return new Promise(() => {});
      }),
    );
    mount(createQueryClient({ retry: false }), <Who label="a" />);
    await act(async () => undefined);
    expect(signal?.aborted).toBe(false);
    act(() => root.unmount());
    root = createRoot(container);
    expect(signal?.aborted).toBe(true);
  });

  it("signing out resets every cached query so the next account never sees old data", async () => {
    const fetchMock = vi
      .fn()
      .mockImplementation(async (path: string) =>
        path.includes("logout")
          ? response(204)
          : path.includes("/accounts/me/")
            ? response(401, {})
            : response(200, []),
      );
    vi.stubGlobal("fetch", fetchMock);
    const client = createQueryClient({ retry: false });
    client.setQueryData(queryKeys.me, ME);
    client.setQueryData(queryKeys.participantEvents("w1"), [
      { public_id: "e1" },
    ]);
    function Out() {
      const out = useSignOut();
      return <button onClick={() => out.mutate()}>out</button>;
    }
    mount(client, <Out />);
    await act(async () => container.querySelector("button")!.click());
    await until(
      () =>
        client.getQueryData(queryKeys.participantEvents("w1")) === undefined,
    );
    expect(client.getQueryData(queryKeys.me)).not.toEqual(ME);
    expect(
      fetchMock.mock.calls.some(([path]) => String(path).includes("logout")),
    ).toBe(true);
  });

  it("applies optimistic updates at once, rolls back on failure and revalidates on settle", async () => {
    const client = createQueryClient({ retry: false });
    const key = ["items"] as const;
    const server = { items: ["a"], failNext: false };
    let release!: () => void;
    let gate = new Promise<void>((resolve) => (release = resolve));
    vi.stubGlobal(
      "fetch",
      vi.fn(async (_path: string, init?: RequestInit) => {
        if (init?.method === "POST") {
          await gate; // the server answers only when the test lets it
          if (server.failNext) return response(500, { detail: "nope" });
          server.items = [...server.items, JSON.parse(String(init.body)).name];
          return response(201, {});
        }
        return response(200, server.items);
      }),
    );
    let add!: (name: string) => Promise<unknown>;
    function List() {
      const items = useQuery({
        queryKey: key,
        queryFn: () => apiRequest<string[]>("/items"),
      });
      const mutation = useMutation({
        mutationFn: (name: string) =>
          apiRequest("/items", { method: "POST", body: { name } }),
        ...optimistic<string[], string>(client, key, (current, name) => [
          ...(current ?? []),
          name,
        ]),
      });
      add = (name) => mutation.mutateAsync(name).catch(() => undefined);
      return <p data-testid="list">{(items.data ?? []).join(",")}</p>;
    }
    mount(client, <List />);
    await until(() => text("list") === "a");

    let pending!: Promise<unknown>;
    await act(async () => {
      pending = add("b");
    });
    await until(() => text("list") === "a,b"); // visible while the server has not answered
    expect(server.items).toEqual(["a"]);
    await act(async () => {
      release();
      await pending;
    });
    await until(() => text("list") === "a,b");
    expect(server.items).toEqual(["a", "b"]); // and confirmed by the revalidation

    server.failNext = true;
    gate = new Promise<void>((resolve) => (release = resolve));
    await act(async () => {
      pending = add("c");
    });
    await until(() => text("list") === "a,b,c");
    await act(async () => {
      release();
      await pending;
    });
    await until(() => text("list") === "a,b"); // rolled back, then revalidated
    expect(server.items).toEqual(["a", "b"]);
  });
});
