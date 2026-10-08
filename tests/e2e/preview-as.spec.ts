import { expect, test, type Page } from "@playwright/test";
import { accessible, eventIds, settled, signIn } from "./support";

// PD-F005-B02-T05: an organizer previews what a participant, a judge or the public would see, asked
// of the server and read-only; it is never an impersonation. It creates and publishes a form, so it
// runs on an isolated fixture.
const dialog = (page: Page) => page.getByRole("dialog");
const field = (id: string, label: string, visible_to: string[]) => ({
  id,
  type: "text",
  label,
  required: id === "pitch",
  visible_to,
});

async function makeForm(page: Page, name: string) {
  const { workspace, event } = await eventIds(page);
  const base = `/api/v1/workspaces/${workspace}/events/${event}`;
  const created = await page.request.post(`${base}/forms/`, { data: { name } });
  expect(created.status()).toBe(201);
  const form = (await created.json()).public_id as string;
  const schema = {
    fields: [
      field("pitch", "Pitch", ["participant", "judge", "organizer"]),
      field("repo", "Repository", ["participant"]),
      field("notes", "Judge notes", ["judge"]),
    ],
  };
  expect(
    (
      await page.request.put(`${base}/forms/${form}/`, { data: { schema } })
    ).status(),
  ).toBe(200);
  expect(
    (await page.request.post(`${base}/forms/${form}/publish/`)).status(),
  ).toBe(201);
  return { workspace, event, base };
}

async function openPreview(page: Page, who: string) {
  await page.locator(".cx-account summary").click();
  await page
    .locator(".cx-account__roles")
    .getByRole("button", { name: who, exact: true })
    .click();
  await expect(dialog(page)).toBeVisible();
}

for (const width of [1440, 390]) {
  test(`an organizer sees the form as each kind of person would and is never impersonating at ${width}`, async ({
    page,
  }, info) => {
    test.skip(info.project.name !== "desktop", "explicit viewport matrix");
    await page.setViewportSize({ width, height: 900 });
    await signIn(page, "organizer");
    const { workspace, event } = await makeForm(page, `Preview ${width}`);
    await page.goto(`/app/w/${workspace}/overview?event=${event}`);
    await settled(page);

    await openPreview(page, "Participant");
    await expect(
      dialog(page).getByRole("heading", { name: "Preview as participant" }),
    ).toBeVisible();
    await expect(dialog(page)).toContainText("Nothing is saved or sent");
    await expect(dialog(page)).toContainText("still signed in as");
    const rows = dialog(page).locator("tbody tr td:first-child");
    await expect(rows).toHaveText(["Pitch", "Repository"]);
    await expect(dialog(page)).toContainText(
      "1 of 3 fields are not shown to a participant.",
    );
    if (width === 390) {
      const b = (await dialog(page).boundingBox())!;
      expect(b.x).toBeGreaterThanOrEqual(0);
      expect(b.x + b.width).toBeLessThanOrEqual(390);
    }
    await accessible(page);

    // the same dialog, another kind of person
    await dialog(page).getByRole("radio", { name: "Judge" }).check();
    await expect(rows).toHaveText(["Pitch", "Judge notes"]);
    await dialog(page).getByRole("radio", { name: "Public" }).check();
    await expect(dialog(page)).toContainText(
      "No fields are shown to a public.",
    );
    const frame = dialog(page).locator("iframe");
    await expect(frame).toBeVisible();
    expect(await frame.getAttribute("sandbox")).toBe(""); // a picture of the page, not the page
    await expect(page.frameLocator("iframe").locator("body")).toContainText(
      /\S/,
    );

    // still the organizer to the server, and nothing was changed
    const dashboard = await page.request.get(
      `/api/v1/workspaces/${workspace}/events/${event}/dashboard/`,
    );
    expect(dashboard.status()).toBe(200);
    await page.keyboard.press("Escape");
    await expect(dialog(page)).toHaveCount(0);
    await expect(page.locator(".cx-account summary")).toBeVisible();
  });
}

test("the palette opens it, and a judge or a participant is never offered it", async ({
  page,
}) => {
  await signIn(page, "organizer");
  const { workspace, event } = await makeForm(page, "Palette preview");
  await page.goto(`/app/w/${workspace}/overview?event=${event}`);
  await settled(page);
  await page.keyboard.press("Control+k");
  await page.getByRole("combobox").fill("preview as judge");
  await page.getByRole("combobox").press("Enter");
  await expect(
    dialog(page).getByRole("heading", { name: "Preview as judge" }),
  ).toBeVisible();
  await expect(dialog(page).locator("tbody tr td:first-child")).toHaveText([
    "Pitch",
    "Judge notes",
  ]);
  await page.keyboard.press("Escape");
  await page.locator(".cx-account summary").click();
  await page.getByRole("button", { name: "Sign out", exact: true }).click();
  await expect(page.getByLabel("Username")).toBeVisible();

  for (const role of ["judge-01", "participant-01"]) {
    await signIn(page, role);
    await page.waitForLoadState("networkidle");
    await page.getByRole("button").filter({ hasText: /./ }).first().waitFor();
    const opened = await page.evaluate(() =>
      document.body.textContent?.includes("Preview as"),
    );
    if (opened) throw new Error(`${role} sees a preview control`);
    await page.request.post("/api/v1/accounts/logout/");
  }
});
