import { expect, test } from "@playwright/test";
import {
  accessible,
  chooseWorkspaceEvent,
  goToDestination,
  goToTask,
  noHorizontalOverflow,
  openWorkspace,
  settled,
  signIn,
  watch,
} from "./support";

// Read-only tour of secondary/developer/builder surfaces (UIV2-B09).
for (const width of [390, 768, 1024, 1440]) {
  test(`developer and builder surfaces at ${width}px`, async ({
    page,
  }, info) => {
    test.skip(
      info.project.name !== "desktop",
      "explicit viewport matrix runs once",
    );
    await page.setViewportSize({ width, height: 960 });
    await signIn(page, "organizer");
    const problems = watch(page);

    await page.goto("/app/?api=explorer");
    await expect(
      page.getByRole("heading", { name: "API explorer" }),
    ).toBeVisible();
    await page.getByRole("button", { name: "Check service health" }).click();
    await expect(page.locator(".cx-api-endpoint")).toBeVisible();
    await page.getByRole("button", { name: "Send request" }).click();
    await expect(
      page.getByRole("region", { name: "API response" }),
    ).toBeVisible();
    await settled(page);
    await accessible(page);
    await noHorizontalOverflow(page);
    await page.screenshot({
      path: `tests/e2e/artifacts/uiv2-b09-api-${width}.png`,
      fullPage: true,
    });

    await page.goto("/app/");
    await openWorkspace(page);
    await chooseWorkspaceEvent(page);
    await goToDestination(page, "setup");
    for (const task of [
      "Settings",
      "Stages",
      "Policies",
      "Rules",
      "Forms",
      "Public page",
    ]) {
      await goToTask(page, task);
      await settled(page);
      await accessible(page);
      await noHorizontalOverflow(page);
      if (task === "Public page")
        await page.screenshot({
          path: `tests/e2e/artifacts/uiv2-b09-page-builder-${width}.png`,
          fullPage: true,
        });
    }
    for (const dest of ["integrations", "communications", "operations"]) {
      await goToDestination(page, dest);
      await settled(page);
      await accessible(page);
      await noHorizontalOverflow(page);
      await page.screenshot({
        path: `tests/e2e/artifacts/uiv2-b09-${dest}-${width}.png`,
        fullPage: true,
      });
    }
    expect(problems.filter((p) => !p.includes("/accounts/me/"))).toEqual([]);
  });
}
