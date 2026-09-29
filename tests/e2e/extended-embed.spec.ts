import { expect, test } from "@playwright/test";
import path from "node:path";
import { eventIds, signIn } from "./support";

test("embed renders the live public API gallery", async ({ page }) => {
  await signIn(page, "organizer");
  const { event } = await eventIds(page);
  await page.context().clearCookies();
  await page.route("**/__conflux_embed_evidence", (route) =>
    route.fulfill({
      contentType: "text/html",
      body: `<!doctype html><html><body><conflux-gallery event="${event}"></conflux-gallery></body></html>`,
    }),
  );
  await page.goto("/__conflux_embed_evidence");
  const response = page.waitForResponse((r) =>
    r.url().includes(`/events/${event}/gallery/`),
  );
  await page.addScriptTag({
    path: path.resolve(__dirname, "../../src/embed/dist/conflux-gallery.js"),
  });
  expect((await response).status()).toBe(200);
  await expect(page.locator("conflux-gallery .card").first()).toBeVisible();
  await expect(page.locator("conflux-gallery")).not.toContainText("could not");
});
