import { expect, test } from "@playwright/test";
import { account, PASSWORD, watch } from "./support";

test("a wrong password is announced and nothing is listed", async ({
  page,
}) => {
  await page.goto("/app/");
  await page.getByLabel("Username").fill(account("organizer"));
  await page.getByLabel("Password").fill("not-the-password");
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page.getByRole("alert")).toHaveText(
    "Invalid username or password.",
  );
  await expect(page.getByLabel("Password")).toHaveValue("");
  await expect(
    page.getByRole("navigation", { name: "Your workspaces" }),
  ).toHaveCount(0);
});

test("signing in lists workspaces and signing out returns to the form", async ({
  page,
}) => {
  const problems = watch(page);
  await page.goto("/app/");
  await page.getByLabel("Username").fill(account("organizer"));
  await page.getByLabel("Password").fill(PASSWORD);
  await page.keyboard.press("Enter");
  const nav = page.getByRole("navigation", { name: "Your workspaces" });
  await expect(nav.getByRole("button")).toHaveCount(1);
  await page.getByRole("button", { name: "Sign out" }).click();
  await expect(page.getByLabel("Username")).toBeVisible();
  // The initial signed-out probe legitimately answers 401; nothing else may fail.
  expect(
    problems.filter(
      (p) =>
        !p.includes("401") &&
        !p.includes("403") &&
        !p.includes("Failed to load resource"),
    ),
  ).toEqual([]);
});

test("the root URL lands on the app and keeps its query", async ({ page }) => {
  const event = "00000000-0000-0000-0000-000000000000";
  // The gateway sends the legacy root URL to the app with its query intact...
  const gateway = await page.request.get(`/?event=${event}`, {
    maxRedirects: 0,
  });
  expect(gateway.status()).toBe(302);
  expect(gateway.headers().location).toMatch(
    new RegExp(`/app/\\?event=${event}$`),
  );
  // ...and the app turns that legacy URL into its canonical route (lib/routes.ts legacyTarget).
  await page.goto(`/?event=${event}`);
  await expect(page).toHaveURL(new RegExp(`/app/event/${event}$`));
});
