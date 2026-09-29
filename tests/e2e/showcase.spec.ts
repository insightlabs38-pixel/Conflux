import { expect, test } from "@playwright/test";
import {
  accessible,
  eventIds,
  noHorizontalOverflow,
  signIn,
  watch,
} from "./support";

let event = "";
test.beforeAll(async ({ browser }) => {
  const page = await browser.newPage();
  await signIn(page, "organizer");
  event = (await eventIds(page)).event;
  await page.close();
});

test("showcase browsing preserves search, clear filters, project evidence and public identity", async ({
  page,
}) => {
  const problems = watch(page);
  await page.goto(`/e/${event}/gallery/`);
  const cards = page.locator(".cx-project-card");
  await expect(cards.first()).toBeVisible();
  const title = await cards.first().getByRole("heading").innerText();
  await page.getByRole("searchbox").fill(title);
  await page.getByRole("button", { name: "Search", exact: true }).click();
  await expect(page.getByRole("status")).toContainText("Filters active");
  await expect(cards.first().getByRole("heading")).toHaveText(title);
  await accessible(page);
  await cards.first().getByRole("heading").getByRole("link").click();
  await expect(page.getByRole("heading", { level: 1 })).toHaveText(title);
  await expect(
    page.getByRole("heading", { name: "About the project", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Submission evidence", exact: true }),
  ).toBeVisible();
  const evidence = page
    .getByText("Version and integrity reference", { exact: true })
    .first();
  await evidence.focus();
  await page.keyboard.press("Enter");
  await expect(
    page.locator(".cx-submission-proof details").first(),
  ).toHaveAttribute("open", "");
  await accessible(page);
  await noHorizontalOverflow(page);
  await page
    .getByRole("link", { name: "Back to gallery", exact: true })
    .click();
  await page.getByRole("searchbox").fill("not-a-real-project-91732");
  await page.getByRole("button", { name: "Search", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "No projects match yet." }),
  ).toBeVisible();
  await page.getByRole("link", { name: "Clear filters", exact: true }).click();
  await expect(cards.first()).toBeVisible();
  expect(problems).toEqual([]);
});

for (const width of [360, 768, 1024, 1440, 1920]) {
  test(`public showcase at ${width}px: gallery, detail and award hierarchy`, async ({
    page,
  }, info) => {
    test.skip(
      info.project.name === "mobile",
      "explicit viewport matrix runs once",
    );
    await page.setViewportSize({ width, height: 960 });
    await page.goto(`/e/${event}/gallery/`);
    await accessible(page);
    await noHorizontalOverflow(page);
    await page.screenshot({
      path: `tests/e2e/artifacts/uiv2-b05-gallery-${width}.png`,
      fullPage: true,
    });
    await page
      .locator(".cx-project-card")
      .first()
      .getByRole("heading")
      .getByRole("link")
      .click();
    await accessible(page);
    await noHorizontalOverflow(page);
    await page.screenshot({
      path: `tests/e2e/artifacts/uiv2-b05-project-${width}.png`,
      fullPage: true,
    });
    await page.goto(`/e/${event}/results/`);
    await expect(page.getByRole("heading", { level: 1 })).toHaveText(
      "Published results",
    );
    await accessible(page);
    await noHorizontalOverflow(page);
    await page.screenshot({
      path: `tests/e2e/artifacts/uiv2-b05-results-${width}.png`,
      fullPage: true,
    });
    const award = page.locator(".cx-award-section").first();
    if (await award.count()) {
      await award.getByRole("heading", { level: 2 }).getByRole("link").click();
      await accessible(page);
      const winner = page.locator(".cx-project-card").first();
      if (await winner.count()) {
        await winner.getByRole("heading").getByRole("link").click();
        await expect(
          page.getByRole("link", { name: "View project and public artifacts" }),
        ).toBeVisible();
        await accessible(page);
      }
    }
  });
}
