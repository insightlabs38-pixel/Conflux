import { useEffect, useId, useMemo, useState } from "react";
import { Link, useLocation } from "react-router";
import { useMe } from "../hooks/useMe";
import { useShellEvents } from "../hooks/useShellEvents";
import { discardDraft, useDrafts, type DraftInfo } from "../lib/drafts";
import { placeKey, placeOf, shareableTarget } from "../lib/shareLink";
import { setWorkspaceTabs, useWorkspaceTabs } from "../lib/shellPreferences";
import { Modal } from "./Modal";
import { useWorkspaceNavigation } from "./WorkspaceNavigation";

type Tab = { id: string; to: string; label: string; drafts: DraftInfo[] };

/**
 * The places a person keeps open in this workspace, with a mark on the ones that hold unsaved work
 * (spec 005, PD-F005-B03-T02). Absent until there is something to show: a tab exists because the
 * person kept the place open (palette: Keep this place open) or because it holds a draft. Each tab
 * opens where that place was left. Closing one that holds a draft asks first and says what is lost.
 */
export function WorkspaceTabs() {
  const navigation = useWorkspaceNavigation();
  const location = useLocation();
  const user = useMe().data?.public_id ?? "";
  const workspaceId = navigation?.workspaceId ?? "";
  const kept = useWorkspaceTabs(user, workspaceId);
  const drafts = useDrafts(workspaceId);
  const { events } = useShellEvents(workspaceId, navigation?.role ?? "");
  const [closing, setClosing] = useState<Tab | null>(null);
  const titleId = useId();

  // a kept tab follows its person: it reopens at the last place they were in it
  const here = shareableTarget(location.pathname, location.search);
  useEffect(() => {
    if (!here || !user) return;
    const at = kept.findIndex((to) => placeKey(to) === placeKey(here));
    if (at >= 0 && kept[at] !== here)
      setWorkspaceTabs(
        user,
        workspaceId,
        kept.map((to, index) => (index === at ? here : to)),
      );
  }, [here, kept, user, workspaceId]);

  const tabs: Tab[] = useMemo(() => {
    const out = new Map<string, Tab>();
    const add = (to: string, draft?: DraftInfo) => {
      const place = placeOf(to);
      if (!place) return;
      const id = placeKey(to);
      const existing = out.get(id);
      if (existing) {
        if (draft) existing.drafts.push(draft);
        return;
      }
      const name = events.find(
        (event) => event.public_id === place.event,
      )?.name;
      const destination = navigation?.destinations.find(
        (item) => item.id === place.view,
      );
      out.set(id, {
        id,
        to,
        label: `${destination?.label ?? place.view}${name ? ` · ${name}` : ""}`,
        drafts: draft ? [draft] : [],
      });
    };
    for (const to of kept) add(to);
    for (const draft of drafts) add(draft.to, draft);
    return [...out.values()];
  }, [kept, drafts, events, navigation]);

  if (!navigation || tabs.length === 0) return null;
  const close = (tab: Tab) => {
    for (const draft of tab.drafts) discardDraft(workspaceId, draft.scope);
    setWorkspaceTabs(
      user,
      workspaceId,
      kept.filter((to) => placeKey(to) !== tab.id),
    );
    setClosing(null);
  };
  return (
    <nav className="cx-tabs" aria-label="Open places">
      <ul>
        {tabs.map((tab) => {
          const current = !!here && placeKey(here) === tab.id;
          return (
            <li key={tab.id} data-current={current || undefined}>
              <Link to={tab.to} aria-current={current ? "page" : undefined}>
                {tab.label}
                {tab.drafts.length > 0 && (
                  <>
                    <span className="cx-tabs__dirty" aria-hidden="true">
                      ●
                    </span>
                    <span className="cx-visually-hidden">
                      , unsaved changes
                    </span>
                  </>
                )}
              </Link>
              <button
                type="button"
                aria-label={`Close ${tab.label}`}
                onClick={() =>
                  tab.drafts.length ? setClosing(tab) : close(tab)
                }
              >
                ×
              </button>
            </li>
          );
        })}
      </ul>
      {closing && (
        <Modal titleId={titleId} onClose={() => setClosing(null)}>
          <h2 id={titleId}>Close {closing.label}?</h2>
          <p>
            This place has unsaved changes (
            {closing.drafts.map((d) => d.label).join(", ")}). Closing it
            discards them.
          </p>
          <div className="cx-consequence__actions">
            <button type="button" onClick={() => setClosing(null)}>
              Keep editing
            </button>
            <button type="button" onClick={() => close(closing)}>
              Discard and close
            </button>
          </div>
        </Modal>
      )}
    </nav>
  );
}
