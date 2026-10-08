import { expect, test, type Page } from "@playwright/test";
import { accessible, eventIds, settled, signIn } from "./support";

// PD-F006-B02-T07: a transient view in the address. A filter whose values are all structured is in
// the link and opens the same list for anyone; a filter with text is never put in a link and the
// person is told to save a view; a link that does not fit is refused whole. Read-only.
const grid = (page: Page) =>
  page.locator('.cx-entity-grid[data-entity="projects"]');

async function openTools(page: Page) {
  const tools = grid(page).locator(".cx-entity-grid__tools");
  if (!(await tools.evaluate((el) => (el as HTMLDetailsElement).open)))
    await tools.locator("summary").click();
}

test("a structured filter is in the address and reopens the same list; text is kept out of it", async ({
  page,
  context,
}) => {
  await signIn(page, "organizer");
  const { workspace, event } = await eventIds(page);
  const api = `/api/v1/workspaces/${workspace}/events/${event}/entities/projects/`;
  const tree = { field: "gallery_visible", op: "eq", value: true };
  const expected = await (
    await page.request.get(
      `${api}?filter=${encodeURIComponent(JSON.stringify(tree))}`,
    )
  ).json();
  const base = `/app/w/${workspace}/participants?event=${event}&section=ProjectsGrid`;

  await page.goto(base);
  await settled(page);
  await expect(grid(page).locator("tbody tr").first()).toBeVisible();
  await openTools(page);
  await grid(page)
    .getByRole("button", { name: "Add condition", exact: true })
    .click();
  await grid(page)
    .getByLabel("Field of condition 1")
    .selectOption({ label: "In gallery" });
  await expect(
    grid(page).getByRole("group", { name: "Active filter" }),
  ).toContainText("In gallery is yes");
  await expect(page).toHaveURL(/f_projects=[A-Za-z0-9_-]+/);
  const link = page.url();
  expect(link).not.toContain("gallery_visible"); // encoded, not spelled out

  // someone opens the link in a fresh page: the same filter, the same rows
  const other = await context.newPage();
  await other.goto(link);
  await settled(other);
  await expect(grid(other).locator("tbody tr").first()).toBeVisible();
  await expect(
    grid(other).getByRole("group", { name: "Active filter" }),
  ).toContainText("In gallery is yes");
  await expect(grid(other)).toContainText(
    `of ${expected.total.toLocaleString("en-US")}`,
  );
  await accessible(other);
  await other.close();

  // free text is not put in a link, and the person is told how to share it
  await grid(page)
    .getByLabel("Field of condition 1")
    .selectOption({ label: "Project" });
  await grid(page).getByLabel("Value of condition 1").fill("Bright");
  await expect(page).not.toHaveURL(/f_projects/);
  expect(page.url()).not.toContain("Bright");
  await expect(grid(page)).toContainText("not in the link");
  await expect(grid(page)).toContainText("Save it as a view to share it.");

  // a link that does not decode or holds text is refused whole: everything shows, the address is clean
  const forged = Buffer.from(
    JSON.stringify({ field: "name", op: "contains", value: "x" }),
  ).toString("base64url");
  for (const bad of ["not-a-filter", forged]) {
    await page.goto(`${base}&f_projects=${bad}`);
    await settled(page);
    await expect(grid(page).locator("tbody tr").first()).toBeVisible();
    await expect(
      grid(page).getByRole("group", { name: "Active filter" }),
    ).toHaveCount(0);
    await expect(grid(page)).toContainText(
      `of ${(await (await page.request.get(api)).json()).total}`,
    );
    await expect(page).not.toHaveURL(/f_projects/);
  }
});
