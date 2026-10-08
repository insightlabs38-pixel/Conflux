import { expect, test, type Page } from "@playwright/test";
import { accessible, eventIds, settled, signIn } from "./support";

// PD-F006-B02-T04, T05 and T06: a private saved view end to end - save, change, Reset, save the
// change, a refused duplicate name, share with organizers, pin - and delete. It writes views, so it
// runs on an isolated fixture.
const grid = (page: Page) =>
  page.locator('.cx-entity-grid[data-entity="projects"]');

test.skip(({ isMobile }) => isMobile, "writes views; one viewport is enough");

test("a saved view is private until shared, shows when the list differs, resets, keeps its change, refuses a duplicate name and can be pinned", async ({
  page,
}) => {
  await signIn(page, "organizer");
  const { workspace, event } = await eventIds(page);
  const api = `/api/v1/workspaces/${workspace}/events/${event}`;
  await page.goto(
    `/app/w/${workspace}/participants?event=${event}&section=ProjectsGrid`,
  );
  await settled(page);
  await expect(grid(page).locator("tbody tr").first()).toBeVisible();
  const header = (name: string) =>
    grid(page)
      .locator("thead th")
      .filter({ hasText: new RegExp(`^${name}`) });
  const tools = grid(page).locator(".cx-entity-grid__tools");
  if (!(await tools.evaluate((el) => (el as HTMLDetailsElement).open)))
    await tools.locator("summary").click();
  const views = grid(page).getByRole("group", { name: "Saved views" });
  const name = `Flow ${Date.now()}`;

  // save the list as it is, sorted by project
  await grid(page)
    .getByLabel("Sort by")
    .selectOption({ label: "Project, ascending" });
  await views.getByRole("button", { name: "Save as new view" }).click();
  await views.getByLabel("Name").fill(name);
  await views.getByRole("button", { name: "Save view" }).click();
  await expect(views).toContainText("View saved.");
  await expect(views).toContainText("Private to you.");
  expect(
    (await (await page.request.get(`${api}/views/?entity=projects`)).json())[0]
      .visibility,
  ).toBe("private");
  await expect(views.getByRole("button", { name: "Reset" })).toHaveCount(0); // nothing differs

  // change the list: it says so, and Reset goes back to the saved order
  await grid(page)
    .getByLabel("Sort by")
    .selectOption({ label: "Team, descending" });
  await expect(views).toContainText("Changed since saved");
  await views.getByRole("button", { name: "Reset" }).click();
  await expect(views).not.toContainText("Changed since saved");
  await expect(header("Project")).toHaveAttribute("aria-sort", "ascending");

  // change it again and keep the change: a reload shows the new order
  await grid(page)
    .getByLabel("Sort by")
    .selectOption({ label: "Team, descending" });
  await views.getByRole("button", { name: "Save", exact: true }).click();
  await expect(views).toContainText("View saved.");
  await page.reload();
  await settled(page);
  await expect(header("Team")).toHaveAttribute("aria-sort", "descending");

  // a second view with the same name is refused in words and nothing is lost
  await tools
    .locator("summary")
    .click()
    .catch(() => {});
  if (!(await tools.evaluate((el) => (el as HTMLDetailsElement).open)))
    await tools.locator("summary").click();
  await views.getByRole("button", { name: "Save as new view" }).click();
  await views.getByLabel("Name").fill(name);
  await views.getByRole("button", { name: "Save view" }).click();
  await expect(views.getByRole("alert")).toContainText(
    "already have a view with this name",
  );
  await views.getByRole("button", { name: "Cancel" }).click();

  // share with organizers, then pin it: pinned views are listed first
  await views.getByLabel("Shared with organizers").click(); // the box follows the server answer
  await expect(views).toContainText("Visible to every organizer.");
  await expect
    .poll(
      async () =>
        (
          await (await page.request.get(`${api}/views/?entity=projects`)).json()
        )[0].visibility,
    )
    .toBe("organizers");
  await views.getByRole("button", { name: "Pin view" }).click();
  const groups = await views
    .getByRole("combobox")
    .locator("optgroup")
    .evaluateAll((els) => els.map((e) => e.getAttribute("label")));
  expect(groups[0]).toBe("Pinned");
  await accessible(page);

  // delete it with its consequence stated
  await views.getByRole("button", { name: "Delete view" }).click();
  await grid(page)
    .getByRole("button", { name: new RegExp(`^Delete “${name}”`) })
    .click();
  await expect(views).toContainText("View deleted.");
  expect(
    await (await page.request.get(`${api}/views/?entity=projects`)).json(),
  ).toHaveLength(0);
});
