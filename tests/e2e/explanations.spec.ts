import { expect, test } from "@playwright/test";
import {
  accessible,
  chooseWorkspaceEvent,
  eventIds,
  goToDestination,
  goToTask,
  noHorizontalOverflow,
  openWorkspace,
  settled,
  signIn,
} from "./support";

// Explanations (PD-F002-B02-T06): the policy debugger says why in one shape, and so do the
// consequence dialog and readiness. The policy is created through the API, so it runs on an
// isolated fixture. Looking changes nothing.
for (const width of [390, 1440]) {
  test(`a denied policy check explains itself at ${width}`, async ({
    page,
  }, info) => {
    test.skip(info.project.name !== "desktop", "explicit viewport matrix");
    await page.setViewportSize({ width, height: 900 });
    await signIn(page, "organizer");
    await openWorkspace(page);
    const { workspace, event } = await eventIds(page);
    const base = `/api/v1/workspaces/${workspace}/events/${event}`;
    // A window that closed yesterday, and a policy that needs it open.
    const day = 24 * 3600 * 1000;
    const gate = await page.request.post(`${base}/temporal-gates/`, {
      data: {
        name: `submissions${width}`,
        opens_at: new Date(Date.now() - 3 * day).toISOString(),
        closes_at: new Date(Date.now() - day).toISOString(),
      },
    });
    expect(gate.status()).toBe(201);
    const made = await page.request.post(`${base}/policies/`, {
      data: {
        name: `Open window ${width}`,
        ast: { op: "eq", fact: `gate_open:submissions${width}`, value: true },
      },
    });
    expect(made.status()).toBe(201);
    const policy = (await made.json()).public_id as string;
    const bound = await page.request.post(`${base}/policy-bindings/`, {
      data: { action: width === 390 ? "award" : "advance", policy },
    });
    expect(bound.status()).toBe(201);

    const writes: string[] = [];
    page.on("request", (request) => {
      if (request.method() !== "GET" && !request.url().includes("policy-debug"))
        writes.push(`${request.method()} ${request.url()}`);
    });
    await page.goto("/app/");
    await openWorkspace(page);
    await chooseWorkspaceEvent(page);
    await goToDestination(page, "setup");
    // The tabs render once the event has loaded; Policies waits behind Advanced until asked for.
    await expect(page.getByRole("tab", { name: /^Settings/ })).toBeVisible();
    await goToTask(page, "Policies");
    await settled(page);
    const action = width === 390 ? "award" : "advance";
    await page.getByLabel("Debug action").selectOption(action);
    await page.getByRole("button", { name: "Check policy" }).click();
    const why = page.getByRole("region", { name: "Why this decision" });
    await expect(why).toBeVisible();
    await expect(why).toContainText("Blocked");
    await expect(why).toContainText("Denied by policy");
    await expect(why.getByRole("listitem").first()).toContainText("Blocker");
    await expect(why).toContainText(
      `The submissions${width} window is not open.`,
    );
    await noHorizontalOverflow(page);
    await accessible(page);

    // The same answer from the API, with the existing keys intact.
    const direct = await page.request.post(`${base}/policy-debug/`, {
      data: { action },
    });
    const body = await direct.json();
    expect(body.allowed).toBe(false);
    expect(body.explanation.outcome).toBe("blocked");
    expect(
      body.explanation.reasons.every(
        (r: { severity: string }) => r.severity === "blocker",
      ),
    ).toBe(true);
    expect(body.trace.op).toBe("eq");

    // Readiness carries the explanation beside its items.
    const readiness = await (
      await page.request.get(`${base}/readiness/`)
    ).json();
    expect(readiness.explanation.total).toBe(
      readiness.items.filter((i: { passed: boolean }) => !i.passed).length,
    );
    expect(writes).toEqual([]);
  });
}
