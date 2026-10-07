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

// Approval gates (PD-F002-B01-T06): sending a message can be made to wait for a second person.
// Off by default; switched in the Approvals panel; the sender cannot approve their own request.
// It writes, so it runs on an isolated fixture (which has one organizer, so the second person's
// approval is proved by the integration suite; here the hold, the visibility and the withdrawal).
for (const width of [390, 1440]) {
  test(`a gated message is held, shown with what it would send and can be withdrawn at ${width}`, async ({
    page,
  }, info) => {
    test.skip(info.project.name !== "desktop", "explicit viewport matrix");
    await page.setViewportSize({ width, height: 900 });
    await signIn(page, "organizer");
    await openWorkspace(page);
    const { workspace, event } = await eventIds(page);
    const api = `/api/v1/workspaces/${workspace}/events/${event}`;
    const message = {
      subject: `Hello ${width}`,
      body: "Welcome to the event.",
      audience_kind: "all_participants",
    };
    const send = () =>
      page.request.post(`${api}/communications/messages/`, { data: message });

    // Off by default: a message goes out as it always did.
    const config = await (
      await page.request.get(`${api}/configuration/`)
    ).json();
    expect(
      config.settings.find(
        (s: { key: string }) => s.key === "approvals.message_send",
      ).value,
    ).toBe(false);
    const messages = async () =>
      (await (await page.request.get(`${api}/communications/messages/`)).json())
        .length;
    const before = await messages();
    expect((await send()).status()).toBe(201);
    expect(await messages()).toBe(before + 1);

    await page.goto(`/app/w/${workspace}/operations?event=${event}`);
    await settled(page);
    await goToTask(page, "Approvals");
    const panel = page.locator(".cx-card").filter({
      has: page.getByRole("heading", { name: "Approvals", exact: true }),
    });
    const gate = panel.getByLabel("Sending a message to an audience");
    await expect(gate).not.toBeChecked();
    await expect(panel.getByText("No approval requests")).toBeVisible();
    await noHorizontalOverflow(page);

    // Switch the gate on in the page; the server now holds the message.
    await gate.click(); // the box follows the server's answer, so it is not instant
    await expect(gate).toBeChecked();
    await expect
      .poll(async () => {
        const gates = await (
          await page.request.get(`${api}/approval-gates/`)
        ).json();
        return gates.find(
          (g: { action: string }) => g.action === "message_send",
        ).enabled;
      })
      .toBe(true);
    const held = await send();
    expect(held.status()).toBe(409);
    const body = await held.json();
    expect(body.code).toBe("approval_required");
    expect(body.approval.summary[0]).toContain(`Send “Hello ${width}”`);
    expect(await messages()).toBe(before + 1); // nothing more was sent while held

    // The request is on the page, says what it would do, and the asker cannot approve it.
    await page.reload();
    await settled(page);
    await goToTask(page, "Approvals");
    const requests = panel.getByRole("list", { name: "Approval requests" });
    await expect(requests).toContainText(`Send “Hello ${width}”`);
    await expect(requests).toContainText("Waiting for another person");
    await expect(requests.getByRole("button", { name: "Approve" })).toHaveCount(
      0,
    );
    await accessible(page);
    await noHorizontalOverflow(page);
    const self = await page.request.post(
      `${api}/approvals/${body.approval.public_id}/decision/`,
      { data: { decision: "approve" } },
    );
    expect(self.status()).toBe(400);

    // Withdrawing it removes it from the waiting list and keeps the record.
    await requests.getByRole("button", { name: "Withdraw" }).click();
    await expect(panel.getByText("No approval requests")).toBeVisible();
    const after = await (
      await page.request.get(`${api}/approvals/${body.approval.public_id}/`)
    ).json();
    expect(after.status).toBe("cancelled");
    const again = await send();
    expect(again.status()).toBe(409); // a new request is needed
    const next = (await again.json()).approval.public_id;
    expect(next).not.toBe(body.approval.public_id);
    await page.request.post(`${api}/approvals/${next}/cancel/`);

    // Turning the gate off restores the plain behaviour.
    await panel.getByLabel("Sending a message to an audience").click();
    await expect(
      panel.getByLabel("Sending a message to an audience"),
    ).not.toBeChecked();
    await expect.poll(async () => (await send()).status()).toBe(201);
  });
}
