import type { ReactElement } from "react";
import { MemoryRouter, Route, Routes } from "react-router";

/** Renders `node` inside a router at a workspace URL, for component tests that need routing context. */
export function withRouter(
  node: ReactElement,
  url = "/w/w/overview",
): ReactElement {
  return (
    <MemoryRouter initialEntries={[url]}>
      <Routes>
        <Route path="/w/:workspaceId/:view" element={node} />
        <Route path="*" element={node} />
      </Routes>
    </MemoryRouter>
  );
}
