import { execFileSync } from "node:child_process";
import { test as base } from "@playwright/test";
import { asFor, type As } from "./auth-states";
import { account, type Who } from "./support";

/**
 * Isolated browser fixtures (PD-B03-T02; contract in docs/operations/E2E.md). A fixture is a
 * generated demo scenario on a reserved seed (>= 10,000,000), built by the canonical
 * `manage.py e2e_fixture` command, so mutable specs never touch the shared seed-7 reference.
 *
 * E2E_MANAGE overrides how manage.py is reached (default: the one shared compose stack);
 * E2E_KEEP_FIXTURES=1 keeps every fixture for inspection. Failed specs always keep theirs.
 */
export type Profile = "iso-min" | "iso-judged" | "iso-published" | "canary";
export type Fixture = Who & {
  profile: Profile;
  slug: string;
  workspace: string;
  event: string;
  seed: number;
  account(label: string): string;
};

const manage = (...args: string[]): string => {
  const prefix = (
    process.env.E2E_MANAGE ?? "docker compose exec -T app python manage.py"
  ).split(" ");
  try {
    return execFileSync(prefix[0], [...prefix.slice(1), ...args], {
      encoding: "utf8",
      stdio: ["ignore", "pipe", "pipe"],
    }).trim();
  } catch (error) {
    const stderr = String((error as { stderr?: Buffer }).stderr ?? "").trim();
    throw new Error(
      `e2e_fixture ${args.join(" ")} failed: ${stderr.split("\n").pop() ?? error}`,
    );
  }
};

export function provisionFixture(profile: Profile): Fixture {
  const raw = JSON.parse(
    manage("e2e_fixture", "create", profile).split("\n").pop() ?? "{}",
  );
  return {
    ...raw,
    profile,
    account: (label: string) => account(label, raw.seed),
  };
}

export const disposeFixture = (slug: string): string =>
  manage("e2e_fixture", "dispose", slug);

/** Test with a worker-scoped `fixture` of the chosen profile: created before the first test in
 * the worker, disposed after the last one unless something failed. */
export function isolatedTest(profile: Profile) {
  const failed = new Set<string>();
  return base.extend<{ _track: void; as: As }, { fixture: Fixture }>({
    as: async ({ browser, context, page, fixture }, use) =>
      asFor(fixture)({ browser, context, page }, use),
    fixture: [
      async ({}, use, workerInfo) => {
        const fixture = provisionFixture(profile);
        await use(fixture);
        if (process.env.E2E_KEEP_FIXTURES || failed.has(fixture.slug))
          console.log(
            `kept fixture ${fixture.slug} (worker ${workerInfo.workerIndex}); ` +
              `remove with: manage.py e2e_fixture dispose ${fixture.slug}`,
          );
        else disposeFixture(fixture.slug);
      },
      { scope: "worker" },
    ],
    _track: [
      async ({ fixture }, use, testInfo) => {
        await use();
        if (testInfo.status !== testInfo.expectedStatus)
          failed.add(fixture.slug);
      },
      { auto: true },
    ],
  });
}
