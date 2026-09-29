import { chooseWorkspaceEvent } from "./support";
import { expect, test } from "@playwright/test";
import {
  accessible,
  goToDestination,
  noHorizontalOverflow,
  openWorkspace,
  settled,
  signIn,
  watch,
} from "./support";

const destinations: Record<string, string[]> = {
  organizer: [
    "overview",
    "setup",
    "participants",
    "eligibility",
    "judging",
    "results",
    "communications",
    "onsite",
    "integrations",
    "operations",
  ],
  "participant-01": [
    "overview",
    "team",
    "project",
    "resources",
    "messages",
    "profile",
  ],
  "judge-01": ["overview", "queue", "schedule", "profile", "messages"],
};
for (const width of [390, 768, 1024, 1440]) {
  for (const role of Object.keys(destinations)) {
    test(`role navigation ${role} at ${width}`, async ({ page }, info) => {
      test.skip(info.project.name !== "desktop", "explicit viewport matrix");
      await page.setViewportSize({ width, height: 900 });
      await signIn(page, role);
      const problems = watch(page);
      await openWorkspace(page);
      if (role === "organizer") await chooseWorkspaceEvent(page);
      else {
        await page
          .getByRole("combobox", { name: "Event", exact: true })
          .selectOption({ index: 1 });
        if (role === "judge-01")
          await page
            .getByRole("combobox", { name: "Stage", exact: true })
            .selectOption({ index: 1 });
      }
      await settled(page);
      for (const id of destinations[role]) {
        await goToDestination(page, id);
        await settled(page);
        await noHorizontalOverflow(page);
        await accessible(page);
        if (id === "overview")
          await page.screenshot({
            path: `tests/e2e/artifacts/uiv2-b02/${role}-${width}.png`,
            fullPage: true,
          });
      }
      if (role === "organizer") {
        await goToDestination(page, "setup");
        const form = page.locator("form").filter({
          has: page.getByRole("heading", {
            name: "Create event",
            exact: true,
          }),
        });
        await form
          .getByLabel("Name", { exact: true })
          .fill("Draft retained across destinations");
        await goToDestination(page, "overview");
        await goToDestination(page, "setup");
        await expect(form.getByLabel("Name", { exact: true })).toHaveValue(
          "Draft retained across destinations",
        );
      }
      expect(problems).toEqual([]);
    });
  }
}

test("destination links support opening a separate browser tab", async ({
  page,
}, info) => {
  test.skip(info.project.name !== "desktop", "desktop modified click");
  await page.setViewportSize({ width: 1440, height: 900 });
  await signIn(page, "judge-01");
  await openWorkspace(page);
  const previous = page.url();
  const [tab] = await Promise.all([
    page.context().waitForEvent("page"),
    page
      .locator('#workspace-navigation a[href*="view=queue"]')
      .click({ modifiers: ["ControlOrMeta"] }),
  ]);
  await expect(tab).toHaveURL(/view=queue/);
  expect(page.url()).toBe(previous);
  await expect(
    tab.locator('#workspace-navigation a[aria-current="page"]'),
  ).toHaveText("Review queue");
  await tab.close();
});

test("mobile disclosure, account escape and sign-out retain keyboard and session behavior", async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await signIn(page, "participant-01");
  await openWorkspace(page);
  const toggle = page.getByRole("button", { name: "Navigation", exact: true });
  await toggle.click();
  const team = page.locator('#workspace-navigation a[href*="view=team"]');
  await team.focus();
  await page.keyboard.press("Escape");
  await expect(toggle).toBeFocused();
  await expect(toggle).toHaveAttribute("aria-expanded", "false");
  await expect(team).toBeHidden();
  const account = page.locator(".cx-account summary");
  await account.click();
  await page.keyboard.press("Escape");
  await expect(account).toBeFocused();
  await expect(page.locator(".cx-account")).not.toHaveAttribute("open", "");
  await account.click();
  await page.getByRole("button", { name: "Sign out", exact: true }).click();
  await expect(page.getByLabel("Username")).toBeVisible();
  await expect(page).not.toHaveURL(/workspace=/);
  const response = await page.request.get("/api/v1/accounts/me/");
  expect(response.status()).toBe(401);
});
