import { expect, test } from "@playwright/test";
import {
  accessible,
  goToDestination,
  noHorizontalOverflow,
  openWorkspace,
  settled,
  signIn,
} from "./support";

// Notification preferences (PD-F002-B02-T04): a person chooses what is also emailed, per
// workspace, from their profile. The inbox copy and essential notices are fixed, a choice
// survives a reload, and nobody else's choices move. It writes, so it runs on an isolated fixture.
for (const width of [390, 1440]) {
  test(`a participant chooses which notices reach their email at ${width}`, async ({
    page,
  }, info) => {
    test.skip(info.project.name !== "desktop", "explicit viewport matrix");
    await page.setViewportSize({ width, height: 900 });
    await signIn(page, "participant-01");
    await openWorkspace(page);
    const me = await (await page.request.get("/api/v1/accounts/me/")).json();
    const workspace = me.memberships[0].workspace as string;
    const api = `/api/v1/workspaces/${workspace}/notification-preferences/`;
    const email = async (category: string) => {
      const body = await (await page.request.get(api)).json();
      const row = body.categories.find(
        (c: { category: string }) => c.category === category,
      );
      return row.channels.find(
        (c: { channel: string }) => c.channel === "email",
      ).enabled as boolean;
    };
    expect(await email("announcement")).toBe(true);
    expect(await email("mention")).toBe(false);

    await goToDestination(page, "profile");
    // the profile's own disclosure (the account menu and the bell link here too)
    await page
      .locator("main")
      .getByText("Notification preferences", { exact: true })
      .click();
    const panel = page.getByRole("region", {
      name: "Notification preferences",
    });
    await expect(panel).toBeVisible();
    const announcements = panel.getByRole("group", {
      name: "Announcements and reminders",
    });
    const essential = panel.getByRole("group", {
      name: "Account and safety notices",
    });

    // Fixed channels are shown as fixed, never as a choice.
    await expect(
      announcements.getByRole("checkbox", { name: /In-app inbox/ }),
    ).toBeDisabled();
    await expect(
      announcements.getByRole("checkbox", { name: /In-app inbox/ }),
    ).toBeChecked();
    for (const box of await essential.getByRole("checkbox").all()) {
      await expect(box).toBeDisabled();
      await expect(box).toBeChecked();
    }
    await noHorizontalOverflow(page);
    await accessible(page);

    // A choice saves at once and survives a reload.
    const emailBox = announcements.getByRole("checkbox", { name: /Email/ });
    await emailBox.click();
    await expect(
      panel
        .getByRole("status")
        .filter({ hasText: "Announcements and reminders: Email off." }),
    ).toBeVisible();
    expect(await email("announcement")).toBe(false);
    expect(await email("mention")).toBe(false);
    await page.reload();
    await settled(page);
    await goToDestination(page, "profile");
    // the profile's own disclosure (the account menu and the bell link here too)
    await page
      .locator("main")
      .getByText("Notification preferences", { exact: true })
      .click();
    await expect(
      panel
        .getByRole("group", { name: "Announcements and reminders" })
        .getByRole("checkbox", { name: /Email/ }),
    ).not.toBeChecked();
    await accessible(page);

    // Turning it back on restores the default; the server refuses what is fixed.
    await panel
      .getByRole("group", { name: "Announcements and reminders" })
      .getByRole("checkbox", { name: /Email/ })
      .click();
    await expect(
      panel.getByRole("status").filter({ hasText: "Email on." }),
    ).toBeVisible();
    expect(await email("announcement")).toBe(true);
    const refused = await page.request.put(api, {
      data: { category: "essential", channel: "email", enabled: false },
    });
    expect(refused.status()).toBe(400);
    expect(await email("essential")).toBe(true);
  });
}
