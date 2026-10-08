import { expect, test } from "@playwright/test";
import {
  accessible,
  chooseWorkspaceEvent,
  eventIds,
  goToDestination,
  goToTask,
  noHorizontalOverflow,
  openWorkspace,
  settled,
  signIn,
} from "./support";

// PD-F005-B03-T02: unsaved edits survive going to another place in the workspace and coming back,
// the place shows as holding unsaved changes, closing it asks, and a reload warns. Nothing is saved
// (the form is only edited), so it is read-only on the reference event.
test("an unsaved appearance edit waits in its tab while the person works elsewhere, and closing the tab asks", async ({
  page,
}) => {
  await signIn(page, "organizer");
  await page.goto("/app/");
  await openWorkspace(page);
  await chooseWorkspaceEvent(page);
  await goToDestination(page, "setup");
  await goToTask(page, "Public page");
  await page.getByRole("tab", { name: /^Appearance/ }).click();
  await settled(page);

  const tabs = page.getByRole("navigation", { name: "Open places" });
  await expect(tabs).toHaveCount(0); // base state: no tab strip
  const size = page.getByLabel("Hero size", { exact: true });
  const original = await size.inputValue();
  const changed = original === "none" ? "standard" : "none";
  await size.selectOption(changed);
  await expect(tabs).toContainText("unsaved changes");

  // elsewhere: the tab stays, marked
  await goToDestination(page, "overview");
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.screenshot({
    path: "tests/e2e/artifacts/workspace-tabs.png",
    clip: { x: 0, y: 0, width: 1280, height: 220 },
  });
  await expect(tabs).toContainText("unsaved changes");
  await noHorizontalOverflow(page);
  await accessible(page);

  // back through the tab: the edit is where it was left
  await tabs.getByRole("link").first().click();
  await goToTask(page, "Public page");
  await page.getByRole("tab", { name: /^Appearance/ }).click();
  await expect(page.getByLabel("Hero size", { exact: true })).toHaveValue(
    changed,
  );

  // a reload would lose it: the browser is asked
  const warned = await page.evaluate(() => {
    const event = new Event("beforeunload", { cancelable: true });
    window.dispatchEvent(event);
    return event.defaultPrevented;
  });
  expect(warned).toBe(true);

  // closing the tab says what is lost; keep editing keeps it, discard removes it
  await tabs.getByRole("button", { name: /^Close/ }).click();
  const dialog = page.getByRole("dialog");
  await expect(dialog).toContainText("Event appearance");
  await dialog.getByRole("button", { name: "Keep editing" }).click();
  await expect(tabs).toContainText("unsaved changes");
  await tabs.getByRole("button", { name: /^Close/ }).click();
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Discard and close" })
    .click();
  await expect(tabs).toHaveCount(0);
  const { event } = await eventIds(page);
  const saved = await (
    await page.request.get(
      `/api/v1/workspaces/${new URL(page.url()).pathname.split("/")[3]}/events/${event}/page/`,
    )
  ).json();
  expect(JSON.stringify(saved)).not.toContain(`"hero_size":"${changed}"`); // nothing was saved
});

test("a place kept open from the palette survives a reload and reopens where it was", async ({
  page,
}) => {
  await signIn(page, "organizer");
  await openWorkspace(page);
  const { workspace, event } = await eventIds(page);
  await page.goto(
    `/app/w/${workspace}/participants?event=${event}&sort_projects=-name&section=ProjectsGrid`,
  );
  await settled(page);
  await page.locator("main").focus();
  await page.keyboard.press("Control+k");
  await page.getByRole("dialog").getByRole("combobox").fill("keep this place");
  await expect(
    page.getByRole("option", { name: "Keep this place open in a tab" }),
  ).toBeVisible();
  await page.keyboard.press("Enter");
  const tabs = page.getByRole("navigation", { name: "Open places" });
  await expect(tabs).toContainText("Participants");
  await goToDestination(page, "overview");
  await page.reload();
  await settled(page);
  await expect(tabs).toContainText("Participants");
  await tabs.getByRole("link").click();
  await expect(page).toHaveURL(/sort_projects=-name/); // where it was left
  await page.locator("main").focus();
  await page.keyboard.press("Control+k");
  await page.getByRole("dialog").getByRole("combobox").fill("close this place");
  await expect(
    page.getByRole("option", { name: "Close this place's tab" }),
  ).toBeVisible();
  await page.keyboard.press("Enter");
  await expect(tabs).toHaveCount(0);
});
