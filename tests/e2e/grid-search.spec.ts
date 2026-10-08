import { expect, test, type Page } from "@playwright/test";
import { accessible, eventIds, settled, signIn } from "./support";

// PD-F006-B01-T02: free-text search on a list. The server matches every word in any search field;
// the text is typed text, so it is never in the URL or storage. Read-only on the reference event.
const grid = (page: Page) =>
  page.locator('.cx-entity-grid[data-entity="projects"]');

test("a search narrows the list as the server does, says how many, and stays out of the address", async ({
  page,
}) => {
  await signIn(page, "organizer");
  const { workspace, event } = await eventIds(page);
  const api = `/api/v1/workspaces/${workspace}/events/${event}/entities/projects/`;
  const all = await (await page.request.get(`${api}?sort=name`)).json();
  expect(all.total).toBeGreaterThan(3);
  const word = String(all.rows[0].name).split(" ")[0].toLowerCase();
  const expected = await (
    await page.request.get(`${api}?search=${encodeURIComponent(word)}`)
  ).json();
  expect(expected.total).toBeGreaterThan(0);

  const url = `/app/w/${workspace}/participants?event=${event}&section=ProjectsGrid`;
  await page.goto(url);
  await settled(page);
  await expect(grid(page).locator("tbody tr").first()).toBeVisible();
  const box = grid(page).getByRole("searchbox", { name: /Search projects/ });
  await expect(box).toBeVisible();

  await box.fill("a"); // one letter is not asked for
  await expect(grid(page)).toContainText("at least 2 characters");

  await box.fill(word);
  await expect(
    grid(page).getByRole("status").filter({ hasText: "for “" }),
  ).toContainText(
    `${expected.total.toLocaleString("en-US")} ${expected.total === 1 ? "result" : "results"}`,
  );
  expect(page.url()).not.toContain(word); // typed text is not in the address
  await accessible(page);

  await box.fill("zzzqqqxxx");
  await expect(grid(page)).toContainText("0 results");
  await box.fill("");
  await expect(grid(page).locator("tbody tr").first()).toBeVisible();
  await expect(grid(page)).not.toContainText("results for");
});
