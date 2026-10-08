import { expect, test, type Page } from "@playwright/test";
import {
  accessible,
  chooseWorkspaceEvent,
  openWorkspace,
  settled,
  signIn,
} from "./support";

// PD-F005-B01-T05: the command palette. Ctrl+K from anywhere in the workspace opens one overlay of
// commands (go to a place, switch event, theme, preferences, sign out) and record search; commands
// only navigate or change presentation. Read-only on the reference event; it ends by signing out.
test.skip(({ isMobile }) => isMobile, "sets its own viewport");

const dialog = (page: Page) => page.getByRole("dialog");
const box = (page: Page) => dialog(page).getByRole("combobox");
const theme = (page: Page) =>
  page.evaluate(() => document.documentElement.getAttribute("data-theme"));

async function open(page: Page, role: string, width = 1440) {
  await page.setViewportSize({ width, height: 900 });
  await signIn(page, role);
  await openWorkspace(page);
  if (role === "organizer") await chooseWorkspaceEvent(page);
  await settled(page);
  // the palette belongs to the workspace shell: wait until it is there before using the keys
  await expect(page.locator(".cx-search-open")).toBeVisible();
}

for (const width of [1440, 390]) {
  test(`Ctrl+K opens the palette, a command goes to its place and focus lands on the page at ${width}`, async ({
    page,
  }) => {
    await open(page, "organizer", width);
    await page.keyboard.press("Control+k");
    await expect(dialog(page)).toBeVisible();
    await expect(box(page)).toBeFocused();
    await expect(box(page)).toHaveAttribute("aria-expanded", "true");
    const groups = await dialog(page)
      .locator(".cx-search__group")
      .allTextContents();
    expect(groups).toEqual(
      expect.arrayContaining(["Go to", "Appearance", "Account"]),
    );
    if (width === 390) {
      const b = (await dialog(page).boundingBox())!;
      expect(b.x).toBeGreaterThanOrEqual(0);
      expect(b.x + b.width).toBeLessThanOrEqual(390);
    }
    await accessible(page);
    await box(page).fill("go jud");
    await expect(dialog(page).getByRole("option")).toHaveCount(1);
    await expect(dialog(page).getByRole("option")).toHaveText(/^Go to Judging/); // its shortcut is beside it
    await box(page).press("Enter");
    await expect(dialog(page)).toHaveCount(0);
    await expect(page).toHaveURL(/\/judging\?event=/);
    await expect(page.locator("main")).toBeFocused();
    // it is remembered: the next time it is first
    await page.keyboard.press("Control+k");
    await expect(dialog(page).locator(".cx-search__group").first()).toHaveText(
      "Recent",
    );
    await expect(dialog(page).getByRole("option").first()).toHaveText(
      "Go to Judging",
    );
    await page.keyboard.press("Control+k"); // the same keys close it
    await expect(dialog(page)).toHaveCount(0);
  });
}

test("arrow keys move the choice, Escape closes and focus returns to where it was", async ({
  page,
}) => {
  await open(page, "organizer");
  await page.getByRole("link", { name: "Judging", exact: true }).focus();
  await page.keyboard.press("Control+k");
  await box(page).fill("go to");
  const options = dialog(page).getByRole("option");
  await expect(options.first()).toHaveAttribute("aria-selected", "true");
  await page.keyboard.press("ArrowDown");
  await expect(options.nth(1)).toHaveAttribute("aria-selected", "true");
  await expect(box(page)).toHaveAttribute(
    "aria-activedescendant",
    (await options.nth(1).getAttribute("id"))!,
  );
  await page.keyboard.press("ArrowUp");
  await page.keyboard.press("ArrowUp"); // wraps to the last
  await expect(options.last()).toHaveAttribute("aria-selected", "true");
  await page.keyboard.press("Escape");
  await expect(dialog(page)).toHaveCount(0);
  await expect(
    page.getByRole("link", { name: "Judging", exact: true }),
  ).toBeFocused();
});

test("the theme command changes presentation only and a command a role lacks is not offered", async ({
  page,
}) => {
  await open(page, "participant-01");
  await page.keyboard.press("Control+k");
  await box(page).fill("event setup");
  await expect(
    dialog(page).getByRole("option", { name: "Go to Event setup" }),
  ).toHaveCount(0); // an organizer place
  await box(page).fill("dark");
  await box(page).press("Enter");
  await expect.poll(() => theme(page)).toBe("dark");
  await page.keyboard.press("Control+k");
  await box(page).fill("system theme");
  await box(page).press("Enter");
  await expect.poll(() => theme(page)).toBe("light");
});

test("Sign out runs the same sign-out as the account menu", async ({
  page,
}) => {
  await open(page, "judge-01");
  await page.keyboard.press("Control+k");
  await box(page).fill("sign out");
  await box(page).press("Enter");
  await expect(page.getByLabel("Username")).toBeVisible();
  const response = await page.request.get("/api/v1/accounts/me/");
  expect(response.status()).toBe(401);
});
