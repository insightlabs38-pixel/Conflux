import { expect, test } from "@playwright/test";
import {
  accessible,
  goToDestination,
  noHorizontalOverflow,
  openWorkspace,
  settled,
  signIn,
  watch,
} from "./support";

// Runs after the participant lifecycle (a submitted project exists) and before
// judges submit, so the unscored scoring layout can be inspected. It never
// submits a ballot.
for (const width of [390, 768, 1024, 1440]) {
  test(`judge desk at ${width}px: progress, route, evidence and scoring`, async ({
    page,
  }, info) => {
    test.skip(
      info.project.name !== "desktop",
      "explicit viewport matrix runs once",
    );
    await page.setViewportSize({ width, height: 960 });
    await signIn(page, "judge-03");
    const problems = watch(page);
    await openWorkspace(page);
    const main = page.getByRole("region", { name: "Judging" });
    await main.getByLabel("Event").selectOption({ index: 1 });
    await main.getByLabel("Stage").selectOption({ index: 1 });
    const summary = page.getByRole("region", { name: "Your judging summary" });
    await expect(summary).toContainText("remaining");
    await expect(summary.getByText("Recused")).toBeVisible();
    await settled(page);
    await accessible(page);
    await noHorizontalOverflow(page);
    await page.screenshot({
      path: `tests/e2e/artifacts/uiv2-b07-overview-${width}.png`,
      fullPage: true,
    });

    await goToDestination(page, "schedule");
    await expect(
      page.getByRole("region", { name: "Your judging route" }),
    ).toBeVisible();
    await accessible(page);
    await noHorizontalOverflow(page);

    await goToDestination(page, "queue");
    await expect(
      page.getByRole("region", { name: "Your assignments" }),
    ).toBeVisible();
    await page
      .getByRole("list", { name: "Assigned projects" })
      .getByRole("button")
      .first()
      .click();
    await expect(
      page.getByRole("region", { name: "Submitted artifacts" }),
    ).toBeVisible();
    await expect(page.getByText(/Project 1 of \d+/)).toBeVisible();
    await expect(
      page.getByRole("button", { name: "Recuse or report a conflict" }),
    ).toBeVisible();
    await expect(
      page.getByRole("button", { name: "Submit and continue" }),
    ).toBeVisible();
    await settled(page);
    await accessible(page);
    await noHorizontalOverflow(page);
    await page.screenshot({
      path: `tests/e2e/artifacts/uiv2-b07-scoring-${width}.png`,
      fullPage: true,
    });
    // Keyboard: the score fields are reachable and take input.
    const first = page.getByLabel("Score").first();
    await first.focus();
    await page.keyboard.type("7");
    await expect(first).toHaveValue("7");
    expect(problems.filter((p) => !p.includes("/accounts/me/"))).toEqual([]);
  });
}
