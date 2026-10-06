import { chooseWorkspaceEvent } from "./support";
import { expect, test, type Page } from "@playwright/test";
import {
  accessible,
  destinationLink,
  goToDestination,
  noHorizontalOverflow,
  openWorkspace,
  settled,
  signIn,
  watch,
  capture,
} from "./support";

// Optional modules the reference event neither uses nor has turned on are not offered
// (PD-F001-B01-T04); the reference event has eligibility and on-site content but no integrations.
// The deep link of a hidden one stays a valid place.
const hiddenOrganizer = [{ id: "integrations", module: "Integrations" }];
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
          await capture(page, {
            path: `tests/e2e/artifacts/uiv2-b02/${role}-${width}.png`,
            fullPage: true,
          });
      }
      if (role === "organizer") {
        for (const { id, module } of hiddenOrganizer) {
          await expect(destinationLink(page, id)).toHaveCount(0);
          await page.goto(
            page.url().replace(/\/w\/([^/]+)\/[^?]+/, `/w/$1/${id}`),
          );
          await expect(
            page.getByText(`${module} is not turned on for this event.`),
          ).toBeVisible();
          await settled(page);
          await noHorizontalOverflow(page);
          await accessible(page);
        }
        await goToDestination(page, "setup");
        await page
          .getByText("Create a new event or start from a template")
          .click();
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
  test.setTimeout(90_000); // room for the popup attempts below
  await page.setViewportSize({ width: 1440, height: 900 });
  await signIn(page, "judge-01");
  await openWorkspace(page);
  const previous = page.url();
  const link = destinationLink(page, "queue");
  // Contract, independent of browser plumbing: a modified click falls through to the browser
  // (default not prevented) while a plain click is handled in-app (default prevented).
  const prevented = (modifiers: boolean) =>
    link.evaluate((a, ctrl) => {
      const event = new MouseEvent("click", {
        bubbles: true,
        cancelable: true,
        button: 0,
        ctrlKey: ctrl,
      });
      a.dispatchEvent(event);
      return event.defaultPrevented;
    }, modifiers);
  expect(await prevented(true)).toBe(false);
  expect(await prevented(false)).toBe(true);
  await page.goto(previous); // the plain synthetic click navigated in-app; restore the view
  // End to end: the real modified click opens the queue view in a second tab. Under heavy load
  // Chromium sometimes opens the tab without Playwright registering the popup (no `page` event, url
  // stays ""), so the whole user action is attempted up to three times; a real regression fails all.
  let tab!: Page;
  let attempts = 0;
  await expect(async () => {
    attempts++;
    for (const extra of page.context().pages())
      if (extra !== page) await extra.close();
    const opened = page.context().waitForEvent("page", { timeout: 7_000 });
    await destinationLink(page, "queue").click({
      modifiers: ["ControlOrMeta"],
    });
    tab = await opened;
    await tab.waitForLoadState("domcontentloaded");
    expect(await tab.evaluate(() => location.pathname)).toMatch(/\/queue$/);
    await expect(
      tab.locator('#workspace-navigation a[aria-current="page"]'),
    ).toHaveText("Review queue", { timeout: 5_000 });
  }).toPass({ intervals: [0], timeout: 45_000 });
  if (attempts > 1)
    info.annotations.push({
      type: "popup-attempts",
      description: `${attempts} attempts (popup tracking lost under load)`,
    });
  expect(page.url()).toBe(previous);
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
  const team = destinationLink(page, "team");
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
