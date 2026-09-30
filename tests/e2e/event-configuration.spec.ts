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

// Defaults and derived values are queryable (PD-F001-B01-T08): the configuration endpoint tells
// automation every value, its baseline and source, and how to write it, and the Setup panel shows
// the same answer. The journey follows the endpoint's own `write` description literally, the way
// automation would, then sees the result in both. Mutating, so it runs on an isolated fixture.
for (const width of [390, 1440]) {
  test(`configuration answers where each value comes from and how to change it at ${width}`, async ({
    page,
  }, info) => {
    test.skip(info.project.name !== "desktop", "explicit viewport matrix");
    await page.setViewportSize({ width, height: 900 });
    await signIn(page, "organizer");
    await openWorkspace(page);
    const { workspace } = await eventIds(page);
    const stamp = Date.now();
    const created = await page.request.post(
      `/api/v1/workspaces/${workspace}/event-templates/library/hackathon/instantiate/`,
      {
        data: {
          name: `Config ${width} ${stamp}`,
          slug: `config-${width}-${stamp}`,
          starts_at: "2027-03-05T09:00:00Z",
          timezone: "UTC",
        },
      },
    );
    expect(created.status()).toBe(201);
    const event = (await created.json()).public_id as string;
    const configuration = async (query = "") =>
      (
        await (
          await page.request.get(
            `/api/v1/workspaces/${workspace}/events/${event}/configuration/${query}`,
          )
        ).json()
      ).settings as {
        key: string;
        value: unknown;
        source: string;
        baseline: unknown;
        write: {
          method: string;
          path: string;
          field: string;
          body: string;
        } | null;
      }[];
    const mode = async () => (await configuration("?key=registration.mode"))[0];

    // Automation's view: value, baseline and source are all there.
    expect(await mode()).toMatchObject({
      value: "open",
      baseline: "open",
      source: "preset",
    });
    const duration = (await configuration("?source=derived")).find(
      (s) => s.key === "dates.duration_hours",
    );
    expect(duration?.value).toBe(48);

    // Change it exactly as the answer says to (method, path, field): no UI knowledge needed.
    const write = (await mode()).write!;
    expect(write).toMatchObject({
      method: "PUT",
      field: "mode",
      body: "partial",
    });
    const changed = await page.request.fetch(
      `/api/v1/${write.path.replace("{workspace}", workspace).replace("{event}", event)}`,
      { method: write.method, data: { [write.field]: "invite_only" } },
    );
    expect(changed.status()).toBe(200);
    expect(await mode()).toMatchObject({
      value: "invite_only",
      baseline: "open",
      source: "overridden",
    });

    // The Setup panel shows the same thing, behind the Advanced disclosure.
    await page.goto(`/app/w/${workspace}/setup?event=${event}`);
    await settled(page);
    await goToTask(page, "Defaults & overrides");
    const panel = page.getByRole("region", { name: "Defaults and overrides" });
    await expect(panel).toContainText(
      "this event started from the Hackathon format",
    );
    await expect(panel).toContainText("Registration: invite only");
    await expect(panel).toContainText("Started as open.");
    // What a valid new value must satisfy is stated next to the value.
    await expect(panel).toContainText(
      "Rule: Between 1 and 100, and not below the smallest team.",
    );
    // Generated configuration states only the change; the format's own values stay legible.
    await panel.getByText("Generated configuration", { exact: true }).click();
    const generated = panel.locator("pre");
    await expect(generated).toContainText(
      'registration.mode: "invite_only"  # changed; the format uses "open"',
    );
    await expect(generated).toContainText("# Inherited, not stated");
    await expect(generated).toContainText("#   team.min_size: 1  # preset");
    expect(await generated.textContent()).not.toMatch(/^ {2}team\.min_size/m);
    const stated = await (
      await page.request.get(
        `/api/v1/workspaces/${workspace}/events/${event}/configuration/generated/`,
      )
    ).json();
    expect(stated.explicit.map((e: { key: string }) => e.key)).toContain(
      "registration.mode",
    );
    expect(stated.document.format).toBe("hackathon@1");
    await panel.getByLabel("Show").selectOption("overridden");
    await expect(panel.getByRole("listitem")).toHaveCount(1);
    await expect(panel).toContainText("Registration: invite only");
    await noHorizontalOverflow(page);
    await accessible(page);
  });
}
