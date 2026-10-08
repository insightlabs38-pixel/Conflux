import { expect, test, type Page } from "@playwright/test";
import { eventIds, openWorkspace, settled, signIn } from "./support";

// PD-F005-B02-T01: the event's phase (draft, open, closed, judging, published, archived) is derived
// once on the server and shown beside its name in the event switcher, always there but quiet. It
// closes the event, so it runs on an isolated fixture.
test.skip(({ isMobile }) => isMobile, "sets its own viewport");
const trigger = (page: Page) => page.locator(".cx-switcher summary");

for (const width of [1440, 390]) {
  test(`the phase shows beside the event's name, as the server says it, at ${width}`, async ({
    page,
  }, info) => {
    test.skip(info.project.name !== "desktop", "explicit viewport matrix");
    await page.setViewportSize({ width, height: 900 });
    await signIn(page, "organizer");
    const { workspace, event, name } = await eventIds(page);
    const api = `/api/v1/workspaces/${workspace}/events`;
    const list = await (await page.request.get(`${api}/`)).json();
    const phase = list.find(
      (e: { public_id: string }) => e.public_id === event,
    ).phase;
    expect([
      "draft",
      "open",
      "closed",
      "judging",
      "published",
      "archived",
    ]).toContain(phase.key);
    await page.goto(`/app/w/${workspace}/overview?event=${event}`);
    await settled(page);
    await expect(trigger(page)).toContainText(name);
    await expect(trigger(page).locator(".cx-switcher__phase")).toHaveText(
      phase.label,
    );
    await expect(trigger(page)).toHaveAttribute(
      "aria-label",
      new RegExp(`${name}, ${phase.label}\\.`),
    );
    // the sentence behind the word is there for a pointer
    await expect(trigger(page).locator(".cx-switcher__phase")).toHaveAttribute(
      "title",
      phase.reason,
    );
    await trigger(page).click();
    await expect(
      page.locator(".cx-switcher__panel .cx-switcher__phase").first(),
    ).toHaveText(phase.label);
  });
}

for (const role of ["participant-01", "judge-01"]) {
  test(`${role} sees the phase of the event they choose between`, async ({
    page,
  }) => {
    await signIn(page, role);
    await openWorkspace(page);
    await settled(page);
    await trigger(page).click();
    const phase = page
      .locator(".cx-switcher__panel .cx-switcher__phase")
      .first();
    await expect(phase).toBeVisible();
    await expect(phase).toHaveText(/^(Open|Closed|Judging|Published)$/);
  });
}

test("closing the event changes the phase everywhere (it is derived, not stored on the screen)", async ({
  page,
}) => {
  await signIn(page, "organizer");
  const { workspace, event } = await eventIds(page);
  const api = `/api/v1/workspaces/${workspace}/events`;
  const closed = await page.request.post(`${api}/${event}/status/`, {
    data: { status: "closed" },
  });
  expect(closed.status()).toBe(200);
  expect((await closed.json()).phase).toMatchObject({
    key: "closed",
    label: "Closed",
  });
  await page.goto(`/app/w/${workspace}/overview?event=${event}`);
  await settled(page);
  await expect(trigger(page).locator(".cx-switcher__phase")).toHaveText(
    "Closed",
  );
});
