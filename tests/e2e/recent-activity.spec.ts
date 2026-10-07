import { expect, test, type Page } from "@playwright/test";
import { eventIds, settled, signIn } from "./support";

// PD-F005-B02-T02: the palette offers the organizer's own latest actions (from the audit log) and
// the saved views they opened lately. It performs a real audited change and creates a saved view, so
// it runs on an isolated fixture.
const dialog = (page: Page) => page.getByRole("dialog");
const words = (action: string) => {
  const text = action.replace(/[._]+/g, " ").trim();
  return text.charAt(0).toUpperCase() + text.slice(1);
};

for (const width of [1440, 390]) {
  test(`the palette shows what I did last and links to where it is kept at ${width}`, async ({
    page,
  }, info) => {
    test.skip(info.project.name !== "desktop", "explicit viewport matrix");
    await page.setViewportSize({ width, height: 900 });
    await signIn(page, "organizer");
    const { workspace, event } = await eventIds(page);
    // a real audited change by this organizer
    const created = await page.request.post(
      `/api/v1/workspaces/${workspace}/events/${event}/tracks/`,
      {
        data: {
          name: `Recent ${width}`,
          description: "for the recent actions test",
        },
      },
    );
    expect(created.status()).toBe(201);
    const mine = await (
      await page.request.get(`/api/v1/audit/${workspace}/?mine=1&limit=8`)
    ).json();
    expect(mine.length).toBeGreaterThan(0);
    expect(
      mine.every((row: { actor: string }) => row.actor === mine[0].actor),
    ).toBe(true);
    const newest = words(mine[0].action);

    await page.goto(`/app/w/${workspace}/overview?event=${event}`);
    await settled(page);
    await page.locator(".cx-search-open").click();
    const group = dialog(page).locator(".cx-search__group", {
      hasText: "Recent actions",
    });
    await expect(group).toBeVisible();
    const first = dialog(page).getByRole("option", {
      name: new RegExp(`^${newest}`),
    });
    await expect(first.first()).toBeVisible();
    await expect(first.first()).toContainText(/just now|min ago/);
    // typing narrows them; choosing one opens Operations and audit
    await dialog(page)
      .getByRole("combobox")
      .fill(newest.split(" ")[0].toLowerCase());
    await expect(first.first()).toBeVisible();
    await first.first().click();
    await expect(page).toHaveURL(/\/operations\?event=/);
  });
}

test("a view I opened lately is offered, and it is not offered twice once pinned", async ({
  page,
}) => {
  await signIn(page, "organizer");
  const { workspace, event } = await eventIds(page);
  const made = await page.request.post(
    `/api/v1/workspaces/${workspace}/events/${event}/views/`,
    {
      data: {
        entity: "projects",
        name: "Opened lately",
        visibility: "private",
        query: {
          filter: null,
          sort: "name",
          columns: [],
          density: "comfortable",
        },
      },
    },
  );
  expect(made.status()).toBe(201);
  const id = (await made.json()).public_id as string;
  await page.goto(
    `/app/w/${workspace}/participants?event=${event}&section=ProjectsGrid`,
  );
  await settled(page);
  const grid = page.locator('.cx-entity-grid[data-entity="projects"]');
  await grid.locator(".cx-entity-grid__tools > summary").click();
  await grid
    .getByRole("group", { name: "Saved views" })
    .getByRole("combobox")
    .selectOption(id);
  await page.goto(`/app/w/${workspace}/overview?event=${event}`);
  await settled(page);
  await page.keyboard.press("Control+k");
  await expect(
    dialog(page).locator(".cx-search__group", { hasText: "Recent views" }),
  ).toBeVisible();
  await expect(
    dialog(page).getByRole("option", { name: "Open view Opened lately" }),
  ).toBeVisible();
  await page.keyboard.press("Escape");
  // pin it: it moves to Pinned views and is no longer listed as recent
  await page.goto(
    `/app/w/${workspace}/participants?event=${event}&section=ProjectsGrid&view_projects=${id}`,
  );
  await settled(page);
  await grid.locator(".cx-entity-grid__tools > summary").click();
  await grid.getByRole("button", { name: "Pin view" }).click();
  await page.goto(`/app/w/${workspace}/overview?event=${event}`);
  await settled(page);
  await page.keyboard.press("Control+k");
  await expect(
    dialog(page).locator(".cx-search__group", { hasText: "Pinned views" }),
  ).toBeVisible();
  await expect(
    dialog(page).locator(".cx-search__group", { hasText: "Recent views" }),
  ).toHaveCount(0);
});

test("a participant is offered no recent actions and nothing is asked of the audit log", async ({
  page,
}) => {
  await signIn(page, "participant-01");
  const asked: string[] = [];
  page.on("request", (r) => {
    if (r.url().includes("/api/v1/audit/")) asked.push(r.url());
  });
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto("/app/");
  await page
    .getByRole("button", { name: /participant/i })
    .first()
    .click();
  await settled(page);
  await page.locator(".cx-search-open").click();
  await expect(dialog(page)).toBeVisible();
  await expect(
    dialog(page).locator(".cx-search__group", { hasText: "Recent actions" }),
  ).toHaveCount(0);
  expect(asked).toEqual([]);
});
