import { expect, test, type Page } from "@playwright/test";
import {
  accessible,
  goToDestination,
  goToTask,
  openWorkspace,
  signIn,
} from "./support";

// Async-operation contract (PD-B04-T05; hooks/useOperation.ts) in a real browser: progress, cancel
// that really aborts the transfer, a failed part as an alert with a retry. The upload intent and the
// storage PUTs are stubbed at the network edge so this stays read-only on the shared demo event;
// the real create -> upload -> validate path is the lifecycle canary.
test.skip(
  ({ isMobile }) => isMobile,
  "operation contract; viewport independent",
);

async function openEvidence(page: Page) {
  await signIn(page, "participant-01");
  await openWorkspace(page);
  await page
    .getByRole("combobox", { name: "Event", exact: true })
    .selectOption({ index: 1 });
  await goToDestination(page, "project");
  await page
    .getByRole("combobox", { name: "Project", exact: true })
    .selectOption({ index: 1 });
  await goToTask(page, "Evidence & checks");
  const evidence = page.getByRole("region", { name: "Project artifacts" });
  await expect(evidence).toBeVisible();
  return evidence;
}

async function chooseFile(evidence: ReturnType<Page["getByRole"]>) {
  await evidence.getByLabel("Title").first().fill("Operation contract proof");
  await evidence.locator('input[type="file"]').setInputFiles({
    name: "proof.txt",
    mimeType: "text/plain",
    buffer: Buffer.from("abcdef"),
  });
}

function stubIntent(page: Page) {
  const intents: string[] = [];
  return page
    .route("**/artifacts/upload-intents/", (route) => {
      intents.push(route.request().url());
      return route.fulfill({
        status: 201,
        contentType: "application/json",
        body: JSON.stringify({
          artifact: { public_id: "stub-artifact" },
          intent: "stub-intent",
          upload: {
            mode: "multipart",
            urls: [
              "http://storage.invalid/part-1",
              "http://storage.invalid/part-2",
            ],
            part_size: 3,
          },
        }),
      });
    })
    .then(() => intents);
}

test("a running upload shows progress and Cancel aborts the transfer without completing anything", async ({
  page,
}) => {
  const evidence = await openEvidence(page);
  const intents = await stubIntent(page);
  let partRequests = 0;
  let completed = false;
  await page.route("http://storage.invalid/**", () => {
    partRequests++; // held: never answered until the page aborts it
  });
  await page.route("**/upload-intents/*/complete/", (route) => {
    completed = true;
    return route.abort();
  });
  await chooseFile(evidence);
  await evidence.getByRole("button", { name: "Upload", exact: true }).click();

  const status = evidence
    .getByRole("status")
    .filter({ hasText: "Uploading part 1 of 2" });
  await expect(status).toBeVisible();
  await expect(status).toHaveAttribute("aria-busy", "true");
  await expect(status.getByRole("progressbar")).toHaveAttribute("max", "2");
  await expect(
    evidence.getByRole("button", { name: "Upload", exact: true }),
  ).toBeDisabled();
  expect(intents).toHaveLength(1);
  await accessible(page); // the pending state is announced and labelled

  await status.getByRole("button", { name: "Cancel" }).click();
  await expect(evidence.getByText(/^Cancelled\./)).toBeVisible();
  await expect(evidence.getByRole("alert")).toHaveCount(0);
  await expect(
    evidence.getByRole("button", { name: "Upload", exact: true }),
  ).toBeEnabled();
  expect(partRequests).toBe(1);
  expect(completed).toBe(false);
});

test("a failed part is an alert with the reason, and Try again starts a fresh attempt", async ({
  page,
}) => {
  const evidence = await openEvidence(page);
  const intents = await stubIntent(page);
  await page.route("http://storage.invalid/**", (route) =>
    route.fulfill({ status: 503, body: "busy" }),
  );
  await chooseFile(evidence);
  await evidence.getByRole("button", { name: "Upload", exact: true }).click();
  await expect(evidence.getByRole("alert")).toContainText(
    "Part 1 failed (503)",
  );
  expect(intents).toHaveLength(1);
  await evidence.getByRole("button", { name: "Try again" }).click();
  await expect.poll(() => intents.length).toBe(2);
  await expect(evidence.getByRole("alert")).toContainText(
    "Part 1 failed (503)",
  );
});
