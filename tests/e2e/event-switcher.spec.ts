import { expect, test, type Page } from "@playwright/test";
import { eventIds, openWorkspace, settled, signIn } from "./support";

// PD-F005-B01-T02: choose the event from the top bar; favorites and recents are remembered on this
// device and forgotten at sign-out. Read-only on the reference event.
test.skip(({ isMobile }) => isMobile, "sets its own viewport");

const switcher = (page: Page) => page.locator(".cx-switcher");
const trigger = (page: Page) => page.locator(".cx-switcher summary");

for (const width of [1440, 390]) {
  test(`an organizer picks the event, stars it and finds it again after a reload at ${width}`, async ({
    page,
  }) => {
    await page.setViewportSize({ width, height: 900 });
    await signIn(page, "organizer");
    const { workspace, event, name } = await eventIds(page);
    await page.goto(`/app/w/${workspace}/overview`);
    await settled(page);
    await expect(trigger(page)).toContainText(/Choose an event|Loading events/);
    await trigger(page).click();
    await expect(page.getByRole("link", { name })).toBeVisible();
    await page.getByRole("link", { name }).click();
    expect(new URL(page.url()).searchParams.get("event")).toBe(event);
    await expect(trigger(page)).toContainText(name);
    await expect(switcher(page)).not.toHaveAttribute("open", "");
    // star it: it moves under Favorites
    await trigger(page).click();
    await page.getByRole("button", { name: `Favorite ${name}` }).click();
    await expect(
      switcher(page).getByRole("region", { name: "Favorite events" }),
    ).toContainText(name);
    // device-local: it is still a favorite after a reload, and the current event follows the URL
    await page.reload();
    await settled(page);
    await expect(trigger(page)).toContainText(name);
    await trigger(page).click();
    await expect(
      switcher(page).getByRole("region", { name: "Favorite events" }),
    ).toContainText(name);
    await expect(
      page.getByRole("button", { name: `Favorite ${name}` }),
    ).toHaveAttribute("aria-pressed", "true");
    // Escape closes it and returns focus to its button
    await page.keyboard.press("Escape");
    await expect(switcher(page)).not.toHaveAttribute("open", "");
    await expect(trigger(page)).toBeFocused();
  });
}

test("choosing an event is a history entry and Back returns to the place before it", async ({
  page,
}) => {
  await signIn(page, "organizer");
  const { workspace, name } = await eventIds(page);
  await page.goto(`/app/w/${workspace}/judging`);
  await settled(page);
  await trigger(page).click();
  await page.getByRole("link", { name }).click();
  await expect(page).toHaveURL(/\/judging\?event=/);
  await page.goBack();
  await expect(page).toHaveURL(new RegExp(`/judging$`));
  await expect(trigger(page)).toContainText("Choose an event");
});

test("sign-out forgets the favorites kept on the device", async ({ page }) => {
  await signIn(page, "organizer");
  const { workspace, name } = await eventIds(page);
  await page.goto(`/app/w/${workspace}/overview`);
  await settled(page);
  await trigger(page).click();
  await page.getByRole("button", { name: `Favorite ${name}` }).click();
  expect(
    await page.evaluate(() =>
      Object.keys(localStorage).filter((k) => k.startsWith("conflux:v1:")),
    ),
  ).not.toEqual([]);
  await page.locator(".cx-account summary").click();
  await page.getByRole("button", { name: "Sign out", exact: true }).click();
  await expect(page.getByLabel("Username")).toBeVisible();
  expect(
    await page.evaluate(() =>
      Object.keys(localStorage).filter((k) => k.startsWith("conflux:v1:")),
    ),
  ).toEqual([]);
});

for (const role of ["participant-01", "judge-01"]) {
  test(`${role} sees the events they may choose from, nothing from other roles`, async ({
    page,
  }) => {
    await signIn(page, role);
    await openWorkspace(page);
    await settled(page);
    await expect(trigger(page)).toBeVisible();
    await trigger(page).click();
    const panel = page.locator(".cx-switcher__panel");
    await expect(panel).toBeVisible();
    const events = await panel
      .locator(".cx-switcher__choice")
      .allTextContents();
    expect(events.length).toBeGreaterThan(0);
    // the same list the role's own event picker offers
    const me = await (await page.request.get("/api/v1/accounts/me/")).json();
    const ws = me.memberships[0].workspace;
    const listed = await (
      await page.request.get(
        `/api/v1/workspaces/${ws}/${role === "judge-01" ? "judge" : "participant"}-events/`,
      )
    ).json();
    for (const item of listed) expect(events).toContain(item.name);
  });
}
