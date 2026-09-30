import { expect, test } from "@playwright/test";
import {
  accessible,
  chooseWorkspaceEvent,
  destinationLink,
  eventIds,
  goToDestination,
  goToTask,
  noHorizontalOverflow,
  openWorkspace,
  settled,
  signIn,
} from "./support";

// Optional modules (PD-F001-B01-T04): a system that is off disappears from navigation, its link is
// still a valid place that explains itself, turning it on is an explicit audited choice that
// survives a refresh, and a module that already holds content cannot be turned off. Mutating, so
// it runs on an isolated fixture: one sequential journey (webhooks cannot be removed once created),
// with the narrow layout for the off/on states and the wide layout for the rest.
test("integrations follows the organizer's choice and its content, at narrow and wide layouts", async ({
  page,
}, info) => {
  test.skip(info.project.name !== "desktop", "explicit viewport matrix");
  await page.setViewportSize({ width: 390, height: 900 });
  await signIn(page, "organizer");
  await openWorkspace(page);
  await chooseWorkspaceEvent(page);
  const { workspace, event } = await eventIds(page);
  const state = async () =>
    (
      await (
        await page.request.get(
          `/api/v1/workspaces/${workspace}/modules/?event=${event}`,
        )
      ).json()
    ).modules.find((m: { key: string }) => m.key === "integrations");
  const start = await state();
  expect(
    [start.in_use, start.explicit],
    "the fixture starts with the module off and empty",
  ).toEqual([false, null]);
  const link = destinationLink(page, "integrations");
  const turnOff = page.getByRole("button", {
    name: /^Turn off integrations$/i,
  });

  // Off (narrow): no link, but the deep link explains and offers to turn it on.
  await expect(link).toHaveCount(0);
  await page.goto(
    page.url().replace(/\/w\/([^/]+)\/[^?]+/, "/w/$1/integrations"),
  );
  await expect(
    page.getByText("Integrations is not turned on for this event."),
  ).toBeVisible();
  await noHorizontalOverflow(page);
  await accessible(page);

  // On (narrow): turning it on offers the link and the tools; the server recorded the choice.
  await page.getByRole("button", { name: /^Turn on integrations$/i }).click();
  await expect(link).toHaveCount(1);
  await expect(
    page.getByRole("heading", { name: "Webhooks", exact: true }),
  ).toBeVisible();
  await settled(page);
  await noHorizontalOverflow(page);
  await accessible(page);
  expect((await state()).explicit).toBe(true);

  // The choice is server state: it survives a refresh (wide).
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.reload();
  await settled(page);
  await expect(link).toHaveCount(1);

  // Turning it off from Setup removes the link again.
  await goToDestination(page, "setup");
  await goToTask(page, "Features");
  await turnOff.click();
  await expect(link).toHaveCount(0);
  expect((await state()).explicit).toBe(false);

  // Once it holds content it is on whatever was chosen, and cannot be turned off.
  const created = await page.request.post(
    `/api/v1/workspaces/${workspace}/webhooks/`,
    {
      data: {
        url: "https://example.com/hook",
        event_types: ["submission.created"],
        event,
      },
    },
  );
  expect(created.status()).toBe(201);
  await page.reload();
  await settled(page);
  await expect(link).toHaveCount(1);
  await goToDestination(page, "setup");
  await goToTask(page, "Features");
  await expect(turnOff).toBeDisabled();
  await expect(
    page.getByText(/Integrations already has content for this event/),
  ).toBeVisible();
  const refused = await page.request.patch(
    `/api/v1/workspaces/${workspace}/events/${event}/modules/integrations/`,
    { data: { enabled: false } },
  );
  expect(refused.status()).toBe(400);
  await accessible(page);
});
