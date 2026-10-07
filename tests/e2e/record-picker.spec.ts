import { expect, test } from "@playwright/test";
import {
  chooseWorkspaceEvent,
  goToDestination,
  goToTask,
  openWorkspace,
  settled,
  signIn,
} from "./support";

// PD-F004-B05-T05: a record is chosen by name, never typed as an id (read-only on the reference event).
for (const width of [1440, 390]) {
  test(`the policy check picks a project by name at ${width}`, async ({
    page,
  }, info) => {
    test.skip(info.project.name !== "desktop", "explicit viewport matrix");
    await page.setViewportSize({ width, height: 900 });
    await signIn(page, "organizer");
    await openWorkspace(page);
    await chooseWorkspaceEvent(page);
    await settled(page);
    await goToDestination(page, "setup");
    await goToTask(page, "Policies");
    await settled(page);
    const picker = page.getByRole("combobox", {
      name: "Project for grant check",
    });
    await expect(picker.locator("option")).not.toHaveCount(1);
    const names = await picker.locator("option").allTextContents();
    expect(names[0]).toMatch(/^Choose a project/);
    expect(names[1]).not.toMatch(/^[0-9a-f]{8}-/); // a name, not an id
    await picker.selectOption({ index: 1 });
    await page.getByRole("button", { name: "Check policy" }).click();
    await expect(page.getByLabel("Policy debug result")).toBeVisible();
  });
}
