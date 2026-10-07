import { expect, test, type Page } from "@playwright/test";
import {
  accessible,
  chooseWorkspaceEvent,
  eventIds,
  openWorkspace,
  settled,
  signIn,
} from "./support";

// PD-F005-B01-T06: the header Search finds places, events and the records of the selected event,
// through the universal query engine, and opens a hit at its place. Read-only on the reference event.
test.skip(({ isMobile }) => isMobile, "sets its own viewport");

const trigger = (page: Page) =>
  page.getByRole("button", { name: "Search or run a command" });
const dialog = (page: Page) => page.getByRole("dialog");
const box = (page: Page) => dialog(page).getByRole("combobox");

async function open(page: Page, role: string, width = 1440) {
  await page.setViewportSize({ width, height: 900 });
  await signIn(page, role);
  await openWorkspace(page);
  if (role === "organizer") await chooseWorkspaceEvent(page);
  await settled(page);
  await expect(trigger(page)).toBeVisible(); // the workspace shell, not the workspace chooser
}

/** A seeded project's name and a few letters of it, from the same query the search uses. */
async function aProject(page: Page) {
  const { workspace, event } = await eventIds(page);
  const page1 = await (
    await page.request.get(
      `/api/v1/workspaces/${workspace}/events/${event}/entities/projects/?columns=name&sort=name&limit=1`,
    )
  ).json();
  const name = page1.rows[0].name as string;
  return { name, part: name.slice(0, 4), event };
}

for (const width of [1440, 390]) {
  test(`an organizer finds a project, opens it at its list and the dialog gives focus back at ${width}`, async ({
    page,
  }) => {
    await open(page, "organizer", width);
    const { name, part, event } = await aProject(page);
    await trigger(page).click();
    await expect(box(page)).toBeFocused();
    await expect(dialog(page).getByRole("option").first()).toBeVisible(); // the commands, before anything is typed
    await box(page).fill(part);
    const group = dialog(page).locator(".cx-search__group", {
      hasText: "Projects",
    });
    await expect(group).toBeVisible();
    const hit = dialog(page).getByRole("option", { name: new RegExp(name) });
    await expect(hit.first()).toBeVisible();
    if (width === 390) {
      const b = (await dialog(page).boundingBox())!;
      expect(b.x).toBeGreaterThanOrEqual(0);
      expect(b.x + b.width).toBeLessThanOrEqual(390);
    }
    await accessible(page);
    await box(page).press("Enter");
    await expect(dialog(page)).toHaveCount(0);
    const url = new URL(page.url());
    expect(url.pathname).toMatch(/\/participants$/);
    expect(url.searchParams.get("event")).toBe(event);
    expect(url.searchParams.get("section")).toBe("ProjectsGrid");
    expect(url.search).not.toContain(part); // what was typed is not in the URL
    await expect(
      page.getByRole("tab", { name: /^Projects/, selected: true }),
    ).toBeVisible();
  });
}

test("places are found as commands, Escape closes and focus returns to Search", async ({
  page,
}) => {
  await open(page, "organizer");
  await trigger(page).click();
  await box(page).fill("judg");
  await expect(
    dialog(page).locator(".cx-search__group", { hasText: "Go to" }),
  ).toBeVisible();
  await dialog(page).getByRole("option", { name: "Go to Judging" }).click();
  await expect(page).toHaveURL(/\/judging/);
  await trigger(page).click();
  await box(page).fill("zzzzq");
  await expect(dialog(page)).toContainText("No results for “zzzzq”.");
  await page.keyboard.press("Escape");
  await expect(dialog(page)).toHaveCount(0);
  await expect(trigger(page)).toBeFocused();
});

for (const role of ["participant-01", "judge-01"]) {
  test(`${role} finds places and events but is offered no record search`, async ({
    page,
  }) => {
    await open(page, role);
    const requests: string[] = [];
    page.on("request", (r) => requests.push(r.url()));
    await trigger(page).click();
    await box(page).fill("ev");
    await expect(
      dialog(page).locator(".cx-search__group").first(),
    ).toBeVisible();
    await page.waitForTimeout(600); // let a record search show itself if it were going to
    expect(
      requests.filter(
        (url) => /\/entities\/[a-z]+\//.test(url) && url.includes("filter="),
      ),
    ).toEqual([]);
    await expect(
      dialog(page).locator(".cx-search__group", { hasText: "Projects" }),
    ).toHaveCount(0);
  });
}
