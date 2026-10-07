import { appHref, routes } from "../../lib/routes";
import { AppShell } from "../../components/AppShell";
import { PageHeader, ButtonLink } from "../../components/Foundation";
import {
  ProfileHeader,
  SkillTags,
  type PersonIdentity,
} from "../../components/Person";
import { LoadingState } from "../../components/LoadingState";
import { ErrorState } from "../../components/ErrorState";
import { useLoad } from "../../hooks/useLoad";
export function PersonProfilePage({ personId }: { personId: string }) {
  const {
    data,
    error: failure,
    loading,
    reload,
  } = useLoad<PersonIdentity>(
    `/api/v1/accounts/people/${encodeURIComponent(personId)}/`,
    {
      describe: (status) =>
        status === 404
          ? "This profile is private or unavailable."
          : `Could not load profile (${status}).`,
    },
  );
  const valid =
    data && typeof data.display_name === "string" && Array.isArray(data.links);
  const person = valid ? data : null;
  const error =
    failure?.message ?? (data && !valid ? "Invalid profile response." : "");
  return (
    <AppShell
      brandAs="p"
      nav={
        <ButtonLink href={appHref(routes.home)} variant="secondary">
          Open Conflux
        </ButtonLink>
      }
    >
      <PageHeader
        as="h1"
        title="Profile"
        description="Reusable identity shared by this person."
      />
      {loading && <LoadingState label="Loading profile…" />}
      {!loading && error && (
        <ErrorState kind="read" message={error} onRetry={reload} />
      )}{" "}
      {!loading && !error && person && (
        <ProfileHeader person={person} headingAs="h2">
          <SkillTags
            values={[
              ...(person.skills || []),
              ...(person.interests || []),
              ...(person.preferred_roles || []),
            ]}
          />
        </ProfileHeader>
      )}
    </AppShell>
  );
}
