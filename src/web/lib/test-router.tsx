import type { ReactElement } from "react";
import { QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter, Route, Routes } from "react-router";
import { createQueryClient } from "./query";

/** A query client for tests: production defaults except no retries, so failures surface at once. */
export const createTestQueryClient = () => createQueryClient({ retry: false });

/** Only the query client (no router), for components that use server state but not routing. */
export function withQuery(node: ReactElement): ReactElement {
  return (
    <QueryClientProvider client={createTestQueryClient()}>
      {node}
    </QueryClientProvider>
  );
}

/** Renders `node` inside a router (at a workspace URL) and a fresh query client, for component tests. */
export function withRouter(
  node: ReactElement,
  url = "/w/w/overview",
): ReactElement {
  return (
    <QueryClientProvider client={createTestQueryClient()}>
      <MemoryRouter initialEntries={[url]}>
        <Routes>
          <Route path="/w/:workspaceId/:view" element={node} />
          <Route path="*" element={node} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );
}
