import { expect, test } from "@playwright/test";
import { account, PASSWORD, signIn, settled } from "./support";

// Real routes and stable deep links (PD-B04-T01): direct loads through the gateway, refresh,
// history, compatibility redirects for the pre-router query-string URLs, and role boundaries.
test.skip(
  ({ isMobile }) => isMobile,
  "history/URL contract; viewport independent",
);

const current = (page: import("@playwright/test").Page) =>
  page.locator('#workspace-navigation a[aria-current="page"]');

async function workspaceOf(page: import("@playwright/test").Page) {
  const me = await (await page.request.get("/api/v1/accounts/me/")).json();
  return me.memberships[0].workspace as string;
}

test("a deep link opens a workspace view directly and survives refresh", async ({
  page,
}) => {
  await signIn(page, "judge-01");
  const workspace = await workspaceOf(page);
  await page.goto(`/app/w/${workspace}/queue`); // hard load: the gateway must serve the shell for nested paths
  await expect(current(page)).toHaveText("Review queue");
  await page.reload();
  await expect(current(page)).toHaveText("Review queue");
  expect(new URL(page.url()).pathname).toBe(`/app/w/${workspace}/queue`);
});

test("browser back and forward move between workspace views", async ({
  page,
}) => {
  await signIn(page, "judge-01");
  const workspace = await workspaceOf(page);
  await page.goto(`/app/w/${workspace}/overview`);
  await expect(current(page)).toHaveText("Overview");
  await page.locator('#workspace-navigation a[href$="/queue"]').click();
  await expect(current(page)).toHaveText("Review queue");
  await page.locator('#workspace-navigation a[href$="/schedule"]').click();
  await expect(current(page)).toHaveText("Schedule & route");
  await page.goBack();
  await expect(current(page)).toHaveText("Review queue");
  await page.goBack();
  await expect(current(page)).toHaveText("Overview");
  await page.goForward();
  await expect(current(page)).toHaveText("Review queue");
  expect(new URL(page.url()).pathname).toBe(`/app/w/${workspace}/queue`);
});

test("legacy query-string URLs redirect to their routes without a history entry", async ({
  page,
}) => {
  await signIn(page, "judge-01");
  const workspace = await workspaceOf(page);
  const me = await (await page.request.get("/api/v1/accounts/me/")).json();
  await page.goto("/app/w/x/overview"); // a known starting entry
  const before = await page.evaluate(() => history.length);
  await page.goto(`/app/?workspace=${workspace}&view=queue`);
  await expect(page).toHaveURL(new RegExp(`/app/w/${workspace}/queue$`));
  await expect(current(page)).toHaveText("Review queue");
  expect(await page.evaluate(() => history.length)).toBe(before + 1); // the goto itself, no extra redirect entry
  await page.goto(`/?workspace=${workspace}`); // the gateway's own root redirect, then the SPA's
  await expect(page).toHaveURL(new RegExp(`/app/w/${workspace}/overview$`));
  await page.goto(`/app/?person=${me.public_id}`); // profile_url emitted by the API
  await expect(page).toHaveURL(new RegExp(`/app/person/${me.public_id}$`));
  await expect(page.getByRole("heading", { name: "Profile" })).toBeVisible();
  await page.goto("/app/?api=explorer");
  await expect(page).toHaveURL(/\/app\/api-explorer$/);
});

test("a view the role does not have is replaced by the overview", async ({
  page,
}) => {
  await signIn(page, "participant-01");
  const workspace = await workspaceOf(page);
  await page.goto(`/app/w/${workspace}/setup`); // an organizer destination
  await expect(page).toHaveURL(new RegExp(`/app/w/${workspace}/overview$`));
  await expect(current(page)).toHaveText("Overview");
  await settled(page);
  await expect(page.getByText("Operator console")).toHaveCount(0);
});

test("a workspace the account does not belong to is denied, unknown pages are not found", async ({
  page,
}) => {
  await signIn(page, "judge-01");
  await page.goto("/app/w/00000000-0000-0000-0000-000000000000/overview");
  await expect(
    page.getByText("You are not a member of this workspace."),
  ).toBeVisible();
  await page.goto("/app/definitely/not/a/page");
  await expect(page.getByText("That page does not exist.")).toBeVisible();
  await expect(
    page.getByRole("link", { name: "Back to workspaces" }),
  ).toHaveAttribute("href", /^\/app\/?$/);
});

test("signed out, a deep link asks for sign-in and lands on the same URL afterwards", async ({
  page,
  browser,
}) => {
  await signIn(page, "organizer");
  const workspace = await workspaceOf(page);
  const fresh = await (await browser.newContext()).newPage();
  await fresh.goto(`/app/w/${workspace}/communications`);
  await expect(fresh.getByLabel("Username")).toBeVisible();
  await fresh.getByLabel("Username").fill(account("organizer"));
  await fresh.getByLabel("Password").fill(PASSWORD);
  await fresh.getByRole("button", { name: "Sign in" }).click();
  await expect(
    fresh.locator('#workspace-navigation a[aria-current="page"]'),
  ).toHaveText("Communications");
  expect(new URL(fresh.url()).pathname).toBe(
    `/app/w/${workspace}/communications`,
  );
  await fresh.context().close();
});

test("selecting a workspace and going back to workspaces is a real history round trip", async ({
  page,
}) => {
  await signIn(page, "judge-01");
  await page
    .locator('nav[aria-label="Your workspaces"] button')
    .first()
    .click();
  await expect(page).toHaveURL(/\/app\/w\/[^/]+\/overview$/);
  await page.getByRole("button", { name: "Back to workspaces" }).click();
  await expect(page).toHaveURL(/\/app\/?$/);
  await page.goBack();
  await expect(page).toHaveURL(/\/app\/w\/[^/]+\/overview$/);
  await page.goForward();
  await expect(page).toHaveURL(/\/app\/?$/);
  await expect(
    page.getByRole("navigation", { name: "Your workspaces" }),
  ).toBeVisible();
});
