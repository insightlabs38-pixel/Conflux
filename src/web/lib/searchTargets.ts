import targets from "./searchTargets.json";

/**
 * Where a hit of each queryable entity goes, and which of its fields names it. The keys are the
 * entities of the universal query engine (`core.entities`); `tests/integration/test_search_targets.py`
 * fails when an entity is registered without an entry here (or an entry names a field the entity
 * does not have), so a new entity forces a decision about how it is found and where it opens. The
 * file is JSON so the server test and the app read the same thing.
 */
export type SearchTarget = {
  noun: string;
  nouns: string;
  /** The text field searched with `contains` and shown as the hit's title. */
  labelField: string;
  /** A second field shown beside the title. */
  detailField?: string;
  /** The workspace view and its linkable section that list the entity. */
  view: string;
  section?: string;
};

export const SEARCH_TARGETS = targets as Record<string, SearchTarget>;
