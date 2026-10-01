/**
 * The client half of the extensions inventory (PD-F002-B02-T08). The server declares what this
 * deployment's code provides and checks the declarations against the live registries
 * (`core/manifest.py`); the browser only lists it. There is nothing to install, enable or edit.
 */
export type ExtensionState = "live" | "declared" | "missing";

export type ManifestEntry = {
  kind: string;
  id: string;
  label: string;
  state: ExtensionState;
};

export type Manifest = {
  id: string;
  version: string;
  label: string;
  api_version: number;
  provides: ManifestEntry[];
  requires: { kind: string; id: string }[];
};

export type Capability = {
  kind: string;
  label: string;
  description: string;
  /** No runtime registry backs it, so it is listed from the declarations only. */
  declared_only: boolean;
  entries: { id: string; label: string; manifest: string | null }[];
};

export type ExtensionProblem = {
  code: string;
  severity: "error" | "warning";
  manifest: string | null;
  message: string;
};

export type Extensions = {
  api_version: number;
  supported_api_versions: number[];
  manifests: Manifest[];
  capabilities: Capability[];
  problems: ExtensionProblem[];
  ok: boolean;
};

export const extensionsUrl = (workspaceId: string) =>
  `/api/v1/workspaces/${workspaceId}/extensions/`;

/** "communications requires core" for a requirement of one source on another. */
export const requirementText = (r: { kind: string; id: string }): string =>
  r.kind === "manifest" ? r.id : `${r.kind}: ${r.id}`;
