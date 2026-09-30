import { describe, expect, it } from "vitest";

/**
 * Ratchet for the server-state migration (PD-B04-T07): a screen loads server data with `useLoad` /
 * `useQuery` (hooks/useLoad.ts), not with a hand-written `useEffect` that requests and then sets
 * state. The files below are the ones not migrated yet, each for a stated reason; the count per
 * file may only go down. A new effect-based fetch anywhere fails this test.
 */
const sources = import.meta.glob(
  ["../**/*.{ts,tsx}", "!../**/*.test.{ts,tsx}"],
  {
    query: "?raw",
    import: "default",
    eager: true,
  },
) as Record<string, string>;

// Effects whose body calls the network (directly or through a local request/load/refresh helper).
const CALL =
  /\b(apiJson|apiRequest|readJson|request|refresh|load|fetch)\s*(<[^>]*>)?\(/;

export function fetchingEffects(source: string): number {
  let count = 0;
  for (const match of source.matchAll(/useEffect\(/g)) {
    let depth = 1;
    let index = (match.index ?? 0) + match[0].length;
    const start = index;
    while (depth && index < source.length) {
      if (source[index] === "(") depth++;
      else if (source[index] === ")") depth--;
      index++;
    }
    if (CALL.test(source.slice(start, index))) count++;
  }
  return count;
}

/** Not migrated, with the reason. Only ever decrease these numbers or delete entries. */
const remaining: Record<string, { effects: number; why: string }> = {
  // Editors whose form state is seeded from the server and edited as a draft.
  "../features/event-builder/RegistrationPanel.tsx": {
    effects: 1,
    why: "draft form seeded from server",
  },
  "../features/form-builder/FormBuilder.tsx": {
    effects: 1,
    why: "editor draft",
  },
  "../features/form-builder/ProjectForms.tsx": {
    effects: 1,
    why: "participant form draft",
  },
  "../features/page-builder/PageBuilder.tsx": {
    effects: 1,
    why: "editor draft",
  },
  "../features/policy-builder/PolicyBuilder.tsx": {
    effects: 1,
    why: "editor draft",
  },
  "../features/stage-builder/StageBuilder.tsx": {
    effects: 1,
    why: "editor draft",
  },
  "../features/judging/EvaluationBuilder.tsx": {
    effects: 4,
    why: "rubric/pool editors with drafts",
  },
  "../features/judging/JudgeExpertisePanel.tsx": {
    effects: 1,
    why: "draft seeded from server",
  },
  "../features/profile/ProfilePanel.tsx": {
    effects: 1,
    why: "profile draft seeded from server",
  },
  "../features/awards/AwardsPanel.tsx": { effects: 1, why: "editor draft" },
  "../features/teams/MarketplacePanel.tsx": { effects: 1, why: "editor draft" },
  "../features/community-voting/CommunityVotingBuilder.tsx": {
    effects: 1,
    why: "editor draft",
  },
  // Paginated or appended feeds need an infinite-query contract.
  "../features/communications/CommunicationsPanel.tsx": {
    effects: 1,
    why: "feeds appended locally",
  },
  "../features/community-voting/FraudReview.tsx": {
    effects: 1,
    why: "paginated signals",
  },
  "../features/integrations/WebhooksPanel.tsx": {
    effects: 1,
    why: "paginated deliveries",
  },
  // Deliberately manual.
  "../features/judging/JudgeWorkspace.tsx": {
    effects: 1,
    why: "offline queue cache and outbox (PlanQueue)",
  },
  "../features/api-explorer/ApiExplorer.tsx": {
    effects: 1,
    why: "public schema read, credentials omitted",
  },
};

describe("server-state migration ratchet", () => {
  it("scans the application sources", () => {
    expect(Object.keys(sources).length).toBeGreaterThan(50);
  });

  it("has no effect-based fetching outside the recorded files", () => {
    const found = Object.fromEntries(
      Object.entries(sources)
        .map(([file, text]) => [file, fetchingEffects(text)] as const)
        .filter(([, count]) => count > 0),
    );
    const unexpected = Object.entries(found).filter(
      ([file, count]) => count > (remaining[file]?.effects ?? 0),
    );
    expect(unexpected).toEqual([]);
  });

  it("keeps the record honest (an entry that no longer fetches must be deleted)", () => {
    const stale = Object.entries(remaining).filter(
      ([file]) => fetchingEffects(sources[file] ?? "") === 0,
    );
    expect(stale.map(([file]) => file)).toEqual([]);
  });

  it("recognizes the pattern it forbids", () => {
    expect(
      fetchingEffects("useEffect(() => { apiJson<X>(url).then(setX); }, [])"),
    ).toBe(1);
    expect(
      fetchingEffects("useEffect(() => { document.title = 'x'; }, [])"),
    ).toBe(0);
  });
});
