import { expect, test } from "@playwright/test";
import {
  accessible,
  eventIds,
  goToTask,
  noHorizontalOverflow,
  openWorkspace,
  settled,
  signIn,
} from "./support";

// The shared schema form (PD-F002-B02-T01): a setting is changed in place on Defaults & overrides,
// with the control its schema declares, a refusal shown before anything is sent, and the value
// saved through the endpoint the configuration answer names. It writes, so it runs on an isolated
// fixture.
for (const width of [390, 1440]) {
  test(`settings are changed with schema-driven controls and saved through their own endpoints at ${width}`, async ({
    page,
  }, info) => {
    test.skip(info.project.name !== "desktop", "explicit viewport matrix");
    await page.setViewportSize({ width, height: 900 });
    await signIn(page, "organizer");
    await openWorkspace(page);
    const { workspace, event } = await eventIds(page);
    const api = `/api/v1/workspaces/${workspace}/events/${event}`;
    const settings = async () => {
      const body = await (
        await page.request.get(`${api}/configuration/`)
      ).json();
      return Object.fromEntries(
        body.settings.map((s: { key: string }) => [s.key, s]),
      ) as Record<string, { value: unknown; label: string; editable: boolean }>;
    };
    const before = await settings();
    const waitlist = before["registration.waitlist_enabled"];
    const capacity = before["registration.capacity"];
    const starts = before["event.starts_at"];

    await page.goto(`/app/w/${workspace}/setup?event=${event}`);
    await settled(page);
    await goToTask(page, "Defaults & overrides");
    const panel = page.getByRole("region", { name: "Defaults and overrides" });
    await expect(panel).toBeVisible();
    await noHorizontalOverflow(page);

    // A boolean is a checkbox; saving goes through the registration endpoint.
    await panel
      .getByRole("button", { name: `Change ${waitlist.label}` })
      .click();
    const form = panel.getByRole("form", { name: `Change ${waitlist.label}` });
    await form.getByRole("checkbox").setChecked(waitlist.value !== true);
    await form.getByRole("button", { name: "Save" }).click();
    await expect(form).toHaveCount(0);
    expect((await settings())["registration.waitlist_enabled"].value).toBe(
      waitlist.value !== true,
    );

    // A bounded number refuses a bad value in the form, before anything is sent.
    await panel
      .getByRole("button", { name: `Change ${capacity.label}` })
      .click();
    const capacityForm = panel.getByRole("form", {
      name: `Change ${capacity.label}`,
    });
    const input = capacityForm.getByRole("spinbutton");
    await input.fill("0");
    await expect(capacityForm.getByRole("alert")).toContainText("at least 1");
    await expect(
      capacityForm.getByRole("button", { name: "Save" }),
    ).toBeDisabled();
    await accessible(page);
    await input.fill("25");
    await capacityForm.getByRole("button", { name: "Save" }).click();
    await expect(capacityForm).toHaveCount(0);
    expect((await settings())["registration.capacity"].value).toBe(25);

    // A date-time is entered on the event's own clock and saved as a UTC instant. A start after
    // the end is refused by the event endpoint itself and the form stays open with its reason.
    if (starts?.editable) {
      await panel
        .getByRole("button", { name: `Change ${starts.label}` })
        .click();
      const startsForm = panel.getByRole("form", {
        name: `Change ${starts.label}`,
      });
      const picker = startsForm.locator('input[type="datetime-local"]');
      await picker.fill("2099-05-10T09:00");
      await startsForm.getByRole("button", { name: "Save" }).click();
      await expect(startsForm.getByRole("alert")).toContainText(
        "End must be after start",
      );
      const window = await (await page.request.get(`${api}/timeline/`)).json();
      const ends: string = window.items.find(
        (i: { key: string }) => i.key === "event:window",
      ).local_ends_at;
      const day = new Date(`${ends.slice(0, 10)}T00:00:00Z`);
      day.setUTCDate(day.getUTCDate() - 1);
      const wanted = `${day.toISOString().slice(0, 10)}T09:00`;
      await picker.fill(wanted);
      await startsForm.getByRole("button", { name: "Save" }).click();
      await expect(startsForm).toHaveCount(0);
      const timeline = await (
        await page.request.get(`${api}/timeline/`)
      ).json();
      const item = timeline.items.find(
        (i: { key: string }) => i.key === "event:window",
      );
      expect(item.local_starts_at.slice(0, 16)).toBe(wanted);
    }

    // The domain's own refusal is shown and the form stays open.
    const maxSize = before["team.max_size"];
    await panel
      .getByRole("button", { name: `Change ${maxSize.label}` })
      .click();
    const sizeForm = panel.getByRole("form", {
      name: `Change ${maxSize.label}`,
    });
    await sizeForm.getByRole("spinbutton").fill("1");
    const minSize = (await settings())["team.min_size"].value;
    if (typeof minSize === "number" && minSize > 1) {
      await sizeForm.getByRole("button", { name: "Save" }).click();
      await expect(sizeForm.getByRole("alert")).toBeVisible();
    }
    await sizeForm.getByRole("button", { name: "Cancel" }).click();
    await noHorizontalOverflow(page);
  });
}
