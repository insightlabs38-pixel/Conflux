import { useEffect, useState, type FormEvent } from "react";

type TeamStatus = {
  team: { public_id: string } | null;
  my_role: string | null;
};
type Project = { public_id: string; name: string; team: string | null };
type Profile = {
  public_id: string;
  username: string;
  skills: string[];
  bio: string;
  visible: boolean;
  matched_skills?: string[];
};
type Opening = {
  public_id: string;
  team_name: string;
  project_name: string | null;
  title: string;
  description: string;
  desired_skills: string[];
  matched_skills: string[];
  is_open: boolean;
};

async function request<T>(
  url: string,
  method = "GET",
  body?: object,
): Promise<T> {
  const response = await fetch(url, {
    method,
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!response.ok)
    throw new Error(`Marketplace request failed (${response.status}).`);
  return response.json() as Promise<T>;
}

function skills(value: string): string[] {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

export function MarketplacePanel({
  workspaceId,
  eventId,
}: {
  workspaceId: string;
  eventId: string;
}) {
  const base = `/api/v1/workspaces/${workspaceId}/events/${eventId}/`;
  const market = base + "marketplace/";
  const [status, setStatus] = useState<TeamStatus | null>(null);
  const [profile, setProfile] = useState<Profile | null>(null);
  const [matches, setMatches] = useState<Opening[]>([]);
  const [openings, setOpenings] = useState<Opening[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [candidates, setCandidates] = useState<Profile[]>([]);
  const [selectedOpening, setSelectedOpening] = useState("");
  const [profileSkills, setProfileSkills] = useState("");
  const [bio, setBio] = useState("");
  const [visible, setVisible] = useState(false);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [desiredSkills, setDesiredSkills] = useState("");
  const [projectId, setProjectId] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function refresh() {
    const [nextStatus, nextProfile, nextMatches, nextOpenings] =
      await Promise.all([
        request<TeamStatus>(base + "my-team/"),
        request<{ profile: Profile | null }>(market + "profile/"),
        request<Opening[]>(market + "matches/"),
        request<Opening[]>(market + "openings/"),
      ]);
    setStatus(nextStatus);
    setProfile(nextProfile.profile);
    setProfileSkills(nextProfile.profile?.skills.join(", ") ?? "");
    setBio(nextProfile.profile?.bio ?? "");
    setVisible(nextProfile.profile?.visible ?? false);
    setMatches(nextMatches);
    setOpenings(nextOpenings);
    if (nextStatus.my_role === "captain") {
      const [mine, nextProjects] = await Promise.all([
        request<Opening[]>(market + "my-openings/"),
        request<Project[]>(base + "projects/"),
      ]);
      setOpenings(mine);
      setProjects(
        nextProjects.filter((item) => item.team === nextStatus.team?.public_id),
      );
    }
  }

  useEffect(() => {
    let active = true;
    refresh().catch((cause: unknown) => {
      if (active)
        setError(
          cause instanceof Error
            ? cause.message
            : "Marketplace could not load.",
        );
    });
    return () => {
      active = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [base]);

  async function run(action: () => Promise<void>) {
    setBusy(true);
    setError("");
    try {
      await action();
    } catch (cause) {
      setError(
        cause instanceof Error ? cause.message : "Marketplace request failed.",
      );
    } finally {
      setBusy(false);
    }
  }

  function saveProfile(event: FormEvent) {
    event.preventDefault();
    void run(async () => {
      await request<Profile>(market + "profile/", "PUT", {
        skills: skills(profileSkills),
        bio,
        visible,
      });
      await refresh();
    });
  }

  function createOpening(event: FormEvent) {
    event.preventDefault();
    void run(async () => {
      await request<Opening>(market + "openings/", "POST", {
        title,
        description,
        desired_skills: skills(desiredSkills),
        project: projectId || null,
      });
      setTitle("");
      setDescription("");
      setDesiredSkills("");
      setProjectId("");
      await refresh();
    });
  }

  function toggleOpening(opening: Opening) {
    void run(async () => {
      await request<Opening>(
        market + `openings/${opening.public_id}/`,
        "PATCH",
        { is_open: !opening.is_open },
      );
      await refresh();
    });
  }

  function showCandidates(openingId: string) {
    void run(async () => {
      setSelectedOpening(openingId);
      setCandidates(
        await request<Profile[]>(market + `openings/${openingId}/matches/`),
      );
    });
  }

  return (
    <section aria-label="Team marketplace">
      <h2>Team marketplace</h2>
      {error && <p role="alert">{error}</p>}
      <button type="button" disabled={busy} onClick={() => void run(refresh)}>
        Refresh marketplace
      </button>
      <form onSubmit={saveProfile}>
        <h3>Your skills profile</h3>
        <label>
          Skills, separated by commas{" "}
          <input
            value={profileSkills}
            onChange={(event) => setProfileSkills(event.target.value)}
          />
        </label>
        <label>
          About you{" "}
          <textarea
            value={bio}
            onChange={(event) => setBio(event.target.value)}
            maxLength={500}
          />
        </label>
        <label>
          <input
            type="checkbox"
            checked={visible}
            onChange={(event) => setVisible(event.target.checked)}
          />{" "}
          Show my profile to other participants
        </label>
        <button disabled={busy}>Save profile</button>
        {profile && (
          <p>
            {profile.visible
              ? "Your profile is visible."
              : "Your profile is private."}
          </p>
        )}
      </form>
      {status?.my_role === "captain" ? (
        <>
          <h3>Your openings</h3>
          <ul>
            {openings.map((opening) => (
              <li key={opening.public_id}>
                {opening.title} · {opening.is_open ? "Open" : "Closed"}
                <button
                  type="button"
                  disabled={busy}
                  onClick={() => toggleOpening(opening)}
                >
                  {opening.is_open ? "Close" : "Reopen"}
                </button>
                <button
                  type="button"
                  disabled={busy}
                  onClick={() => showCandidates(opening.public_id)}
                >
                  Find participants
                </button>
              </li>
            ))}
          </ul>
          <form onSubmit={createOpening}>
            <h3>Post an opening</h3>
            <label>
              Role{" "}
              <input
                value={title}
                onChange={(event) => setTitle(event.target.value)}
                required
                maxLength={120}
              />
            </label>
            <label>
              Project{" "}
              <select
                value={projectId}
                onChange={(event) => setProjectId(event.target.value)}
              >
                <option value="">No project yet</option>
                {projects.map((item) => (
                  <option key={item.public_id} value={item.public_id}>
                    {item.name}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Skills wanted, separated by commas{" "}
              <input
                value={desiredSkills}
                onChange={(event) => setDesiredSkills(event.target.value)}
              />
            </label>
            <label>
              Description{" "}
              <textarea
                value={description}
                onChange={(event) => setDescription(event.target.value)}
                maxLength={500}
              />
            </label>
            <button disabled={busy}>Post opening</button>
          </form>
          {selectedOpening && (
            <section aria-label="Matching participants">
              <h3>Matching participants</h3>
              <ul>
                {candidates.map((item) => (
                  <li key={item.public_id}>
                    {item.username} · {item.skills.join(", ")} · matching:{" "}
                    {item.matched_skills?.join(", ") || "none"}
                  </li>
                ))}
              </ul>
              <p>
                Share a team invite link with a participant you want to recruit.
              </p>
            </section>
          )}
        </>
      ) : (
        <>
          <h3>Open roles</h3>
          {matches.length === 0 ? (
            <p>No matching openings yet.</p>
          ) : (
            <ul>
              {matches.map((opening) => (
                <li key={opening.public_id}>
                  <strong>{opening.title}</strong> · {opening.team_name}
                  {opening.project_name ? ` · ${opening.project_name}` : ""} ·
                  matching skills: {opening.matched_skills.join(", ") || "none"}
                  <p>{opening.description}</p>
                </li>
              ))}
            </ul>
          )}
        </>
      )}
    </section>
  );
}
