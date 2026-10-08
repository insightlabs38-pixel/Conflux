import { expect, test } from "@playwright/test";
import {
  accessible,
  eventIds,
  noHorizontalOverflow,
  settled,
  signIn,
} from "./support";

// PD-F005-B03-T03: operations mode puts a second pane beside the page on displays 1800px wide or
// more. A device choice, off by default; read-only; it goes away below 1800 and returns above it.
test.skip(({ isMobile }) => isMobile, "sets its own viewport");

test("operations mode shows a second pane only on a wide display, and the page keeps its place", async ({
  page,
}) => {
  await page.setViewportSize({ width: 1920, height: 1080 });
  await signIn(page, "organizer");
  const { workspace, event } = await eventIds(page);
  await page.goto(`/app/w/${workspace}/overview?event=${event}`);
  await settled(page);
  const pane = page.getByRole("complementary", { name: "Operations" });
  await expect(pane).toHaveCount(0); // off by default: nothing changes

  // on, through the account menu
  await page.locator("details.cx-account summary").click();
  await page
    .getByRole("radio", { name: "Second pane beside the page" })
    .check();
  await expect(pane).toBeVisible();
  await page.locator("details.cx-account summary").click(); // close the menu
  await expect(
    pane.getByRole("button", { name: "Needs attention" }),
  ).toHaveAttribute("aria-pressed", "true");
  await expect(pane).toContainText("Live operations");
  await expect(pane).toContainText(/Data as of \d\d:\d\d:\d\d/);
  const main = page.locator("main#main-content");
  const mainBox = await main.boundingBox();
  const paneBox = await pane.boundingBox();
  expect(paneBox!.x).toBeGreaterThanOrEqual(mainBox!.x + mainBox!.width - 1); // beside, not over
  expect(paneBox!.width).toBeLessThanOrEqual(430); // never stretched
  await page.screenshot({
    path: "tests/e2e/artifacts/operations-mode-1920.png",
  });
  await noHorizontalOverflow(page);
  await accessible(page);

  // what it watches is a choice
  await pane.getByRole("button", { name: "Your recent actions" }).click();
  await expect(
    pane.getByRole("button", { name: "Your recent actions" }),
  ).toHaveAttribute("aria-pressed", "true");
  await pane.getByRole("button", { name: "Inbox" }).click();
  await expect(pane.getByRole("button", { name: "Inbox" })).toHaveAttribute(
    "aria-pressed",
    "true",
  );

  // below 1800 the pane is not there at all (not hidden, not fetching), above it returns
  await page.setViewportSize({ width: 1440, height: 900 });
  await expect(pane).toHaveCount(0);
  await noHorizontalOverflow(page);
  await page.setViewportSize({ width: 1920, height: 1080 });
  await expect(pane).toBeVisible();

  // the choice outlives a reload; closing the pane turns it off
  await page.reload();
  await settled(page);
  await expect(pane).toBeVisible();
  await pane.getByRole("button", { name: "Close pane" }).click();
  await expect(pane).toHaveCount(0);
});

test("operations mode is offered and reversible from the palette", async ({
  page,
}) => {
  await page.setViewportSize({ width: 1920, height: 1080 });
  await signIn(page, "organizer");
  const { workspace, event } = await eventIds(page);
  await page.goto(`/app/w/${workspace}/overview?event=${event}`);
  await settled(page);
  const pane = page.getByRole("complementary", { name: "Operations" });
  const run = async (text: string) => {
    await page.locator("main").focus();
    await page.keyboard.press("Control+k");
    await page.getByRole("dialog").getByRole("combobox").fill(text);
    await expect(page.getByRole("option", { name: text })).toBeVisible();
    await page.keyboard.press("Enter");
  };
  await run("Turn on operations mode");
  await expect(pane).toBeVisible();
  await run("Turn off operations mode");
  await expect(pane).toHaveCount(0);
});
