import { expect, test, type Page } from "@playwright/test";
import {
  accessible,
  eventIds,
  noHorizontalOverflow,
  settled,
  signIn,
} from "./support";

// PD-F006-B02-T08: group and subgroup. The server lists the buckets with counts; a bucket opens its
// rows through the ordinary query. Read-only on the reference event.
const grid = (page: Page) =>
  page.locator('.cx-entity-grid[data-entity="projects"]');

async function openTools(page: Page) {
  const tools = grid(page).locator(".cx-entity-grid__tools");
  if (!(await tools.evaluate((el) => (el as HTMLDetailsElement).open)))
    await tools.locator("summary").click();
}

test("rows group by a field and a second inside it, counts equal the server's and a bucket opens its own rows", async ({
  page,
}) => {
  await signIn(page, "organizer");
  const { workspace, event } = await eventIds(page);
  const api = `/api/v1/workspaces/${workspace}/events/${event}/entities/projects/`;
  const buckets = await (await page.request.get(`${api}?group=track`)).json();
  expect(buckets.groups.length).toBeGreaterThan(1);
  const nested = await (
    await page.request.get(`${api}?group=track&subgroup=gallery_visible`)
  ).json();

  await page.goto(
    `/app/w/${workspace}/participants?event=${event}&section=ProjectsGrid`,
  );
  await settled(page);
  await expect(grid(page).locator("tbody tr").first()).toBeVisible();
  await openTools(page);
  await grid(page).getByLabel("Group by").selectOption({ label: "Track" });
  await expect(page).toHaveURL(/group_projects=track/);
  const heads = grid(page).locator(".cx-groups__head");
  await expect(heads).toHaveCount(buckets.groups.length);
  for (const [index, group] of buckets.groups.entries())
    await expect(heads.nth(index)).toHaveText(
      `Track: ${group.label} · ${group.count}`,
    );
  await expect(grid(page).locator("tbody")).toHaveCount(0); // buckets only, until one is opened

  // open the first bucket: its rows are exactly its count (page of 25)
  const first = buckets.groups[0];
  await heads.first().click();
  await expect(heads.first()).toHaveAttribute("aria-expanded", "true");
  await expect(grid(page).locator("tbody tr")).toHaveCount(
    Math.min(first.count, 25),
  );
  await expect(grid(page).locator(".cx-groups__body")).toContainText(
    `of ${first.count}`,
  );
  await noHorizontalOverflow(page);
  await accessible(page);

  // a subgroup nests inside every group
  await grid(page).getByLabel("Then by").selectOption({ label: "In gallery" });
  await expect(page).toHaveURL(/then_projects=gallery_visible/);
  const firstNested = nested.groups[0];
  await grid(page).locator(".cx-groups__head").first().click();
  await expect(grid(page).locator(".cx-groups__head--sub").first()).toHaveText(
    new RegExp(
      `^In gallery: ${firstNested.subgroups[0].label} · ${firstNested.subgroups[0].count}`,
    ),
  );

  // reload keeps the grouping; ungrouping brings the flat list back
  await page.reload();
  await settled(page);
  await expect(grid(page).locator(".cx-groups__head").first()).toBeVisible();
  await openTools(page);
  await grid(page)
    .getByLabel("Group by")
    .selectOption({ label: "No grouping" });
  await expect(grid(page).locator("tbody tr").first()).toBeVisible();
  await expect(page).not.toHaveURL(/group_projects|then_projects/);
});
