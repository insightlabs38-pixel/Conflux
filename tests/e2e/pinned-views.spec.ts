import { expect, test, type Page } from "@playwright/test";
import { eventIds, settled, signIn } from "./support";

// PD-F005-B02-T03: a saved view can be pinned and is then offered first in the palette. A pin is the
// person's, kept on the device; the view itself is the server's. It creates a saved view, so it runs
// on an isolated fixture.
const dialog = (page: Page) => page.getByRole("dialog");
// the Registration and Projects grids are both mounted; this is the Projects one
const grid = (page: Page) =>
  page.locator('.cx-entity-grid[data-entity="projects"]');

/** The view bar sits in the grid's collapsed "Filter, views and columns" disclosure. */
async function openTools(page: Page) {
  const tools = grid(page).locator(".cx-entity-grid__tools");
  if (!(await tools.evaluate((el) => (el as HTMLDetailsElement).open)))
    await tools.locator("summary").click();
}

async function makeView(page: Page, name: string) {
  const { workspace, event } = await eventIds(page);
  const base = `/api/v1/workspaces/${workspace}/events/${event}/views/`;
  const response = await page.request.post(base, {
    data: {
      entity: "projects",
      name,
      visibility: "private",
      query: {
        filter: null,
        sort: "name",
        columns: [],
        density: "comfortable",
      },
    },
  });
  expect(response.status()).toBe(201);
  const view = await response.json();
  return { workspace, event, base, id: view.public_id as string };
}

for (const width of [1440, 390]) {
  test(`a pinned view is offered first in the palette and opens selected at ${width}`, async ({
    page,
  }, info) => {
    test.skip(info.project.name !== "desktop", "explicit viewport matrix");
    await page.setViewportSize({ width, height: 900 });
    await signIn(page, "organizer");
    const { workspace, event, id } = await makeView(
      page,
      `Needs review ${width}`,
    );
    await page.goto(
      `/app/w/${workspace}/participants?event=${event}&section=ProjectsGrid`,
    );
    await settled(page);
    await openTools(page);
    await grid(page)
      .getByRole("group", { name: "Saved views" })
      .getByRole("combobox")
      .selectOption(id);
    const pin = grid(page).getByRole("button", { name: "Pin view" });
    await expect(pin).toHaveAttribute("aria-pressed", "false");
    await pin.click();
    await expect(
      grid(page).getByRole("button", { name: "Unpin view" }),
    ).toHaveAttribute("aria-pressed", "true");

    // from anywhere: the palette offers it first
    await page.goto(`/app/w/${workspace}/overview?event=${event}`);
    await settled(page);
    await page.locator(".cx-search-open").click();
    await expect(dialog(page).locator(".cx-search__group").first()).toHaveText(
      "Pinned views",
    );
    const option = dialog(page).getByRole("option", {
      name: `Open view Needs review ${width}`,
    });
    await expect(option).toBeVisible();
    await option.click();
    const url = new URL(page.url());
    expect(url.pathname).toMatch(/\/participants$/);
    expect(url.searchParams.get("section")).toBe("ProjectsGrid");
    expect(url.searchParams.get("view_projects")).toBe(id);
    await expect(grid(page)).toBeVisible();
    await openTools(page);
    await expect(
      grid(page)
        .getByRole("group", { name: "Saved views" })
        .getByRole("combobox"),
    ).toHaveValue(id);
    await expect(
      grid(page).getByRole("button", { name: "Unpin view" }),
    ).toBeVisible();
  });
}

test("unpinning removes it, a deleted view is no longer offered and pins are forgotten at sign-out", async ({
  page,
}) => {
  await signIn(page, "organizer");
  const { workspace, event, base, id } = await makeView(page, "Short lived");
  await page.goto(
    `/app/w/${workspace}/participants?event=${event}&section=ProjectsGrid&view_projects=${id}`,
  );
  await settled(page);
  await openTools(page);
  await grid(page).getByRole("button", { name: "Pin view" }).click();
  const offered = async () => {
    await page.keyboard.press("Control+k");
    await expect(dialog(page)).toBeVisible();
    const found = await dialog(page)
      .getByRole("option", { name: "Open view Short lived" })
      .count();
    await page.keyboard.press("Escape");
    return found;
  };
  await page.locator("main").focus();
  expect(await offered()).toBe(1);
  await grid(page).getByRole("button", { name: "Unpin view" }).click();
  expect(await offered()).toBe(0);

  // pin again, delete the view on the server: the pin does not resolve and is not shown
  await grid(page).getByRole("button", { name: "Pin view" }).click();
  expect(await offered()).toBe(1);
  const deleted = await page.request.delete(`${base}${id}/`);
  expect(deleted.status()).toBeLessThan(300);
  await page.goto(`/app/w/${workspace}/overview?event=${event}`);
  await settled(page);
  await page.locator("main").focus();
  expect(await offered()).toBe(0);

  await page.locator(".cx-account summary").click();
  await page.getByRole("button", { name: "Sign out", exact: true }).click();
  await expect(page.getByLabel("Username")).toBeVisible();
  expect(
    await page.evaluate(() =>
      Object.keys(localStorage).filter((k) => k.includes(":pinned-views")),
    ),
  ).toEqual([]);
});
