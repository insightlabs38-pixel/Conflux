import { expect, test, type Page } from "@playwright/test";
import { eventIds, openWorkspace, settled, signIn } from "./support";

// URL-state conventions (PD-B04-T04; lib/urlState.ts): context (event/stage/plan) lives in the URL
// so refresh, Back and shared links keep it; invalid values fall back without a history entry.
test.skip(({ isMobile }) => isMobile, "URL contract; viewport independent");

const search = (page: Page) => new URL(page.url()).search;

test("organizer: the selected event is in the URL and survives refresh, Back and a shared link", async ({
  page,
}) => {
  await signIn(page, "organizer");
  await openWorkspace(page);
  const { workspace, event, name, status } = await eventIds(page);
  const nav = page.getByRole("navigation", { name: "Workspace events" });
  const current = nav.locator("[aria-current]");
  await expect(nav.getByRole("button").first()).toBeVisible();
  expect(search(page)).toBe("");

  await nav.getByRole("button", { name: `${name} (${status})` }).click();
  await expect(page).toHaveURL(new RegExp(`\\?event=${event}$`));
  await expect(current).toContainText(name);

  await page.reload();
  await expect(current).toContainText(name);
  expect(search(page)).toBe(`?event=${event}`);

  await page.goBack();
  await expect(page).toHaveURL(/\/app\/w\/[^/]+\/overview$/);
  await expect(current).toHaveCount(0);

  await page.goto(`/app/w/${workspace}/overview?event=${event}`);
  await expect(current).toContainText(name);
});

test("organizer: an event the account cannot see is dropped from the URL without a history entry", async ({
  page,
}) => {
  await signIn(page, "organizer");
  await openWorkspace(page);
  const { workspace } = await eventIds(page);
  const seen: string[] = [];
  page.on("request", (request) => {
    const path = new URL(request.url()).pathname;
    if (path.includes("/events/nonexistent-event")) seen.push(path);
  });
  const before = await page.evaluate(() => history.length);
  await page.goto(`/app/w/${workspace}/overview?event=nonexistent-event`);
  await expect(
    page.getByRole("navigation", { name: "Workspace events" }),
  ).toBeVisible();
  await expect(page).toHaveURL(/\/overview$/);
  expect(seen).toEqual([]); // never requested
  // One entry for the navigation itself; the correction replaced it instead of adding another.
  expect(await page.evaluate(() => history.length)).toBe(before + 1);
});

test("judge: event and stage are context that a refresh and other views keep", async ({
  page,
}) => {
  await signIn(page, "judge-01");
  await openWorkspace(page);
  const main = page.getByRole("region", { name: "Judging" });
  await main.getByLabel("Event").selectOption({ index: 1 });
  await expect(page).toHaveURL(/\?event=[^&]+$/);
  const event = new URL(page.url()).searchParams.get("event")!;
  await main.getByLabel("Stage").selectOption({ index: 1 });
  await expect
    .poll(() => new URL(page.url()).searchParams.get("stage"))
    .not.toBeNull();
  const stage = new URL(page.url()).searchParams.get("stage")!;

  await page.reload();
  await expect(main.getByLabel("Event")).toHaveValue(event);
  await expect(main.getByLabel("Stage")).toHaveValue(stage);

  // Another view keeps the context (the destination link carries it) ...
  await page.locator('#workspace-navigation a[href*="/queue"]').first().click();
  await expect(page).toHaveURL(new RegExp(`/queue\\?.*event=${event}`));
  // ... and switching the event clears the levels below it.
  await main.getByLabel("Event").selectOption({ value: "" });
  await expect.poll(() => search(page)).toBe("");
  await settled(page);
});

test("judge: a stage that does not belong to the event is dropped, the event is kept", async ({
  page,
}) => {
  await signIn(page, "judge-01");
  await openWorkspace(page);
  const main = page.getByRole("region", { name: "Judging" });
  await main.getByLabel("Event").selectOption({ index: 1 });
  await expect(page).toHaveURL(/\?event=[^&]+$/);
  const event = new URL(page.url()).searchParams.get("event")!;
  await page.goto(
    `${new URL(page.url()).pathname}?event=${event}&stage=not-a-stage`,
  );
  await expect(main.getByLabel("Event")).toHaveValue(event);
  await expect.poll(() => search(page)).toBe(`?event=${event}`);
});
