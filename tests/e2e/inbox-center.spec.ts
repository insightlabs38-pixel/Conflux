import { expect, test, type Page } from "@playwright/test";
import { eventIds, openWorkspace, settled, signIn } from "./support";

// PD-F005-B01-T07: the notification center in the top bar. It is a view of the member's inbox
// through the existing endpoints: the unread count, the latest messages, mark one read, a link to
// all messages and to the notification preferences. It sends a real message, so it runs on an
// isolated fixture.
const bell = (page: Page) => page.locator(".cx-inbox summary");
const panel = (page: Page) => page.locator(".cx-inbox__panel");

async function send(page: Page, subject: string) {
  await signIn(page, "organizer");
  await openWorkspace(page);
  const { workspace, event } = await eventIds(page);
  const response = await page.request.post(
    `/api/v1/workspaces/${workspace}/events/${event}/communications/messages/`,
    {
      data: {
        subject,
        body: "Doors open at nine. Bring your badge.",
        audience_kind: "all_participants",
      },
    },
  );
  expect(response.status()).toBe(201);
  await page.request.post("/api/v1/accounts/logout/"); // the next sign-in is another person
  return { workspace, event };
}

for (const width of [1440, 390]) {
  test(`a participant sees what is waiting, reads it and marks it read at ${width}`, async ({
    page,
  }, info) => {
    test.skip(info.project.name !== "desktop", "explicit viewport matrix");
    await page.setViewportSize({ width, height: 900 });
    const subject = `Welcome ${width}`;
    await send(page, subject);
    await signIn(page, "participant-01");
    await openWorkspace(page);
    await settled(page);
    await expect(bell(page)).toHaveAttribute(
      "aria-label",
      /^Notifications, \d+ unread$/,
    );
    const waiting = Number(await page.locator(".cx-inbox__count").innerText());
    expect(waiting).toBeGreaterThanOrEqual(1); // the fixture's other tests send messages too
    await bell(page).click();
    const row = panel(page).locator("li", { hasText: subject });
    await expect(row).toContainText("Doors open at nine");
    await expect(row).toContainText("New");
    if (width === 390) {
      const box = (await panel(page).boundingBox())!;
      expect(box.x).toBeGreaterThanOrEqual(0);
      expect(box.x + box.width).toBeLessThanOrEqual(390);
    }
    // opening it marked nothing; reading is explicit
    await expect(page.locator(".cx-inbox__count")).toHaveText(String(waiting));
    await row.getByRole("button", { name: "Mark read" }).click();
    await expect(row.getByRole("button", { name: "Mark read" })).toHaveCount(0);
    const left = waiting - 1;
    const after = left
      ? `Notifications, ${left} unread`
      : "Notifications, none unread";
    await expect(bell(page)).toHaveAttribute("aria-label", after);
    // the server holds it: still read after a reload
    await page.reload();
    await settled(page);
    await expect(bell(page)).toHaveAttribute("aria-label", after);
    await bell(page).click();
    await expect(panel(page).locator("li", { hasText: subject })).toBeVisible();
    await expect(
      panel(page)
        .locator("li", { hasText: subject })
        .getByRole("button", { name: "Mark read" }),
    ).toHaveCount(0);
    // Escape closes it and returns focus to the bell
    await page.keyboard.press("Escape");
    await expect(page.locator(".cx-inbox")).not.toHaveAttribute("open", "");
    await expect(bell(page)).toBeFocused();
  });
}

test("the links go to all messages and to the notification preferences", async ({
  page,
}) => {
  const subject = "Links check";
  await send(page, subject);
  await signIn(page, "participant-01");
  await openWorkspace(page);
  await settled(page);
  await bell(page).click();
  await panel(page).getByRole("link", { name: "All messages" }).click();
  await expect(page).toHaveURL(/\/messages/);
  await expect(page.getByRole("heading", { name: "Inbox" })).toBeVisible();
  await expect(page.locator("main").getByText(subject).first()).toBeVisible();
  await bell(page).click();
  await panel(page)
    .getByRole("link", { name: "Notification preferences" })
    .click();
  await expect(page).toHaveURL(/\/profile.*#notification-preferences/);
  await expect(
    page.getByRole("region", { name: "Notification preferences" }),
  ).toBeVisible();
});

test("an organizer who received nothing is told they are caught up, and a failed read says so and recovers", async ({
  page,
}) => {
  await signIn(page, "organizer");
  await openWorkspace(page);
  await settled(page);
  await bell(page).click();
  await expect(panel(page)).toContainText("You are all caught up.");
  await expect(
    panel(page).getByRole("link", { name: "All messages" }),
  ).toHaveCount(0); // organizers have Communications, not Messages
  // the list cannot load: what happened is said, nothing is lost, retry recovers
  await page.route("**/inbox/", (route) =>
    route.fulfill({ status: 503, json: { detail: "down" } }),
  );
  await page.reload();
  await settled(page);
  await bell(page).click();
  await expect(panel(page).getByRole("alert")).toContainText(
    "Could not load your inbox.",
  );
  await page.unroute("**/inbox/");
  await panel(page).getByRole("button", { name: "Try again" }).click();
  await expect(panel(page)).toContainText("You are all caught up.");
});
