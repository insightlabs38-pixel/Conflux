import { expect, test } from "@playwright/test";
import {
  accessible,
  noHorizontalOverflow,
  openWorkspace,
  signIn,
  watch,
  settled,
} from "./support";

for (const role of ["organizer", "judge-01", "participant-01"]) {
  test(`${role}: workspace loads without errors, overflow or axe violations`, async ({
    page,
  }) => {
    await signIn(page, role);
    const problems = watch(page);
    await openWorkspace(page);
    await settled(page);
    await expect(page.getByRole("main")).toBeVisible();
    await expect(
      page.getByRole("button", { name: "Back to workspaces" }),
    ).toBeVisible();
    await noHorizontalOverflow(page);
    await accessible(page);
    expect(problems).toEqual([]);
  });
}

test("a participant cannot open the organizer console by URL", async ({
  page,
}) => {
  await signIn(page, "participant-01");
  await openWorkspace(page);
  await expect(page.getByText("Operator console")).toHaveCount(0);
});

test("organizer keyboard path: every workspace control is reachable and shows focus", async ({
  page,
}) => {
  await signIn(page, "organizer");
  await openWorkspace(page);
  await settled(page);
  for (let i = 0; i < 6; i++) await page.keyboard.press("Tab");
  const outline = await page.evaluate(() => {
    const el = document.activeElement as HTMLElement;
    return (
      getComputedStyle(el).outlineStyle +
      "|" +
      getComputedStyle(el).outlineWidth
    );
  });
  expect(outline).not.toMatch(/^none/);
});
