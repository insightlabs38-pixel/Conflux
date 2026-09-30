import { expect, test } from "@playwright/test";
import {
  accessible,
  eventIds,
  goToTask,
  noHorizontalOverflow,
  openWorkspace,
  settled,
  signIn,
} from "./support";

// The dense data grid over the universal entity query, with saved views (PD-F002-B01-T01..T03):
// the organizer's applications and projects lists sort, filter, hide columns, change density and
// keep a saved view that a link reopens. Everything is asked of the server. Saved views are
// written, so this runs on an isolated fixture.
for (const width of [390, 1440]) {
  test(`applications and projects are a filterable grid with saved views at ${width}`, async ({
    page,
  }, info) => {
    test.skip(info.project.name !== "desktop", "explicit viewport matrix");
    await page.setViewportSize({ width, height: 900 });
    const viewName = `Starts with A ${width}`;
    await signIn(page, "organizer");
    await openWorkspace(page);
    const { workspace, event } = await eventIds(page);
    const api = `/api/v1/workspaces/${workspace}/events/${event}`;
    const everyone = await (
      await page.request.get(`${api}/entities/applications/`)
    ).json();
    expect(everyone.total).toBeGreaterThan(2);
    const names: string[] = everyone.rows.map(
      (row: { username: string }) => row.username,
    );

    await page.goto(`/app/w/${workspace}/participants?event=${event}`);
    await settled(page);
    await goToTask(page, "Registration");
    const panel = page.locator('[data-entity="applications"]');
    const grid = panel.getByRole("region", { name: "Applications" });
    await expect(grid.locator("tbody tr")).toHaveCount(everyone.total);
    await noHorizontalOverflow(page);

    // Sort is asked of the server. Wide screens sort from the header; the stacked narrow layout has
    // no header, so the same choice is offered as "Sort by" in the tools.
    const ascending = [...names].sort();
    const firstApplicant = () =>
      grid.locator("tbody tr").first().locator("td").nth(0);
    await panel.getByText("Filter, views and columns").click();
    if (width >= 768) {
      const applicant = grid.getByRole("columnheader", { name: /Applicant/ });
      await applicant.getByRole("button").click();
      await expect(applicant).toHaveAttribute("aria-sort", "ascending");
      await expect(firstApplicant()).toContainText(ascending[0]);
      await applicant.getByRole("button").press("Enter");
      await expect(applicant).toHaveAttribute("aria-sort", "descending");
      await expect(firstApplicant()).toContainText(
        ascending[ascending.length - 1],
      );
    } else {
      await panel.getByLabel("Sort by").selectOption("username");
      await expect(firstApplicant()).toContainText(ascending[0]);
      await panel.getByLabel("Sort by").selectOption("-username");
      await expect(firstApplicant()).toContainText(
        ascending[ascending.length - 1],
      );
    }

    // Filter: one condition narrows the list; clearing it restores it.
    const section = page
      .getByRole("region", { name: "Applications" })
      .locator("..");
    const tools = panel.getByRole("group", { name: "Filter" });
    await tools.getByRole("button", { name: "Add condition" }).click();
    await tools.getByLabel("Field of condition 1").selectOption("username");
    await tools.getByLabel("Operator of condition 1").selectOption("eq");
    await tools.getByLabel("Value of condition 1").fill(ascending[0]);
    await expect(grid.locator("tbody tr")).toHaveCount(1);
    await expect(panel.getByText("(filtered)")).toBeVisible();
    await tools.getByLabel("Value of condition 1").fill("nobody-by-this-name");
    await expect(panel.getByText("No rows match this filter")).toBeVisible();
    await panel
      .locator(".cx-state")
      .getByRole("button", { name: "Clear filter" })
      .click();
    await expect(grid.locator("tbody tr")).toHaveCount(everyone.total);

    // Columns and density are the viewer's choice.
    const columns = page
      .getByRole("group", { name: "Columns" })
      .or(page.locator("fieldset", { hasText: "Columns" }));
    await columns.getByLabel("Note").uncheck();
    await expect(grid.getByRole("columnheader", { name: "Note" })).toHaveCount(
      0,
    );
    await panel.getByRole("button", { name: "Compact" }).click();
    await expect(panel.locator(".cx-grid-wrap--compact")).toBeVisible();
    await panel.getByRole("button", { name: "Comfortable" }).click();

    // A saved view keeps the filter; a link to it reopens it.
    await tools.getByRole("button", { name: "Add condition" }).click();
    await tools.getByLabel("Field of condition 1").selectOption("username");
    await tools
      .getByLabel("Operator of condition 1")
      .selectOption("startswith");
    await tools
      .getByLabel("Value of condition 1")
      .fill(ascending[0].slice(0, 4));
    const views = panel.getByRole("group", { name: "Saved views" });
    await views.getByRole("button", { name: "Save as new view" }).click();
    await views.getByLabel("Name").fill(viewName);
    await views.getByRole("button", { name: "Save view" }).click();
    await expect(views.getByRole("status").last()).toContainText("View saved.");
    await expect(page).toHaveURL(/[?&]view_applications=[0-9a-f-]{36}/);
    const link = page.url();
    await accessible(page);

    await page.goto(link);
    await settled(page);
    await goToTask(page, "Registration");
    await expect(grid.locator("tbody tr").first()).toBeVisible();
    await panel.getByText("Filter, views and columns").click();
    await expect(
      panel.getByRole("group", { name: "Saved views" }).getByRole("combobox"),
    ).toHaveValue(/[0-9a-f-]{36}/);

    // Changing the list after opening a view says so; the view is per person until shared.
    const again = panel.getByRole("group", { name: "Filter" });
    await again.getByLabel("Value of condition 1").fill("zzzz");
    await expect(panel.getByText("Changed since saved")).toBeVisible();
    const saved = await (
      await page.request.get(`${api}/views/?entity=applications`)
    ).json();
    expect(saved).toHaveLength(1);
    expect(saved[0].name).toBe(viewName);

    // A view nobody can see falls back to the default list instead of failing.
    await page.goto(
      `/app/w/${workspace}/participants?event=${event}&view_applications=00000000-0000-4000-8000-000000000000`,
    );
    await settled(page);
    await goToTask(page, "Registration");
    await panel.getByText("Filter, views and columns").click();
    await expect(
      panel.getByRole("group", { name: "Saved views" }).getByRole("combobox"),
    ).toHaveValue("");

    // Delete it with its consequence stated.
    await panel
      .getByRole("group", { name: "Saved views" })
      .getByRole("combobox")
      .selectOption({ label: viewName });
    await panel.getByRole("button", { name: "Delete view" }).click();
    await expect(panel.getByRole("alertdialog")).toContainText(
      "The data it shows is not touched.",
    );
    await panel
      .getByRole("button", { name: new RegExp(`^Delete “${viewName}”`) })
      .click();
    await expect(panel.getByText("View deleted.")).toBeVisible();
    expect(
      await (
        await page.request.get(`${api}/views/?entity=applications`)
      ).json(),
    ).toHaveLength(0);

    // The same grid lists projects.
    await goToTask(page, "Projects");
    const projects = page
      .locator('[data-entity="projects"]')
      .getByRole("region", { name: "Projects" });
    const total = (
      await (await page.request.get(`${api}/entities/projects/`)).json()
    ).total;
    await expect(projects.locator("tbody tr")).toHaveCount(total);
    await noHorizontalOverflow(page);
    await accessible(page);
  });
}
