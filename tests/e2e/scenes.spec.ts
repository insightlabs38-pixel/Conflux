import { test } from "@playwright/test";
import path from "node:path";
import { eventIds, openWorkspace, settled, signIn } from "./support";

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
  ]) {
    await page.goto(path);
    await settled(page);
    await page.screenshot({ path: shot(name), fullPage: true });
  }
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
    await page.screenshot({ path: shot(`${n}-workspace`), fullPage: true });
  });
}
