import { expect, test, type Page } from "@playwright/test";
import { eventIds, settled, signIn } from "./support";

// PD-F005-B03-T06: route/view state is serializable enough to link to an exact operational context.
// A list's sort and page are panel state in the URL, a link reproduces them, and "Copy link to this
// view" copies exactly that address - without the invite token or typed text. Read-only.
test.use({ permissions: ["clipboard-read", "clipboard-write"] });

const grid = (page: Page) =>
  page.locator('.cx-entity-grid[data-entity="projects"]');

async function openTools(page: Page) {
  const tools = grid(page).locator(".cx-entity-grid__tools");
  if (!(await tools.evaluate((el) => (el as HTMLDetailsElement).open)))
    await tools.locator("summary").click();
}

test("a link with a sort reproduces the list, an unknown sort is ignored, and Copy link copies the clean address", async ({
  page,
}) => {
  await signIn(page, "organizer");
  const { workspace, event } = await eventIds(page);
  const path = `/app/w/${workspace}/participants`;
  await page.goto(
    `${path}?event=${event}&section=ProjectsGrid&sort_projects=-name&invite=SECRET&q=ada`,
  );
  await settled(page);
  await expect(grid(page).locator("tbody tr").first()).toBeVisible();
  await openTools(page);
  await expect(grid(page).getByLabel("Sort by")).toHaveValue("-name");

  // the palette copies the exact context, minus the credential and the typed text
  await page.locator("main").focus();
  await page.keyboard.press("Control+k");
  await page.getByRole("dialog").getByRole("combobox").fill("copy link");
  await expect(
    page.getByRole("option", { name: "Copy link to this view" }),
  ).toBeVisible();
  await page.keyboard.press("Enter");
  await expect(page.locator(".cx-notice")).toHaveText("Link copied.");
  const copied = await page.evaluate(() => navigator.clipboard.readText());
  const url = new URL(copied);
  expect(url.pathname).toBe(path);
  expect(url.searchParams.get("event")).toBe(event);
  expect(url.searchParams.get("sort_projects")).toBe("-name");
  expect(url.searchParams.get("section")).toBe("ProjectsGrid");
  expect(copied).not.toContain("SECRET");
  expect(copied).not.toContain("ada");

  // opening the copied link shows the same list
  await page.goto(copied);
  await settled(page);
  await openTools(page);
  await expect(grid(page).getByLabel("Sort by")).toHaveValue("-name");

  // a sort this list cannot honour is ignored, not an error
  await page.goto(
    `${path}?event=${event}&section=ProjectsGrid&sort_projects=nonsense`,
  );
  await settled(page);
  await expect(grid(page).locator("tbody tr").first()).toBeVisible();
  await openTools(page);
  await expect(grid(page).getByLabel("Sort by")).toHaveValue("");
});
