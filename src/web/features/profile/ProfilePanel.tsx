import { useEffect, useState, type FormEvent } from "react";
import { Button } from "../../components/Button";
import {
  Field,
  TextInput,
  TextArea,
  Select,
} from "../../components/Foundation";
import { ErrorState } from "../../components/ErrorState";
import { LoadingState } from "../../components/LoadingState";
import {
  ProfileHeader,
  SkillTags,
  type PersonIdentity,
} from "../../components/Person";
import { Badge } from "../../components/Badge";

type Profile = PersonIdentity & {
  visibility: "private" | "members" | "public";
  event_profiles: {
    event: string;
    event_name: string;
    skills: string[];
    roles: string[];
    interests: string[];
    team_seeking: boolean;
    availability_hours_per_week: number | null;
  }[];
  judge_expertise: { workspace: string; tags: string[] }[];
  mentoring: {
    event_name: string;
    headline: string;
    available: boolean;
    tracks: string[];
  }[];
};
async function request(method = "GET", body?: object): Promise<Profile> {
  const response = await fetch("/api/v1/accounts/profile/", {
    method,
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!response.ok) {
    const data = await response.json().catch(() => null);
    throw new Error(
      data
        ? Object.entries(data)
            .map(
              ([key, value]) =>
                `${key}: ${Array.isArray(value) ? value.join(" ") : JSON.stringify(value)}`,
            )
            .join(" ")
        : `Profile request failed (${response.status}).`,
    );
  }
  const data = (await response.json()) as Profile;
  if (
    !data ||
    typeof data.display_name !== "string" ||
    typeof data.username !== "string" ||
    !Array.isArray(data.links) ||
    !Array.isArray(data.event_profiles) ||
    !Array.isArray(data.judge_expertise) ||
    !Array.isArray(data.mentoring)
  )
    throw new Error("Invalid profile response.");
  return data;
}
export function ProfilePanel() {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [draft, setDraft] = useState<Profile | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [saved, setSaved] = useState(false);
  const [retry, setRetry] = useState(0);
  const [skillText, setSkillText] = useState("");
  const [interestText, setInterestText] = useState("");
  const [roleText, setRoleText] = useState("");
  useEffect(() => {
    let active = true;
    setLoading(true);
    setError("");
    request()
      .then((value) => {
        if (active) {
          setProfile(value);
          setDraft(value);
          setSkillText((value.skills || []).join(", "));
          setInterestText((value.interests || []).join(", "));
          setRoleText((value.preferred_roles || []).join(", "));
        }
      })
      .catch((cause) => {
        if (active)
          setError(String(cause instanceof Error ? cause.message : cause));
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [retry]);
  async function save(event: FormEvent) {
    event.preventDefault();
    if (!draft) return;
    setBusy(true);
    setError("");
    setSaved(false);
    try {
      const value = await request("PATCH", {
        display_name: draft.display_name,
        avatar_url: draft.avatar_url,
        bio: draft.bio,
        location: draft.location,
        links: draft.links.filter((link) => link.label || link.url),
        visibility: draft.visibility,
        skills: skillText
          .split(",")
          .map((value) => value.trim())
          .filter(Boolean),
        interests: interestText
          .split(",")
          .map((value) => value.trim())
          .filter(Boolean),
        preferred_roles: roleText
          .split(",")
          .map((value) => value.trim())
          .filter(Boolean),
      });
      setProfile(value);
      setDraft(value);
      setSaved(true);
    } catch (cause) {
      setError(
        cause instanceof Error ? cause.message : "Could not save profile.",
      );
    } finally {
      setBusy(false);
    }
  }
  if (loading) return <LoadingState label="Loading profile…" />;
  if (!profile || !draft)
    return (
      <ErrorState
        message={error || "Could not load profile."}
        onRetry={() => setRetry((value) => value + 1)}
      />
    );
  const tags = [
    ...(profile.skills || []),
    ...(profile.interests || []),
    ...(profile.preferred_roles || []),
  ];
  const update = (key: keyof Profile, value: string) => {
    setSaved(false);
    setDraft((current) => (current ? { ...current, [key]: value } : current));
  };
  return (
    <section aria-label="Your profile" className="cx-profile">
      <ProfileHeader person={profile}>
        <Badge>
          {profile.visibility === "members"
            ? "Shared workspace members"
            : `${profile.visibility} profile`}
        </Badge>
        <SkillTags values={tags} />
      </ProfileHeader>
      <details className="cx-profile-editor">
        <summary>Edit your profile</summary>
        <form onSubmit={save} aria-label="Edit profile">
          <fieldset disabled={busy}>
            <legend>Reusable identity</legend>
            <p>
              Your sign-in username stays the same. Visibility controls who can
              see this identity; event matching preferences remain managed in
              each event.
            </p>
            <div className="cx-grid">
              {(
                [
                  ["display_name", "Display name", 120],
                  ["location", "Location (optional)", 120],
                  ["avatar_url", "Avatar image URL (optional)", 2048],
                ] as const
              ).map(([key, label, maxLength]) => (
                <Field key={key} label={label}>
                  {(props) => (
                    <TextInput
                      {...props}
                      value={draft[key]}
                      maxLength={maxLength}
                      type={key === "avatar_url" ? "url" : "text"}
                      onChange={(event) => update(key, event.target.value)}
                    />
                  )}
                </Field>
              ))}
              <Field
                label="Profile visibility"
                hint="Private: only you. Members: people sharing a workspace. Public: anyone with your profile link."
              >
                {(props) => (
                  <Select
                    {...props}
                    value={draft.visibility}
                    onChange={(event) =>
                      update("visibility", event.target.value)
                    }
                  >
                    <option value="private">Private</option>
                    <option value="members">Shared workspace members</option>
                    <option value="public">Public</option>
                  </Select>
                )}
              </Field>
            </div>
            <Field label="Short bio" hint="Up to 500 characters.">
              {(props) => (
                <TextArea
                  {...props}
                  value={draft.bio}
                  maxLength={500}
                  onChange={(event) => update("bio", event.target.value)}
                />
              )}
            </Field>
            <div className="cx-grid">
              <Field
                label="Skills, separated by commas"
                hint="Reusable interests and skills; event matching remains separately controlled."
              >
                {(props) => (
                  <TextInput
                    {...props}
                    value={skillText}
                    onChange={(event) => {
                      setSaved(false);
                      setSkillText(event.target.value);
                    }}
                  />
                )}
              </Field>
              <Field label="Interests, separated by commas">
                {(props) => (
                  <TextInput
                    {...props}
                    value={interestText}
                    onChange={(event) => {
                      setSaved(false);
                      setInterestText(event.target.value);
                    }}
                  />
                )}
              </Field>
              <Field label="Preferred roles, separated by commas">
                {(props) => (
                  <TextInput
                    {...props}
                    value={roleText}
                    onChange={(event) => {
                      setSaved(false);
                      setRoleText(event.target.value);
                    }}
                  />
                )}
              </Field>
            </div>
            <fieldset>
              <legend>Website and project links</legend>
              {draft.links.map((link, index) => (
                <div className="cx-profile-link-editor" key={index}>
                  <Field label={`Link ${index + 1} label`}>
                    {(props) => (
                      <TextInput
                        {...props}
                        maxLength={50}
                        value={link.label}
                        onChange={(event) => {
                          setSaved(false);
                          setDraft({
                            ...draft,
                            links: draft.links.map((item, i) =>
                              i === index
                                ? { ...item, label: event.target.value }
                                : item,
                            ),
                          });
                        }}
                      />
                    )}
                  </Field>
                  <Field label={`Link ${index + 1} URL`}>
                    {(props) => (
                      <TextInput
                        {...props}
                        type="url"
                        value={link.url}
                        onChange={(event) => {
                          setSaved(false);
                          setDraft({
                            ...draft,
                            links: draft.links.map((item, i) =>
                              i === index
                                ? { ...item, url: event.target.value }
                                : item,
                            ),
                          });
                        }}
                      />
                    )}
                  </Field>
                  <Button
                    variant="secondary"
                    onClick={() => {
                      setSaved(false);
                      setDraft({
                        ...draft,
                        links: draft.links.filter((_, i) => i !== index),
                      });
                    }}
                  >
                    Remove link {index + 1}
                  </Button>
                </div>
              ))}
              <Button
                variant="secondary"
                disabled={draft.links.length >= 6}
                onClick={() =>
                  setDraft({
                    ...draft,
                    links: [...draft.links, { label: "", url: "" }],
                  })
                }
              >
                Add link
              </Button>
            </fieldset>
          </fieldset>
          {error && <p role="alert">{error}</p>}
          {saved && <p role="status">Profile saved.</p>}
          <Button type="submit" disabled={busy}>
            {busy ? "Saving…" : "Save profile"}
          </Button>
        </form>
      </details>
      <section aria-label="Event identity">
        <h3>Event interests & availability</h3>
        {profile.event_profiles.length === 0 ? (
          <p>
            No event matching preferences yet. Add skills and interests in your
            event’s team marketplace.
          </p>
        ) : (
          <div className="cx-grid">
            {profile.event_profiles.map((value) => (
              <article key={value.event} className="cx-profile-event">
                <h4>{value.event_name}</h4>
                <p>
                  {value.team_seeking
                    ? "Looking for a team"
                    : "Not currently seeking a team"}
                  {value.availability_hours_per_week !== null
                    ? ` · ${value.availability_hours_per_week} hours/week`
                    : ""}
                </p>
                <SkillTags
                  values={[...value.skills, ...value.roles, ...value.interests]}
                />
              </article>
            ))}
          </div>
        )}
      </section>
      {profile.judge_expertise.length > 0 && (
        <section aria-label="Judge expertise">
          <h3>Judge expertise</h3>
          <SkillTags
            values={profile.judge_expertise.flatMap((value) => value.tags)}
          />
          <p>
            Manage expertise below in your judge workspace. It stays scoped to
            each workspace.
          </p>
        </section>
      )}
      {profile.mentoring.length > 0 && (
        <section aria-label="Mentor identity">
          <h3>Mentoring</h3>
          {profile.mentoring.map((value, index) => (
            <article key={index}>
              <h4>{value.event_name}</h4>
              <p>
                {value.headline} ·{" "}
                {value.available ? "Available" : "Unavailable"}
              </p>
              <SkillTags values={value.tracks} />
            </article>
          ))}
        </section>
      )}
    </section>
  );
}
