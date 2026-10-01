import { expect, test } from "@playwright/test";
import {
  accessible,
  goToDestination,
  goToTask,
  noHorizontalOverflow,
  openWorkspace,
  settled,
  signIn,
} from "./support";

// The shared rich-content primitive (PD-F002-B02-T02): the participant's project story has a
// preview rendered by the server from the same rules the public page uses. Hostile text is shown
// as text, an oversize text is refused with the reason, and previewing saves nothing. It writes
// (the save at the end), so it runs on an isolated fixture.
const STORY = [
  "# Build notes",
  "",
  "Uses `pytest` and [the repo](https://example.com/repo).",
  "",
  "| Tool | Role |",
  "| --- | --- |",
  "| Python | API |",
  "",
  "```python",
  "print('ready')",
  "```",
  "",
  "<script>window.__pwned = true</script> [bad](javascript:window.__pwned=true) [old](ftp://example.com/x)",
].join("\n");

for (const width of [390, 1440]) {
  test(`the project story previews what the server will keep at ${width}`, async ({
    page,
  }, info) => {
    test.skip(info.project.name !== "desktop", "explicit viewport matrix");
    await page.setViewportSize({ width, height: 900 });
    await signIn(page, "participant-01");
    await openWorkspace(page);
    await page
      .getByRole("combobox", { name: "Event", exact: true })
      .selectOption({ index: 1 });
    await settled(page);
    await goToDestination(page, "project");
    await page
      .getByRole("combobox", { name: "Project", exact: true })
      .selectOption({ index: 1 });
    await goToTask(page, "Project story");
    const story = page.getByLabel("Project description", { exact: true });
    const preview = page.getByRole("button", { name: "Preview", exact: true });
    const region = page.getByRole("region", {
      name: "Project description preview",
    });
    const writes: string[] = [];
    page.on("request", (request) => {
      if (
        request.method() !== "GET" &&
        !request.url().includes("/rich/preview/")
      )
        writes.push(`${request.method()} ${request.url()}`);
    });

    // Empty text has nothing to preview, and says so without asking the server.
    await story.fill("");
    await preview.click();
    await expect(page.getByText("Nothing to preview yet.")).toBeVisible();

    // Markdown is drawn from the server's tree; hostile text stays text.
    await story.fill(STORY);
    await expect(
      region.getByRole("heading", { name: "Build notes" }),
    ).toBeVisible();
    await expect(
      region.getByRole("link", { name: "the repo" }),
    ).toHaveAttribute("href", "https://example.com/repo");
    await expect(
      region.getByRole("columnheader", { name: "Tool" }),
    ).toBeVisible();
    await expect(
      region.getByRole("group", { name: "python code" }),
    ).toContainText("print('ready')");
    await expect(region).toContainText(
      "<script>window.__pwned = true</script>",
    );
    await expect(region).toContainText("[bad](javascript:window.__pwned=true)");
    await expect(region).toContainText("[old](ftp://example.com/x)");
    await expect(
      region.locator("script, a[href^='javascript'], a[href^='ftp']"),
    ).toHaveCount(0);
    expect(await page.evaluate(() => "__pwned" in window)).toBe(false);
    await noHorizontalOverflow(page);
    await accessible(page);

    // Too long: refused with the reason; the text box keeps the text.
    await story.fill("x".repeat(100_001));
    await expect(
      page.getByRole("alert").filter({ hasText: "100,000" }),
    ).toBeVisible();
    await expect(story).toHaveValue("x".repeat(100_001));
    await accessible(page);

    // Previewing saved nothing; saving does, and the saved text previews the same after a reload.
    expect(writes).toEqual([]);
    await story.fill(STORY);
    await page
      .getByRole("button", { name: "Save project story", exact: true })
      .click();
    await expect(
      page.getByText("Project story saved.", { exact: true }),
    ).toBeVisible();
    await page.reload();
    await settled(page);
    await goToDestination(page, "project");
    await page
      .getByRole("combobox", { name: "Project", exact: true })
      .selectOption({ index: 1 });
    await goToTask(page, "Project story");
    await expect(story).toHaveValue(STORY);
    await page.getByRole("button", { name: "Preview", exact: true }).click();
    await expect(
      region.getByRole("heading", { name: "Build notes" }),
    ).toBeVisible();
  });
}
