import { chooseWorkspaceEvent } from "./support";
import { expect, test } from "@playwright/test";
import path from "node:path";
import {
  eventIds,
  goToDestination,
  openWorkspace,
  settled,
  signIn,
} from "./support";

// Deterministic demo scenes: fixed viewport, reduced motion, seeded data. Screenshots land in
// tests/e2e/artifacts/scenes; a video of each scene is kept because the config records it on demand.
test.use({ video: "on", screenshot: "off" });
const shot = (name: string) =>
  path.join(__dirname, "artifacts", "scenes", `${name}.png`);

test("scene 01 — public event, gallery and results", async ({ page }) => {
  await signIn(page, "organizer");
  const { event } = await eventIds(page);
  for (const [name, path] of [
    ["01-landing", `/e/${event}/`],
    ["02-gallery", `/e/${event}/gallery/`],
    ["03-results", `/e/${event}/results/`],
    ["07-agenda", `/e/${event}/agenda/`],
    ["08-expo-map", `/e/${event}/map/`],
  ]) {
    await page.goto(path);
    await settled(page);
    await page.screenshot({ path: shot(name), fullPage: true });
  }
  await page.goto(`/e/${event}/gallery/`);
  await page.locator("main a[href*='/projects/']").first().click();
  await settled(page);
  await page.screenshot({ path: shot("public-project"), fullPage: true });
});

for (const [n, role] of [
  ["04-organizer", "organizer"],
  ["05-judge", "judge-01"],
  ["06-participant", "participant-01"],
] as const) {
  test(`scene ${n} workspace`, async ({ page }) => {
    await signIn(page, role);
    await page.screenshot({ path: shot(`${n}-selector`) });
    await openWorkspace(page);
    await settled(page);
    if (role === "organizer") {
      await chooseWorkspaceEvent(page);
      await settled(page);
      await goToDestination(page, "judging");
      const judging = page.locator(".cx-card").filter({
        has: page.getByRole("heading", { name: "Judging", exact: true }),
      });
      await judging.getByLabel("Stage").selectOption({ index: 1 });
      await expect(
        judging.getByText("ballots submitted", { exact: false }),
      ).toBeVisible();
      await settled(page);
      await page
        .getByRole("heading", { name: "Main judging", exact: true })
        .evaluate((heading) => heading.scrollIntoView({ block: "start" }));
      await page.screenshot({ path: shot(`${n}-workspace`) });
      await page
        .getByRole("region", { name: "Judging logistics" })
        .getByLabel("Stage")
        .selectOption({ index: 1 });
      await settled(page);
      for (const [name, region, destination] of [
        [
          "organizer-eligibility-overview",
          "Eligibility review queue",
          "eligibility",
        ],
        [
          "organizer-deliberation-overview",
          "Deliberation and finalization",
          "results",
        ],
        ["organizer-onsite", "On-site operations", "onsite"],
        ["organizer-judging-logistics", "Judging logistics", "judging"],
      ]) {
        await goToDestination(page, destination);
        await page
          .getByRole("region", { name: region })
          .screenshot({ path: shot(name) });
      }
    } else {
      await page
        .locator("select")
        .filter({ has: page.locator("option", { hasText: "Choose an event" }) })
        .first()
        .selectOption({ index: 1 });
      if (role === "judge-01") {
        const judging = page.getByRole("region", { name: "Judging" });
        await judging.getByLabel("Stage").selectOption({ index: 1 });
        await goToDestination(page, "queue");
        await expect(
          page.getByRole("region", { name: "Your assignments" }),
        ).toBeVisible();
        await settled(page);
        await goToDestination(page, "schedule");
        await page
          .getByRole("region", { name: "Your judging route" })
          .screenshot({ path: shot("judge-route") });
        await goToDestination(page, "queue");
      } else {
        await goToDestination(page, "project");
        await page
          .getByRole("region", { name: "My projects" })
          .locator("select")
          .filter({
            has: page.locator("option", { hasText: "Choose a project" }),
          })
          .selectOption({ index: 1 });
      }
      await settled(page);
      await page.screenshot({ path: shot(`${n}-workspace`) });
    }
  });
}

test("scene 09 — API explorer and sign-in", async ({ page }) => {
  await page.goto("/app/");
  await page.screenshot({ path: shot("10-signin") });
  await page.goto("/app/?api=explorer");
  await settled(page);
  await page.screenshot({ path: shot("09-api-explorer"), fullPage: true });
});
