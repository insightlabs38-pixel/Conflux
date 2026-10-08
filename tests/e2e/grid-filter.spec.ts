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

  // a value the server refuses is said beside its condition and the rows stay (more than 50 in a list)
  const rows = await grid(page).locator("tbody tr").count();
  await grid(page)
    .getByLabel("Field of condition 1")
    .selectOption({ label: "Project" });
  await grid(page)
    .getByLabel("Operator of condition 1")
    .selectOption({ label: "is one of" });
  await grid(page)
    .getByLabel("Value of condition 1")
    .fill(Array.from({ length: 51 }, (_, i) => `p${i}`).join(","));
  const problem = grid(page).locator("[role=alert].cx-filter-problem");
  await expect(problem).toContainText("Condition 1:");
  await expect(problem).toContainText("At most 50 values");
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

test("conditions nest in groups, read back as one sentence, and match what the API returns for the same tree", async ({
  page,
}) => {
  await signIn(page, "organizer");
  const { workspace, event } = await eventIds(page);
  const api = `/api/v1/workspaces/${workspace}/events/${event}/entities/projects/`;
  const all = await (await page.request.get(`${api}?sort=name`)).json();
  const track = String(
    all.rows.find((r: { track?: string }) => r.track)?.track,
  );
  const tree = {
    and: [
      { field: "track", op: "eq", value: track },
      {
        or: [
          { field: "name", op: "contains", value: "a" },
          { field: "name", op: "contains", value: "e" },
        ],
      },
    ],
  };
  const expected = await (
    await page.request.get(
      `${api}?filter=${encodeURIComponent(JSON.stringify(tree))}`,
    )
  ).json();

  await page.goto(
    `/app/w/${workspace}/participants?event=${event}&section=ProjectsGrid`,
  );
  await settled(page);
  await expect(grid(page).locator("tbody tr").first()).toBeVisible();
  await openTools(page);
  const g = grid(page);
  await g.getByRole("button", { name: "Add condition", exact: true }).click();
  await g.getByLabel("Field of condition 1").selectOption({ label: "Track" });
  await g.getByLabel("Value of condition 1").fill(track);
  await g.getByRole("button", { name: "Add group", exact: true }).click();
  await g.getByLabel("Field of condition 2").selectOption({ label: "Project" });
  await g
    .getByLabel("Operator of condition 2")
    .selectOption({ label: "contains" });
  await g.getByLabel("Value of condition 2").fill("a");
  await g.getByRole("button", { name: "Add condition to group 1" }).click();
  await g.getByLabel("Field of condition 3").selectOption({ label: "Project" });
  await g
    .getByLabel("Operator of condition 3")
    .selectOption({ label: "contains" });
  await g.getByLabel("Value of condition 3").fill("e");

  const active = g.getByRole("group", { name: "Active filter" });
  await expect(active).toContainText(
    `Track is ${track} and (Project contains a or Project contains e)`,
  );
  await expect(g).toContainText(
    expected.total === 0
      ? "Showing 0 of 0"
      : `of ${expected.total.toLocaleString("en-US")}`,
  );
  await expect(g.getByText("Group 1 (match any of these)")).toBeVisible();
  await accessible(page);

  // removing the group leaves the plain condition
  await g.getByRole("button", { name: "Remove group 1" }).click();
  await expect(active).toContainText(`Filter: Track is ${track}`);
  await expect(active).not.toContainText("(");
});

test("a date is chosen in a date box with date words, a range is two boxes, and the sentence says what it means", async ({
  page,
}) => {
  await signIn(page, "organizer");
  const { workspace, event } = await eventIds(page);
  const api = `/api/v1/workspaces/${workspace}/events/${event}/entities/projects/`;
  const tree = {
    field: "created_at",
    op: "between",
    value: ["2026-01-01", "2026-12-31"],
  };
  const expected = await (
    await page.request.get(
      `${api}?filter=${encodeURIComponent(JSON.stringify(tree))}`,
    )
  ).json();
  await page.goto(
    `/app/w/${workspace}/participants?event=${event}&section=ProjectsGrid`,
  );
  await settled(page);
  await expect(grid(page).locator("tbody tr").first()).toBeVisible();
  await openTools(page);
  const g = grid(page);
  await g.getByRole("button", { name: "Add condition", exact: true }).click();
  await g.getByLabel("Field of condition 1").selectOption({ label: "Created" });
  const operators = await g
    .getByLabel("Operator of condition 1")
    .locator("option")
    .allInnerTexts();
  expect(operators).toEqual([
    "before",
    "on or before",
    "after",
    "on or after",
    "between",
    "is empty",
  ]);
  await g
    .getByLabel("Operator of condition 1")
    .selectOption({ label: "between" });
  await expect(g.getByLabel("Start of condition 1")).toHaveAttribute(
    "type",
    "date",
  );
  await g.getByLabel("Start of condition 1").fill("2026-01-01");
  await g.getByLabel("End of condition 1").fill("2026-12-31");
  await expect(g.getByRole("group", { name: "Active filter" })).toContainText(
    "Created between 2026-01-01 and 2026-12-31",
  );
  await expect(g).toContainText(
    expected.total === 0
      ? "Showing 0 of 0"
      : `of ${expected.total.toLocaleString("en-US")}`,
  );
  await accessible(page);
});
