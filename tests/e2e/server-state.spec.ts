import { expect, test } from "@playwright/test";
import { account, PASSWORD } from "./support";

// Server-state layer (PD-B04-T02) observed through the real app: shared requests and no data
// leaking between accounts in one browser session.
test.skip(
  ({ isMobile }) => isMobile,
  "data-layer contract; viewport independent",
);

async function signInForm(
  page: import("@playwright/test").Page,
  label: string,
) {
  await page.getByLabel("Username").fill(account(label));
  await page.getByLabel("Password").fill(PASSWORD);
  await page.getByRole("button", { name: "Sign in" }).click();
}

test("the account is requested once for the selector and the workspace it opens", async ({
  page,
}) => {
  const meRequests: string[] = [];
  page.on("request", (request) => {
    if (new URL(request.url()).pathname === "/api/v1/accounts/me/")
      meRequests.push(request.url());
  });
  await page.goto("/app/");
  await signInForm(page, "judge-01");
  const nav = page.getByRole("navigation", { name: "Your workspaces" });
  await expect(nav).toBeVisible();
  const afterSignIn = meRequests.length; // the signed-out probe plus the post-sign-in refetch
  await nav.getByRole("button").first().click();
  await expect(page).toHaveURL(/\/app\/w\/[^/]+\/overview$/);
  await expect(page.getByRole("region", { name: "Judging" })).toBeVisible();
  expect(meRequests.length).toBe(afterSignIn); // opening the workspace reused the cached account
});

test("signing out and in as someone else in the same session shows nothing from the first account", async ({
  page,
}) => {
  await page.goto("/app/");
  await signInForm(page, "judge-01");
  const nav = page.getByRole("navigation", { name: "Your workspaces" });
  await nav.getByRole("button").first().click();
  await expect(page.getByRole("region", { name: "Judging" })).toBeVisible();
  await expect(page.getByText(account("judge-01"))).toBeVisible();

  await page.locator(".cx-account summary").click();
  await page.getByRole("button", { name: "Sign out", exact: true }).click();
  await expect(page.getByLabel("Username")).toBeVisible(); // no reload: the SPA and its cache persist
  await expect(page.getByText(account("judge-01"))).toHaveCount(0);
  await signInForm(page, "participant-01");
  await expect(nav).toBeVisible();
  await nav.getByRole("button").first().click();
  await expect(
    page.getByRole("region", { name: "Participant events" }),
  ).toBeVisible();
  await expect(page.getByText(account("judge-01"))).toHaveCount(0);
  await expect(page.getByRole("region", { name: "Judging" })).toHaveCount(0);
  expect(
    await (await page.request.get("/api/v1/accounts/me/")).json(),
  ).toMatchObject({
    username: account("participant-01"),
  });
});

test("a server error on the account check is retried, then offered as a retry", async ({
  page,
}) => {
  let attempts = 0;
  await page.route("**/api/v1/accounts/me/", (route) => {
    attempts++;
    return route.fulfill({
      status: 503,
      contentType: "application/json",
      body: "{}",
    });
  });
  await page.goto("/app/");
  await expect(page.getByRole("alert")).toBeVisible({ timeout: 10_000 });
  expect(attempts).toBe(3); // first attempt + two backoff retries, then the error state
  await page.unroute("**/api/v1/accounts/me/");
  await page.getByRole("button", { name: "Try again" }).click();
  await expect(page.getByLabel("Username")).toBeVisible();
});
