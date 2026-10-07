import { expect, test, type Page } from "@playwright/test";
import {
  chooseWorkspaceEvent,
  destinationLink,
  openWorkspace,
  settled,
  signIn,
} from "./support";

// PD-F005-B01-T03: the shell's four tiers (design D-009). Full rail from 1440, icon rail 1024-1439,
// top bar and drawer 768-1023, bottom bar of at most five controls and a "More" sheet below 768.
// Read-only: it only navigates the reference event.
test.skip(({ isMobile }) => isMobile, "sets its own viewport");

async function open(page: Page, role: string, width: number, height = 900) {
  await page.setViewportSize({ width, height });
  await signIn(page, role);
  await openWorkspace(page);
  if (role === "organizer") await chooseWorkspaceEvent(page);
  await settled(page);
}

const rail = (page: Page) => page.locator("#workspace-navigation");
const box = async (page: Page, selector: string) =>
  (await page.locator(selector).first().boundingBox())!;

for (const width of [1920, 1440]) {
  test(`the rail shows icons and words at ${width}`, async ({ page }) => {
    await open(page, "organizer", width);
    expect((await box(page, ".cx-sidebar")).width).toBe(216);
    await expect(rail(page).getByText("Event setup")).toBeVisible();
    await expect(page.locator(".cx-bottom-nav")).toBeHidden();
    await expect(
      page.getByRole("button", { name: "Navigation", exact: true }),
    ).toBeHidden();
  });
}

for (const width of [1280, 1024]) {
  test(`the rail is icons only with the words as tooltip and name at ${width}`, async ({
    page,
  }) => {
    await open(page, "organizer", width);
    expect((await box(page, ".cx-sidebar")).width).toBe(52);
    const setup = destinationLink(page, "setup");
    await expect(setup).toBeVisible();
    await expect(setup).toHaveAttribute("title", "Event setup");
    await expect(page.getByRole("link", { name: "Event setup" })).toBeVisible(); // still its accessible name
    // the words take no room: every rail link is one icon wide
    const wide = await page
      .locator(".cx-sidebar__link")
      .evaluateAll(
        (links) =>
          links.filter((l) => l.getBoundingClientRect().width > 52).length,
      );
    expect(wide).toBe(0);
    await setup.click();
    await expect(setup).toHaveAttribute("aria-current", "page");
  });
}

test("below 1024 a tablet has a top bar and a drawer opened by Navigation", async ({
  page,
}) => {
  await open(page, "organizer", 800);
  await expect(page.locator(".cx-bottom-nav")).toBeHidden();
  await expect(destinationLink(page, "judging")).toBeHidden();
  const toggle = page.getByRole("button", { name: "Navigation", exact: true });
  await toggle.click();
  await expect(toggle).toHaveAttribute("aria-expanded", "true");
  await destinationLink(page, "judging").click();
  await expect(page).toHaveURL(/\/judging/);
  await expect(destinationLink(page, "judging")).toBeHidden(); // closed after choosing
});

test("a phone keeps four places and More in a bottom bar, the rest in a sheet", async ({
  page,
}) => {
  await open(page, "organizer", 390, 844);
  const bar = page.getByRole("navigation", { name: "Quick navigation" });
  await expect(bar).toBeVisible();
  const items = bar.locator("a, button");
  await expect(items).toHaveCount(5); // Overview, People, Judging, On-site, More
  await expect(items.nth(4)).toHaveText("More");
  for (const item of await items.all()) {
    const b = (await item.boundingBox())!;
    expect(b.height).toBeGreaterThanOrEqual(44); // touch target
    expect(b.y + b.height).toBeLessThanOrEqual(844);
  }
  expect((await bar.boundingBox())!.y + (await bar.boundingBox())!.height).toBe(
    844,
  );
  await expect(bar.getByRole("link", { name: "Overview" })).toHaveAttribute(
    "aria-current",
    "page",
  );
  // the main content ends above the bar
  const mainBottom = await page.evaluate(
    () => document.querySelector("main")!.getBoundingClientRect().bottom,
  );
  expect(mainBottom).toBeGreaterThan(0);
  // the sheet holds the places that are not in the bar, grouped as on the rail
  const more = bar.getByRole("button", { name: "More" });
  await more.click();
  await expect(more).toHaveAttribute("aria-expanded", "true");
  await expect(rail(page).getByText("All sections")).toBeVisible();
  await expect(destinationLink(page, "setup")).toBeVisible();
  await expect(destinationLink(page, "operations")).toBeVisible();
  await expect(destinationLink(page, "overview")).toBeHidden(); // already in the bar
  await expect(rail(page).getByText("Advanced")).toBeVisible();
  // Escape closes the sheet and returns focus to More
  await page.keyboard.press("Escape");
  await expect(more).toBeFocused();
  await expect(destinationLink(page, "setup")).toBeHidden();
  // choosing a place goes there, closes the sheet and marks the place
  await more.click();
  await destinationLink(page, "setup").click();
  await expect(page).toHaveURL(/\/setup/);
  await expect(destinationLink(page, "setup")).toBeHidden();
  await expect(more).toHaveAttribute("aria-expanded", "false");
  // the scrim closes it too
  await more.click();
  await page.locator(".cx-sheet-scrim").click({ position: { x: 10, y: 10 } });
  await expect(destinationLink(page, "setup")).toBeHidden();
});

test("a judge's five places all fit in the bar and there is no More", async ({
  page,
}) => {
  await open(page, "judge-01", 390, 844);
  const bar = page.getByRole("navigation", { name: "Quick navigation" });
  await expect(bar.locator("a")).toHaveCount(5);
  await expect(bar.getByRole("button")).toHaveCount(0);
  await expect(bar.getByText("Queue", { exact: true })).toBeVisible();
  await bar.getByRole("link", { name: "Schedule" }).click();
  await expect(page).toHaveURL(/\/schedule/);
  await expect(bar.getByRole("link", { name: "Schedule" })).toHaveAttribute(
    "aria-current",
    "page",
  );
});

test("a participant has four places and More for resources and profile", async ({
  page,
}) => {
  await open(page, "participant-01", 390, 844);
  const bar = page.getByRole("navigation", { name: "Quick navigation" });
  await expect(bar.locator("a")).toHaveCount(4);
  await expect(bar.getByRole("button", { name: "More" })).toBeVisible();
  await bar.getByRole("button", { name: "More" }).click();
  await expect(destinationLink(page, "resources")).toBeVisible();
  await expect(destinationLink(page, "profile")).toBeVisible();
});
