import { expect, test } from "@playwright/test";
import { openWorkspace, signIn } from "./support";

// Realtime boundary (PD-B04-T06; lib/realtime.ts) in the real app: the polling transport hints the
// inbox topic, the hint refetches through the server-state layer, and signing out closes it.
test.skip(
  ({ isMobile }) => isMobile,
  "transport contract; viewport independent",
);

test("the inbox topic polls on an interval and stops with the session", async ({
  page,
}) => {
  await page.clock.install();
  const inbox: string[] = [];
  page.on("request", (request) => {
    if (
      request.method() === "GET" &&
      new URL(request.url()).pathname.endsWith("/inbox/")
    )
      inbox.push(request.url());
  });
  await signIn(page, "participant-01");
  await openWorkspace(page);
  await expect(
    page.getByRole("region", { name: "Participant events" }),
  ).toBeVisible();
  await expect.poll(() => inbox.length).toBeGreaterThan(0);
  const loaded = inbox.length;

  await page.clock.fastForward(61_000); // one poll interval (60 s) later
  await expect.poll(() => inbox.length).toBe(loaded + 1);
  await page.clock.fastForward(61_000);
  await expect.poll(() => inbox.length).toBe(loaded + 2);

  await page.locator(".cx-account summary").click();
  await page.getByRole("button", { name: "Sign out", exact: true }).click();
  await expect(page.getByLabel("Username")).toBeVisible();
  const afterSignOut = inbox.length;
  await page.clock.fastForward(180_000);
  await page.waitForTimeout(300);
  expect(inbox.length).toBe(afterSignOut); // the hub was reset with the session
});
