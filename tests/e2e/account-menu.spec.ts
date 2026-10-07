import { expect, test, type Page } from "@playwright/test";
import {
  accessible,
  chooseWorkspaceEvent,
  eventIds,
  openWorkspace,
  settled,
  signIn,
} from "./support";

// PD-F005-B01-T08: the account menu holds the profile link, notification preferences and the theme.
// The theme is the person's on the app's own screens (system by default) and never reaches the public
// pages; it is device-local and forgotten at sign-out. Read-only on the reference event.
test.skip(({ isMobile }) => isMobile, "sets its own viewport");

const theme = (page: Page) =>
  page.evaluate(() => document.documentElement.getAttribute("data-theme"));
const menu = (page: Page) => page.locator(".cx-account");

async function open(page: Page, role: string, width = 1440) {
  await page.setViewportSize({ width, height: 900 });
  await signIn(page, role);
  await openWorkspace(page);
  if (role === "organizer") await chooseWorkspaceEvent(page);
  await settled(page);
}

test("the menu lists profile, notification preferences, theme and sign-out", async ({
  page,
}) => {
  await open(page, "organizer");
  await menu(page).locator("summary").click();
  await expect(
    menu(page).getByRole("link", { name: "View profile" }),
  ).toBeVisible();
  await expect(
    menu(page).getByRole("link", { name: "Notification preferences" }),
  ).toBeVisible();
  const radios = menu(page).getByRole("radio");
  await expect(radios).toHaveCount(3);
  await expect(menu(page).getByRole("radio", { name: "System" })).toBeChecked();
  await expect(
    menu(page).getByRole("button", { name: "Sign out", exact: true }),
  ).toBeVisible();
});

test("Notification preferences opens the profile at that section", async ({
  page,
}) => {
  await open(page, "participant-01");
  await menu(page).locator("summary").click();
  await menu(page)
    .getByRole("link", { name: "Notification preferences" })
    .click();
  await expect(page).toHaveURL(/\/profile.*#notification-preferences/);
  const section = page.getByRole("region", {
    name: "Notification preferences",
  });
  await expect(section).toBeVisible();
  // the disclosure is open and its heading holds focus, so a keyboard user lands on it
  await expect(
    page.locator("details#notification-preferences"),
  ).toHaveAttribute("open", "");
  await expect(
    page.locator("details#notification-preferences > summary"),
  ).toBeFocused();
});

for (const width of [1440, 390]) {
  test(`dark applies at once, survives a reload and passes the accessibility gate at ${width}`, async ({
    page,
  }) => {
    await open(page, "organizer", width);
    await expect.poll(() => theme(page)).toBe("light"); // system, and this browser asks for light
    await menu(page).locator("summary").click();
    await menu(page).getByRole("radio", { name: "Dark" }).check();
    await expect.poll(() => theme(page)).toBe("dark");
    const background = await page.evaluate(
      () => getComputedStyle(document.body).backgroundColor,
    );
    expect(background).not.toBe("rgb(255, 255, 255)");
    await page.reload();
    await settled(page);
    await expect.poll(() => theme(page)).toBe("dark");
    await accessible(page);
    await menu(page).locator("summary").click();
    await expect(menu(page).getByRole("radio", { name: "Dark" })).toBeChecked();
  });
}

test("System follows the operating system and changes with it", async ({
  page,
}) => {
  await page.emulateMedia({ colorScheme: "dark" });
  await open(page, "judge-01");
  await expect.poll(() => theme(page)).toBe("dark");
  await page.emulateMedia({ colorScheme: "light" });
  await expect.poll(() => theme(page)).toBe("light");
  await menu(page).locator("summary").click();
  await menu(page).getByRole("radio", { name: "Light" }).check();
  await page.emulateMedia({ colorScheme: "dark" });
  await page.waitForTimeout(300); // give a wrong follow time to show
  expect(await theme(page)).toBe("light"); // an explicit choice does not follow the system
});

test("the choice never reaches the public pages and is forgotten at sign-out", async ({
  page,
}) => {
  await open(page, "organizer");
  const { event } = await eventIds(page);
  await menu(page).locator("summary").click();
  await menu(page).getByRole("radio", { name: "Dark" }).check();
  await expect.poll(() => theme(page)).toBe("dark");
  // the server-rendered public site is another document, themed by the organizer
  await page.goto(`/e/${event}/`);
  expect(await theme(page)).not.toBe("dark");
  // the public event page in the app follows its own event theme as well
  await page.goto(`/app/event/${event}`);
  await page.waitForLoadState("networkidle");
  await expect.poll(() => theme(page)).toBeNull();
  await page.goBack();
  await page.goBack();
  await settled(page);
  await menu(page).locator("summary").click();
  await menu(page)
    .getByRole("button", { name: "Sign out", exact: true })
    .click();
  await expect(page.getByLabel("Username")).toBeVisible();
  await expect.poll(() => theme(page)).toBeNull();
  expect(
    await page.evaluate(() =>
      Object.keys(localStorage).filter((key) => key.includes(":theme")),
    ),
  ).toEqual([]);
});
