import { expect, test, type Page } from "@playwright/test";
import { accessible, eventIds, settled, signIn } from "./support";

// PD-F006-B01-T03: structured filters. Conditions typed by field, the active filter read back as a
// sentence outside the tools, and the server's refusal shown beside the condition it names while the
// list keeps its last results. Read-only on the reference event.
const grid = (page: Page) =>
  page.locator('.cx-entity-grid[data-entity="projects"]');

async function openTools(page: Page) {
  const tools = grid(page).locator(".cx-entity-grid__tools");
  if (!(await tools.evaluate((el) => (el as HTMLDetailsElement).open)))
    await tools.locator("summary").click();
}

test("a condition filters through the server and reads back as a sentence; a refused value is explained beside it", async ({
  page,
}) => {
  await signIn(page, "organizer");
  const { workspace, event } = await eventIds(page);
  const api = `/api/v1/workspaces/${workspace}/events/${event}/entities/projects/`;
  const all = await (await page.request.get(`${api}?sort=name`)).json();
  const track = String(
    all.rows.find((r: { track?: string }) => r.track)?.track,
  );
  const filter = JSON.stringify({ field: "track", op: "eq", value: track });
  const expected = await (
    await page.request.get(`${api}?filter=${encodeURIComponent(filter)}`)
  ).json();
  expect(expected.total).toBeGreaterThan(0);
  expect(expected.total).toBeLessThan(all.total);

  await page.goto(
    `/app/w/${workspace}/participants?event=${event}&section=ProjectsGrid`,
  );
  await settled(page);
  await expect(grid(page).locator("tbody tr").first()).toBeVisible();
  await openTools(page);
  await grid(page).getByRole("button", { name: "Add condition" }).click();
  await grid(page)
    .getByLabel("Field of condition 1")
    .selectOption({ label: "Track" });
  await grid(page).getByLabel("Value of condition 1").fill(track);
  const active = grid(page).getByRole("group", { name: "Active filter" });
  await expect(active).toContainText(`Filter: Track is ${track}`);
  await expect(grid(page)).toContainText(`of ${expected.total}`);
  expect(page.url()).not.toContain(track); // typed values are not in the address

  // a value the server refuses is said beside its condition and the rows stay
  const rows = await grid(page).locator("tbody tr").count();
  await grid(page)
    .getByLabel("Field of condition 1")
    .selectOption({ label: "Created" });
  await grid(page)
    .getByLabel("Operator of condition 1")
    .selectOption({ label: "after or more than" });
  await grid(page).getByLabel("Value of condition 1").fill("not-a-date");
  const problem = grid(page).locator("[role=alert].cx-filter-problem");
  await expect(problem).toContainText("Condition 1:");
  await expect(grid(page).getByLabel("Value of condition 1")).toHaveAttribute(
    "aria-invalid",
    "true",
  );
  await expect(active).toContainText("could not be applied");
  expect(await grid(page).locator("tbody tr").count()).toBe(rows);
  await accessible(page);

  await active.getByRole("button", { name: "Clear filter" }).click();
  await expect(active).toHaveCount(0);
  await expect(grid(page)).toContainText(`of ${all.total}`);
});
