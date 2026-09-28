// @vitest-environment happy-dom
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { SignIn } from "./SignIn";

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

async function flush() {
  await act(async () => {
    await new Promise((resolve) => setTimeout(resolve, 10));
  });
}

function type(input: HTMLInputElement, value: string) {
  const setter = Object.getOwnPropertyDescriptor(
    HTMLInputElement.prototype,
    "value",
  )!.set!;
  act(() => {
    setter.call(input, value);
    input.dispatchEvent(new Event("input", { bubbles: true }));
  });
}

function stubFetch(login: { ok: boolean; status: number }, sso?: unknown) {
  const calls: { url: string; init?: RequestInit }[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string, init?: RequestInit) => {
      calls.push({ url, init });
      if (url.includes("oidc/config"))
        return {
          ok: true,
          status: 200,
          json: async () => sso ?? { enabled: false },
        };
      return { ...login, json: async () => ({}) };
    }),
  );
  return calls;
}

function fill(username: string, password: string) {
  type(container.querySelector('input[name="username"]')!, username);
  type(container.querySelector('input[name="password"]')!, password);
}

describe("SignIn", () => {
  it("labels its fields and keeps submit disabled until both are filled", async () => {
    stubFetch({ ok: true, status: 200 });
    act(() => root.render(<SignIn onSignedIn={() => {}} />));
    await flush();
    const labels = [...container.querySelectorAll("label")].map(
      (l) => l.textContent,
    );
    expect(labels).toEqual(["Username", "Password"]);
    const submit = container.querySelector<HTMLButtonElement>(
      'button[type="submit"]',
    )!;
    expect(submit.disabled).toBe(true);
    fill("ada", "pw");
    expect(submit.disabled).toBe(false);
  });

  it("posts credentials with the cookie jar and reports success", async () => {
    const calls = stubFetch({ ok: true, status: 200 });
    const onSignedIn = vi.fn();
    act(() => root.render(<SignIn onSignedIn={onSignedIn} />));
    await flush();
    fill("ada", "s3cret");
    await act(async () => {
      container
        .querySelector("form")!
        .dispatchEvent(
          new Event("submit", { bubbles: true, cancelable: true }),
        );
    });
    await flush();
    const login = calls.find((c) => c.url.endsWith("/accounts/login/"))!;
    expect(login.init?.credentials).toBe("include");
    expect(JSON.parse(login.init!.body as string)).toEqual({
      username: "ada",
      password: "s3cret",
    });
    expect(onSignedIn).toHaveBeenCalledOnce();
  });

  it.each([
    [401, "Invalid username or password."],
    [429, "Too many failed attempts. Try again later."],
    [500, "Could not sign in. Try again."],
  ])(
    "announces a %i failure and clears the password",
    async (status, message) => {
      stubFetch({ ok: false, status });
      const onSignedIn = vi.fn();
      act(() => root.render(<SignIn onSignedIn={onSignedIn} />));
      await flush();
      fill("ada", "wrong");
      await act(async () => {
        container
          .querySelector("form")!
          .dispatchEvent(
            new Event("submit", { bubbles: true, cancelable: true }),
          );
      });
      await flush();
      expect(container.querySelector('[role="alert"]')?.textContent).toBe(
        message,
      );
      expect(
        container.querySelector<HTMLInputElement>('input[name="password"]')!
          .value,
      ).toBe("");
      expect(onSignedIn).not.toHaveBeenCalled();
    },
  );

  it("offers single sign-on only when the server enables it", async () => {
    stubFetch({ ok: true, status: 200 });
    act(() => root.render(<SignIn onSignedIn={() => {}} />));
    await flush();
    expect(container.querySelector("a")).toBeNull();
    act(() => root.unmount());
    root = createRoot(container);
    stubFetch(
      { ok: true, status: 200 },
      {
        enabled: true,
        provider_name: "Campus SSO",
        login_url: "/api/v1/accounts/oidc/login/",
      },
    );
    act(() => root.render(<SignIn onSignedIn={() => {}} />));
    await flush();
    const link = container.querySelector("a")!;
    expect(link.textContent).toBe("Sign in with Campus SSO");
    expect(link.getAttribute("href")).toContain(
      "/api/v1/accounts/oidc/login/?next=",
    );
  });
});
