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

// Threads (PD-F002-B01-T07): internal organizer notes on a project, from the Projects grid. Plain
// text, replies, edit, removal as a tombstone, and invisible to participants. It writes, so it runs
// on an isolated fixture.
for (const width of [390, 1440]) {
  test(`organizers keep notes on a project: write, reply, edit, remove, and participants cannot see them at ${width}`, async ({
    page,
    browser,
  }, info) => {
    test.skip(info.project.name !== "desktop", "explicit viewport matrix");
    await page.setViewportSize({ width, height: 900 });
    await signIn(page, "organizer");
    await openWorkspace(page);
    const { workspace, event } = await eventIds(page);
    const api = `/api/v1/workspaces/${workspace}/events/${event}`;
    const projects = await (
      await page.request.get(`${api}/entities/projects/?sort=name`)
    ).json();
    const project = projects.rows[width === 390 ? 0 : 1] as {
      id: string;
      name: string;
    };
    const thread = `${api}/threads/project/${project.id}/organizers/`;

    await page.goto(`/app/w/${workspace}/participants?event=${event}`);
    await settled(page);
    await goToTask(page, "Projects");
    await page
      .getByRole("button", { name: `Notes on ${project.name}` })
      .click();
    const dialog = page.getByRole("dialog");
    await expect(dialog).toContainText(`Organizer notes on ${project.name}`);
    await expect(dialog).toContainText("No notes yet");
    await noHorizontalOverflow(page);

    // Write a note; markup stays text.
    const risky = `Check the repo <b>link</b> ${width}`;
    await dialog.getByLabel("New note").fill(risky);
    await dialog.getByRole("button", { name: "Post note" }).click();
    const list = dialog.getByRole("list", { name: "Comments" });
    await expect(list).toContainText(risky);
    await expect(list.locator("b")).toHaveCount(0);

    // Reply, edit, then remove with a confirmation.
    await list.getByRole("button", { name: "Reply" }).click();
    await dialog.getByLabel(/^Reply to @/).fill("Looked, it is fine.");
    await dialog.getByRole("button", { name: "Post reply" }).click();
    await expect(list).toContainText("Looked, it is fine.");
    await list.getByRole("button", { name: "Edit" }).first().click();
    await dialog.getByLabel("Edit note").fill(`Edited ${width}`);
    await dialog.getByRole("button", { name: "Save" }).click();
    await expect(list).toContainText(`Edited ${width}`);
    await expect(list).toContainText("edited");
    await accessible(page);
    await noHorizontalOverflow(page);

    await list.getByRole("button", { name: "Remove" }).first().click();
    await expect(dialog).toContainText("cannot be restored");
    await dialog
      .getByRole("group", { name: "Confirm removal" })
      .getByRole("button", { name: "Remove" })
      .click();
    await expect(list).toContainText("This comment was removed.");
    await expect(list).not.toContainText(`Edited ${width}`);
    await expect(list).toContainText("Looked, it is fine."); // the reply keeps its place

    // The record is on the server, content-free in the audit trail, text erased.
    const saved = await (await page.request.get(thread)).json();
    expect(saved.comments[0]).toMatchObject({ removed: true, body: "" });
    await page.keyboard.press("Escape");
    await expect(dialog).toHaveCount(0);

    // A participant of the same workspace cannot read, write or learn that notes exist.
    const other = await browser.newContext();
    const participant = await other.newPage();
    await signIn(participant, "participant-01");
    expect((await participant.request.get(thread)).status()).toBe(404);
    expect(
      (
        await participant.request.post(thread, { data: { body: "hello" } })
      ).status(),
    ).toBe(404);
    await other.close();
  });
}
