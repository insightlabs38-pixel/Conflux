import AxeBuilder from "@axe-core/playwright";
import { expect, type Page } from "@playwright/test";

export const SEED = process.env.E2E_DEMO_SEED ?? "7";
export const PASSWORD = process.env.E2E_DEMO_PASSWORD ?? "demo-pass-7";
export const account = (label: string) => `demo-hackathon-${SEED}-${label}`;

/** Collects browser-side problems so a test can assert there were none. */
export function watch(page: Page) {
  const problems: string[] = [];
  page.on(
    "console",
    (m) =>
      m.type() === "error" &&
      problems.push(`console: ${m.text().slice(0, 200)}`),
  );
  page.on("pageerror", (e) =>
    problems.push(`pageerror: ${e.message.slice(0, 200)}`),
  );
  page.on("response", (r) => {
    if (r.status() >= 400)
      problems.push(`http ${r.status()}: ${new URL(r.url()).pathname}`);
  });
  return problems;
}

export async function signIn(page: Page, label: string) {
  await page.goto("/app/");
  await page.getByLabel("Username").fill(account(label));
  await page.getByLabel("Password").fill(PASSWORD);
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(
    page.getByRole("navigation", { name: "Your workspaces" }),
  ).toBeVisible();
}

export async function openWorkspace(page: Page) {
  await page
    .getByRole("navigation", { name: "Your workspaces" })
    .getByRole("button")
    .first()
    .click();
}

export async function noHorizontalOverflow(page: Page) {
  const overflow = await page.evaluate(
    () =>
      document.documentElement.scrollWidth -
      document.documentElement.clientWidth,
  );
  expect(overflow, "horizontal overflow (px)").toBeLessThanOrEqual(0);
}

export async function accessible(page: Page) {
  const { violations } = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();
  expect(
    violations.map((v) => `${v.id}: ${v.nodes.length} node(s) — ${v.help}`),
    "axe violations",
  ).toEqual([]);
}

export async function eventIds(page: Page) {
  const me = await (await page.request.get("/api/v1/accounts/me/")).json();
  const workspace = me.memberships[0].workspace as string;
  const events = await (
    await page.request.get(`/api/v1/workspaces/${workspace}/events/`)
  ).json();
  return { workspace, event: events[0].public_id as string };
}

/** Waits until every loading indicator has resolved into content or an error. */
export async function settled(page: Page) {
  await page.waitForLoadState("networkidle");
  await expect(page.getByText(/^(Loading|Checking) .*(…|\.\.\.)$/)).toHaveCount(
    0,
  );
}
