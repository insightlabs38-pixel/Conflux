import { expect, test } from "@playwright/test";
import {
  accessible,
  goToDestination,
  goToTask,
  noHorizontalOverflow,
  openWorkspace,
  settled,
  signIn,
  watch,
} from "./support";

for (const width of [390, 768, 1024, 1440]) {
  test(`participant task flow at ${width}px retains drafts and signed evidence`, async ({
    page,
  }, info) => {
    test.skip(
      info.project.name !== "desktop",
      "explicit viewport matrix runs once",
    );
    await page.setViewportSize({ width, height: 960 });
    await signIn(page, "participant-01");
    const problems = watch(page);
    await openWorkspace(page);
    await page
      .getByRole("combobox", { name: "Event", exact: true })
      .selectOption({ index: 1 });
    await expect(
      page.getByRole("region", { name: "Participant overview" }),
    ).toBeVisible();
    await settled(page);
    await accessible(page);
    await noHorizontalOverflow(page);
    await page.screenshot({
      path: `tests/e2e/artifacts/uiv2-b06-overview-${width}.png`,
      fullPage: true,
    });
    await goToDestination(page, "team");
    await goToTask(page, "Find teammates");
    await accessible(page);
    await noHorizontalOverflow(page);
    await goToTask(page, "Your team");
    await goToDestination(page, "resources");
    for (const task of [
      "Rules",
      "Sponsor challenges",
      "On-site participation",
    ]) {
      await goToTask(page, task);
      await settled(page);
      await accessible(page);
      await noHorizontalOverflow(page);
    }
    await goToDestination(page, "project");
    await page
      .getByRole("combobox", { name: "Project", exact: true })
      .selectOption({ index: 1 });
    const story = page.getByLabel("Project description", { exact: true });
    await story.fill("A draft that survives task navigation.");
    await goToTask(page, "Evidence & checks");
    await accessible(page);
    await noHorizontalOverflow(page);
    await goToTask(page, "Project story");
    await expect(story).toHaveValue("A draft that survives task navigation.");
    const current = page.getByRole("tab", { name: /^Project story/ });
    await current.focus();
    await page.keyboard.press("ArrowDown");
    await page.keyboard.press("Enter");
    await expect(
      page.getByRole("tab", { name: /^Evidence & checks/ }),
    ).toHaveAttribute("aria-selected", "true");
    for (const task of [
      "Event forms",
      "Eligibility",
      "Support",
      "After the event",
      "Submission",
    ]) {
      await goToTask(page, task);
      await settled(page);
      await accessible(page);
      await noHorizontalOverflow(page);
    }
    await page
      .getByRole("region", { name: "Submission", exact: true })
      .getByRole("combobox", { name: "Stage", exact: true })
      .selectOption({ index: 1 });
    await expect(
      page.getByText("Signed submission receipt", { exact: true }),
    ).toBeVisible();
    await expect(page.locator(".cx-human-receipt")).toContainText("Version 1");
    const proof = page.getByText("Signature and technical proof", {
      exact: true,
    });
    await proof.focus();
    await page.keyboard.press("Enter");
    await expect(
      page.getByRole("textbox", { name: "Receipt token", exact: true }),
    ).toBeVisible();
    await accessible(page);
    await noHorizontalOverflow(page);
    await proof.click();
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.screenshot({
      path: `tests/e2e/artifacts/uiv2-b06-receipt-${width}.png`,
      fullPage: true,
    });
    expect(problems).toEqual([]);
  });
}
