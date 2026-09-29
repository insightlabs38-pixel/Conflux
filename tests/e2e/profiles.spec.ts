import { expect, test } from "@playwright/test";
import {
  accessible,
  goToDestination,
  noHorizontalOverflow,
  openWorkspace,
  signIn,
} from "./support";

for (const width of [390, 1440]) {
  test(`profile editing and reusable public identity at ${width}`, async ({
    page,
    browser,
  }, info) => {
    test.skip(info.project.name !== "desktop", "explicit viewport matrix");
    await page.setViewportSize({ width, height: 900 });
    await signIn(page, "participant-01");
    await openWorkspace(page);
    const original = await (
      await page.request.get("/api/v1/accounts/profile/")
    ).json();
    const restore = Object.fromEntries(
      [
        "display_name",
        "avatar_url",
        "bio",
        "location",
        "links",
        "visibility",
        "skills",
        "interests",
        "preferred_roles",
      ].map((key) => [key, original[key]]),
    );
    try {
      await goToDestination(page, "profile");
      await expect(
        page.getByRole("region", { name: "Your profile", exact: true }),
      ).toBeVisible();
      await page.getByText("Edit your profile", { exact: true }).click();
      await page
        .getByLabel("Display name", { exact: true })
        .fill("Alex Rivera — Open Systems Builder");
      await page
        .getByLabel("Short bio", { exact: true })
        .fill("Building practical tools for collaborative events.");
      await page
        .getByLabel("Location (optional)", { exact: true })
        .fill("Berlin");
      await page
        .getByLabel("Profile visibility", { exact: true })
        .selectOption("public");
      await page
        .getByRole("form", { name: "Edit profile" })
        .getByLabel("Skills, separated by commas", { exact: true })
        .fill("Python, TypeScript");
      await page
        .getByRole("form", { name: "Edit profile" })
        .getByLabel("Interests, separated by commas", { exact: true })
        .fill("Open systems");
      await page
        .getByRole("form", { name: "Edit profile" })
        .getByLabel("Preferred roles, separated by commas", { exact: true })
        .fill("Builder");
      await page.getByRole("button", { name: "Add link", exact: true }).click();
      await page.getByLabel("Link 1 label", { exact: true }).fill("GitHub");
      await page
        .getByLabel("Link 1 URL", { exact: true })
        .fill("https://github.com/example");
      await accessible(page);
      await noHorizontalOverflow(page);
      await page
        .getByRole("button", { name: "Save profile", exact: true })
        .click();
      await expect(
        page.getByRole("status").filter({ hasText: "Profile saved." }),
      ).toBeVisible();
      await expect(
        page.getByRole("heading", {
          name: "Alex Rivera — Open Systems Builder",
          exact: true,
        }),
      ).toBeVisible();
      const updated = await (
        await page.request.get("/api/v1/accounts/profile/")
      ).json();
      expect(updated.username).toBe(original.username);
      expect(updated.skills).toEqual(["Python", "TypeScript"]);
      await page.screenshot({
        path: `tests/e2e/artifacts/uiv2-b04/profile-${width}.png`,
        fullPage: true,
      });
      await goToDestination(page, "team");
      await goToDestination(page, "profile");
      await expect(
        page.getByLabel("Display name", { exact: true }),
      ).toHaveValue("Alex Rivera — Open Systems Builder");
      const visitor = await browser.newContext({
        baseURL: info.project.use.baseURL,
        viewport: { width, height: 900 },
      });
      const publicPage = await visitor.newPage();
      await publicPage.goto(`/app/?person=${updated.user_public_id}`);
      await expect(
        publicPage.getByRole("heading", {
          name: "Alex Rivera — Open Systems Builder",
          exact: true,
        }),
      ).toBeVisible();
      await expect(
        publicPage.getByRole("link", { name: "GitHub", exact: true }),
      ).toHaveAttribute("href", "https://github.com/example");
      await accessible(publicPage);
      await noHorizontalOverflow(publicPage);
      await publicPage.screenshot({
        path: `tests/e2e/artifacts/uiv2-b04/person-${width}.png`,
        fullPage: true,
      });
      expect(
        (await publicPage.request.get("/api/v1/accounts/profile/")).status(),
      ).toBe(401);
      await visitor.close();
    } finally {
      expect(
        (
          await page.request.patch("/api/v1/accounts/profile/", {
            data: restore,
          })
        ).ok(),
      ).toBe(true);
    }
  });
}
