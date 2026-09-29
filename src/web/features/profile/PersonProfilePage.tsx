import { useEffect, useState } from "react";
import { AppShell } from "../../components/AppShell";
import { PageHeader, ButtonLink } from "../../components/Foundation";
import {
  ProfileHeader,
  SkillTags,
  type PersonIdentity,
} from "../../components/Person";
import { LoadingState } from "../../components/LoadingState";
import { ErrorState } from "../../components/ErrorState";
export function PersonProfilePage({ personId }: { personId: string }) {
  const [person, setPerson] = useState<PersonIdentity | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    let active = true;
    setLoading(true);
    setError("");
    fetch(`/api/v1/accounts/people/${encodeURIComponent(personId)}/`, {
      credentials: "include",
    })
      .then(async (response) => {
        if (!response.ok)
          throw new Error(
            response.status === 404
              ? "This profile is private or unavailable."
              : `Could not load profile (${response.status}).`,
          );
        const data = (await response.json()) as PersonIdentity;
        if (typeof data.display_name !== "string" || !Array.isArray(data.links))
          throw new Error("Invalid profile response.");
        if (active) setPerson(data);
      })
      .catch((cause) => {
        if (active)
          setError(
            cause instanceof Error ? cause.message : "Could not load profile.",
          );
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [personId, retry]);
  return (
    <AppShell
      brandAs="p"
      nav={
        <ButtonLink href="/app/" variant="secondary">
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
        <ErrorState
          message={error}
          onRetry={() => setRetry((value) => value + 1)}
        />
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
