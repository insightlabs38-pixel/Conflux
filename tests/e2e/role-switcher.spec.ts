import { expect, test, type Page } from "@playwright/test";
import { account, eventIds, openWorkspace, settled, signIn } from "./support";

// PD-F005-B02-T04: a person who holds more than one role in a workspace chooses which to view it
// as, with a clear "viewing as" state, and the choice is a screen, never a permission. It grants a
// role through the real members endpoint, so it runs on an isolated fixture.
const roleLinks = (page: Page) => page.locator(".cx-account__roles a");
const railLink = (page: Page, id: string) =>
  page.locator(`#workspace-navigation a[href*="/${id}"]`);

async function grantSecondRole(page: Page) {
  await signIn(page, "organizer");
  const { workspace } = await eventIds(page);
  const username = account("organizer");
  const response = await page.request.post(
    `/api/v1/workspaces/${workspace}/members/`,
    { data: { username, role: "participant" } },
  );
  expect([200, 201]).toContain(response.status());
  return workspace;
}

for (const width of [1440, 390]) {
  test(`an organizer who is also a participant switches the view and always sees which at ${width}`, async ({
    page,
  }, info) => {
    test.skip(info.project.name !== "desktop", "explicit viewport matrix");
    await page.setViewportSize({ width, height: 900 });
    const workspace = await grantSecondRole(page);
    await page.goto(`/app/w/${workspace}/overview`);
    await settled(page);
    // the most privileged role by default, said in words
    await expect(page.locator(".cx-shell__context")).toContainText(
      "viewing as organizer",
    );
    await expect(railLink(page, "participants")).toHaveCount(1);
    await page.locator(".cx-account summary").click();
    await expect(roleLinks(page)).toHaveText(["Organizer", "Participant"]);
    await expect(roleLinks(page).first()).toHaveAttribute(
      "aria-current",
      "true",
    );
    await roleLinks(page).getByText("Participant").click();
    await expect(page).toHaveURL(/overview\?as=participant/);
    await expect(page.locator(".cx-shell__context")).toContainText(
      "viewing as participant",
    );
    await expect(railLink(page, "team")).toHaveCount(1);
    await expect(railLink(page, "participants")).toHaveCount(0);
    // every link keeps the role, a reload keeps it, Back returns to the organizer view
    await page.reload();
    await settled(page);
    await expect(page.locator(".cx-shell__context")).toContainText(
      "viewing as participant",
    );
    await page.goBack();
    await expect(page.locator(".cx-shell__context")).toContainText(
      "viewing as organizer",
    );
  });
}

test("viewing as another role changes the screen, not what the person may do", async ({
  page,
}) => {
  const workspace = await grantSecondRole(page);
  await page.goto(`/app/w/${workspace}/overview?as=participant`);
  await settled(page);
  await expect(page.locator(".cx-shell__context")).toContainText(
    "viewing as participant",
  );
  // still an organizer to the server: an organizer endpoint answers, a role never held is refused
  const { event } = await eventIds(page);
  const organizerOnly = await page.request.get(
    `/api/v1/workspaces/${workspace}/events/${event}/dashboard/`,
  );
  expect(organizerOnly.status()).toBe(200);
  // and a role the person does not hold is dropped from the URL, not shown
  await page.goto(`/app/w/${workspace}/overview?as=judge`);
  await settled(page);
  expect(new URL(page.url()).searchParams.get("as")).toBeNull();
  await expect(page.locator(".cx-shell__context")).toContainText(
    "viewing as organizer",
  );
});

test("the palette switches the role and the event switcher keeps it", async ({
  page,
}) => {
  const workspace = await grantSecondRole(page);
  const { event, name } = await eventIds(page);
  await page.goto(`/app/w/${workspace}/overview?event=${event}`);
  await settled(page);
  await page.keyboard.press("Control+k");
  await page.getByRole("combobox").fill("view as participant");
  await page.getByRole("combobox").press("Enter");
  await expect(page).toHaveURL(/as=participant/);
  await expect(page.locator(".cx-shell__context")).toContainText(
    "viewing as participant",
  );
  // switching event keeps who the person is viewing as
  await page.locator(".cx-switcher summary").click();
  await page.getByRole("link", { name }).click();
  expect(new URL(page.url()).searchParams.get("as")).toBe("participant");
  expect(new URL(page.url()).searchParams.get("event")).toBe(event);
});

test("a person with one role sees no role control and no viewing-as text", async ({
  page,
}) => {
  await signIn(page, "judge-01");
  await openWorkspace(page);
  await settled(page);
  await expect(page.locator(".cx-shell__context")).not.toContainText(
    "viewing as",
  );
  await page.locator(".cx-account summary").click();
  await expect(page.locator(".cx-account__roles")).toHaveCount(0);
});
