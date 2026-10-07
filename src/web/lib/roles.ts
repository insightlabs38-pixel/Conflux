/**
 * The roles a person can hold in a workspace and which one a screen is built for. A person may hold
 * several (the account API returns one membership per role); the URL's `as` context param says which
 * of *their own* roles to view as, so it is a choice of screen, never a grant: the server still
 * authorizes every request against what the person really holds.
 */
export const ROLES = [
  "organizer",
  "admin",
  "judge",
  "mentor",
  "volunteer",
  "participant",
] as const;
export type Role = (typeof ROLES)[number];

export const roleLabel = (role: string) =>
  role === "admin"
    ? "Organizer (admin)"
    : role.charAt(0).toUpperCase() + role.slice(1);

type Membership = { workspace: string; role: string };

/** The workspace's roles the person holds, most privileged first, each once. */
export function rolesIn(
  memberships: Membership[] | undefined,
  workspaceId: string,
): Role[] {
  const held = new Set(
    (memberships ?? [])
      .filter((m) => m.workspace === workspaceId)
      .map((m) => m.role),
  );
  return ROLES.filter((role) => held.has(role));
}

/**
 * The role to show: the requested one when the person holds it, otherwise the most privileged they
 * hold. `requestedUnheld` is true when a role was asked for that they do not have, so the caller can
 * drop it from the URL.
 */
export function pickRole(
  roles: Role[],
  requested: string,
): { role: Role | null; requestedUnheld: boolean } {
  const asked = roles.find((role) => role === requested);
  return {
    role: asked ?? roles[0] ?? null,
    requestedUnheld: requested !== "" && !asked,
  };
}
