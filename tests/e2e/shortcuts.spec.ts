import { expect, test, type Page } from "@playwright/test";
import {
  accessible,
  chooseWorkspaceEvent,
  openWorkspace,
  settled,
  signIn,
} from "./support";

// PD-F005-B02-T07: "?" shows the shortcut help, "/" opens the palette and "G then a letter" goes to a
// place; single-key shortcuts can be switched off. Read-only on the reference event.
test.skip(({ isMobile }) => isMobile, "sets its own viewport");

const dialog = (page: Page) => page.getByRole("dialog");

async function open(page: Page, role: string, width = 1440) {
  await page.setViewportSize({ width, height: 900 });
  await signIn(page, role);
  await openWorkspace(page);
  if (role === "organizer") await chooseWorkspaceEvent(page);
  await settled(page);
  await expect(page.locator(".cx-search-open")).toBeVisible();
  await page.locator("main").focus(); // keys go to the page, not to a field
}

test("? shows the shortcuts for this role, G then a letter goes there, Esc closes the help", async ({
  page,
}) => {
  await open(page, "organizer");
  await page.keyboard.press("?");
  await expect(dialog(page)).toBeVisible();
  await expect(
    dialog(page).getByRole("heading", { name: "Keyboard shortcuts" }),
  ).toBeVisible();
  await expect(dialog(page)).toContainText("G then J");
  await expect(dialog(page)).toContainText("Go to Judging");
  await expect(dialog(page)).toContainText("Search or run a command");
  await accessible(page);
  await page.keyboard.press("Escape");
  await expect(dialog(page)).toHaveCount(0);

  await page.keyboard.press("g");
  await page.keyboard.press("j");
  await expect(page).toHaveURL(/\/judging\?event=/);
  await expect(page.locator("main")).toBeFocused();
  await page.keyboard.press("g");
  await page.keyboard.press("r");
  await expect(page).toHaveURL(/\/results\?event=/);
});

test("/ opens the palette, and the keys are silent while typing and inside a dialog", async ({
  page,
}) => {
  await open(page, "organizer");
  await page.keyboard.press("/");
  await expect(dialog(page).getByRole("combobox")).toBeFocused();
  // inside the palette's own box a ? or g is text
  await dialog(page).getByRole("combobox").fill("g");
  await page.keyboard.type("?j");
  await expect(dialog(page).getByRole("combobox")).toHaveValue("g?j");
  await expect(page).not.toHaveURL(/\/judging/);
  await page.keyboard.press("Escape");
  await expect(dialog(page)).toHaveCount(0);
});

test("single-key shortcuts can be switched off and stay off after a reload; Ctrl+K still works", async ({
  page,
}) => {
  await open(page, "judge-01");
  await page.keyboard.press("?");
  const box = dialog(page).getByRole("checkbox", {
    name: /single-key shortcuts/i,
  });
  await expect(box).toBeChecked();
  await box.uncheck();
  await expect(dialog(page)).toContainText("Single-key shortcuts are off");
  await page.keyboard.press("Escape");
  await page.locator("main").focus();
  await page.keyboard.press("g");
  await page.keyboard.press("q");
  await expect(page).not.toHaveURL(/\/queue/);
  await page.keyboard.press("?");
  await expect(dialog(page)).toHaveCount(0);
  await page.reload();
  await settled(page);
  await page.locator("main").focus();
  await page.keyboard.press("?");
  await expect(dialog(page)).toHaveCount(0);
  await page.keyboard.press("Control+k"); // the modifier keys stay
  await expect(dialog(page).getByRole("combobox")).toBeVisible();
});

test("the account menu opens the help at 390 where there is no keyboard shortcut to find it", async ({
  page,
}) => {
  await open(page, "participant-01", 390);
  await page.locator(".cx-account summary").click();
  await page.getByRole("button", { name: "Keyboard shortcuts" }).click();
  await expect(dialog(page)).toBeVisible();
  await expect(dialog(page)).toContainText("G then T"); // Team
  const b = (await dialog(page).boundingBox())!;
  expect(b.x).toBeGreaterThanOrEqual(0);
  expect(b.x + b.width).toBeLessThanOrEqual(390);
  await accessible(page);
});
