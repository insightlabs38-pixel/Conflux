import fs from "node:fs";
import path from "node:path";
import {
  request as pwRequest,
  test as base,
  type Browser,
  type BrowserContext,
  type Page,
} from "@playwright/test";
import { account, PASSWORD, SEED, type Who } from "./support";

/**
 * Reusable authenticated storage states by role (PD-B03-T03; contract in docs/operations/E2E.md).
 *
 * One API sign-in per (scenario, role) produces a Playwright storage state that specs reuse
 * instead of driving the sign-in form. States are cached under artifacts/auth/<seed>/<label>.json
 * and revalidated against /accounts/me/ before every reuse, so a revoked/expired session is
 * transparently re-issued. Sign-in, sign-out and authorization specs must NOT use them: they
 * exercise the real form, and signing out revokes the server-side session behind a state.
 */
const DIR = path.resolve(__dirname, "../../artifacts/e2e-auth");
const MARGIN_MS = 5 * 60_000;

export const stats = { logins: 0, reuses: 0 };

const baseURL = () => process.env.E2E_BASE_URL ?? "http://localhost:8080";
const reference = (): Who => ({ seed: SEED, password: PASSWORD });

async function valid(file: string, username: string): Promise<boolean> {
  let state: { cookies: { expires: number }[] };
  try {
    state = JSON.parse(fs.readFileSync(file, "utf8"));
  } catch {
    return false;
  }
  const soon = Date.now() / 1000 + MARGIN_MS / 1000;
  if (
    !state.cookies.length ||
    state.cookies.some((c) => c.expires > 0 && c.expires < soon)
  )
    return false;
  const api = await pwRequest.newContext({
    baseURL: baseURL(),
    storageState: file,
  });
  try {
    const me = await api.get("/api/v1/accounts/me/");
    return me.ok() && (await me.json()).username === username;
  } finally {
    await api.dispose();
  }
}

/** Path of a valid storage state for `label` in `who`'s scenario, signing in only when needed. */
export async function authState(
  label: string,
  who: Who = reference(),
): Promise<string> {
  const username = account(label, who.seed);
  const file = path.join(DIR, String(who.seed), `${label}.json`);
  if (await valid(file, username)) {
    stats.reuses++;
    return file;
  }
  const api = await pwRequest.newContext({ baseURL: baseURL() });
  try {
    const login = await api.post("/api/v1/accounts/login/", {
      data: { username, password: who.password },
    });
    if (!login.ok())
      throw new Error(
        `storage state for ${username}: sign-in failed (HTTP ${login.status()}); ` +
          `is the scenario seeded (scripts/demo-reset) and E2E_DEMO_PASSWORD correct?`,
      );
    stats.logins++;
    fs.mkdirSync(path.dirname(file), { recursive: true });
    const tmp = `${file}.${process.pid}.${Date.now()}.tmp`;
    await api.storageState({ path: tmp });
    fs.renameSync(tmp, file); // atomic: concurrent workers never read a partial file
    return file;
  } finally {
    await api.dispose();
  }
}

export type As = {
  /** A page signed in as `label` in this test's own context (replaces any earlier identity). */
  (label: string): Promise<Page>;
  /** A page in a separate context, for tests that need two identities at once. */
  other(label: string): Promise<Page>;
};

function makeAs(
  who: () => Who,
  browser: Browser,
  context: BrowserContext,
  opened: BrowserContext[],
  viewport: { width: number; height: number } | null | undefined,
): As {
  const as = (async (label: string) => {
    const state = JSON.parse(
      fs.readFileSync(await authState(label, who()), "utf8"),
    );
    await context.clearCookies();
    await context.addCookies(state.cookies);
    return context.newPage();
  }) as As;
  as.other = async (label: string) => {
    const created = await browser.newContext({
      baseURL: baseURL(),
      storageState: await authState(label, who()),
      locale: "en-US",
      timezoneId: "UTC",
      reducedMotion: "reduce",
      viewport: viewport ?? undefined,
    });
    opened.push(created);
    return created.newPage();
  };
  return as;
}

/** `test` whose `as(label)` uses storage states of the shared reference scenario (seed 7). */
export const referenceTest = base.extend<{ as: As }>({
  as: async ({ browser, context, page }, use) => {
    const opened: BrowserContext[] = [];
    await use(makeAs(reference, browser, context, opened, page.viewportSize()));
    await Promise.all(opened.map((c) => c.close()));
  },
});

/** Used by isolatedTest: `as` bound to a fixture's scenario. */
export const asFor =
  (fixture: Who) =>
  async (
    {
      browser,
      context,
      page,
    }: { browser: Browser; context: BrowserContext; page: Page },
    use: (as: As) => Promise<void>,
  ) => {
    const opened: BrowserContext[] = [];
    await use(
      makeAs(() => fixture, browser, context, opened, page.viewportSize()),
    );
    await Promise.all(opened.map((c) => c.close()));
  };
