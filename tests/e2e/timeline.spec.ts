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

// The event timeline (PD-F002-B01-T08): every date and window in the event's own clock, advisory
// conflicts, and changing a time through the domain endpoint each item names. It writes, so it
// runs on an isolated fixture.
for (const width of [390, 1440]) {
  test(`the timeline lists everything time-boxed, flags a conflict and moves a session at ${width}`, async ({
    page,
  }, info) => {
    test.skip(info.project.name !== "desktop", "explicit viewport matrix");
    await page.setViewportSize({ width, height: 900 });
    await signIn(page, "organizer");
    await openWorkspace(page);
    const { workspace, event } = await eventIds(page);
    const api = `/api/v1/workspaces/${workspace}/events/${event}`;
    const detail = await (await page.request.get(`${api}/`)).json();
    const base = new Date(detail.starts_at ?? Date.now() + 86_400_000);
    const at = (hours: number) =>
      new Date(base.getTime() + hours * 3_600_000).toISOString();
    const room = await (
      await page.request.post(`${api}/locations/`, {
        data: { kind: "room", name: `Hall ${width}` },
      })
    ).json();
    const session = async (title: string, from: number, to: number) =>
      (
        await page.request.post(`${api}/agenda/`, {
          data: {
            title,
            starts_at: at(from),
            ends_at: at(to),
            location: room.public_id,
            is_public: false,
          },
        })
      ).json();
    const first = await session(`Keynote ${width}`, 1, 3);
    await session(`Panel ${width}`, 2, 4); // overlaps the keynote in the same room

    // The API says the same thing the page will show.
    const body = await (await page.request.get(`${api}/timeline/`)).json();
    expect(body.conflicts.map((c: { code: string }) => c.code)).toContain(
      "location_overlap",
    );
    const keynote = body.items.find(
      (i: { key: string }) => i.key === `agenda:${first.public_id}`,
    );
    expect(keynote.editable).toBe(true);
    expect(keynote.local_starts_at).toMatch(/[+-]\d\d:\d\d$/);

    await page.goto(`/app/w/${workspace}/operations?event=${event}`);
    await settled(page);
    await goToTask(page, "Timeline");
    const panel = page.locator(".cx-card").filter({
      has: page.getByRole("heading", { name: "Timeline", exact: true }),
    });
    await expect(panel).toContainText(`Keynote ${width}`);
    await expect(
      panel.getByRole("region", { name: "Scheduling conflicts" }),
    ).toContainText("overlap on the same location");
    await expect(panel).toContainText("nothing is blocked");
    await noHorizontalOverflow(page);
    await accessible(page);

    // Move the panel so the two no longer overlap: through the agenda endpoint, in the page.
    await panel
      .getByRole("button", { name: `Change the times of Panel ${width}` })
      .click();
    const form = panel.getByRole("form", { name: `Times of Panel ${width}` });
    const [starts, ends] = await form.locator("input").all();
    const startValue = await starts.inputValue();
    // The input is a wall-clock time in the event's zone; shift it as plain calendar arithmetic
    // so a time late in the evening rolls over to the next day instead of wrapping to the same one.
    const wall = new Date(`${startValue}:00Z`).getTime();
    const shift = (h: number) =>
      new Date(wall + h * 3_600_000).toISOString().slice(0, 16);
    await starts.fill(shift(2));
    await ends.fill(shift(4));
    await form.getByRole("button", { name: "Save" }).click();
    await expect(
      panel.getByRole("region", { name: "Scheduling conflicts" }),
    ).toHaveCount(0);
    const after = await (await page.request.get(`${api}/timeline/`)).json();
    expect(
      after.conflicts.filter(
        (c: { code: string }) => c.code === "location_overlap",
      ),
    ).toHaveLength(0);

    // The refusal of an impossible time is the domain's own message.
    await panel
      .getByRole("button", { name: `Change the times of Panel ${width}` })
      .click();
    const again = panel.getByRole("form", { name: `Times of Panel ${width}` });
    const [s2, e2] = await again.locator("input").all();
    await e2.fill(await s2.inputValue());
    await again.getByRole("button", { name: "Save" }).click();
    await expect(again.getByRole("alert")).toBeVisible();
    await again.getByRole("button", { name: "Cancel" }).click();

    // The overview shows what is coming up.
    await page.goto(`/app/w/${workspace}/overview?event=${event}`);
    await settled(page);
    await expect(page.getByLabel("Coming up")).toContainText(
      /Keynote|Panel|Event/,
    );
  });
}
