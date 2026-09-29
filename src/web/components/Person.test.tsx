// @vitest-environment happy-dom
import { act } from "react";
import { createRoot } from "react-dom/client";
import { expect, it } from "vitest";
import { Avatar } from "./Foundation";
import { PersonRow, ProfileHeader, SkillTags } from "./Person";
(
  globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }
).IS_REACT_ACT_ENVIRONMENT = true;
it("keeps deterministic initials when an avatar fails and resets for another source", async () => {
  const host = document.createElement("div");
  const root = createRoot(host);
  await act(async () =>
    root.render(<Avatar name="Alex Rivera" src="https://example.org/a.png" />),
  );
  expect(host.textContent).toBe("AR");
  await act(async () =>
    host.querySelector("img")!.dispatchEvent(new Event("error")),
  );
  expect(host.querySelector("img")!.hidden).toBe(true);
  await act(async () =>
    root.render(<Avatar name="Alex Rivera" src="https://example.org/b.png" />),
  );
  expect(host.querySelector("img")!.hidden).toBe(false);
  await act(async () => root.unmount());
});
it("shows reusable identity, plain biography, safe link semantics and unique skills", async () => {
  const host = document.createElement("div");
  const root = createRoot(host);
  const person = {
    user_public_id: "u1",
    username: "alex",
    display_name: "Alex Rivera",
    avatar_url: "",
    bio: "<script>plain text</script>",
    location: "Berlin",
    links: [{ label: "GitHub", url: "https://github.com/alex" }],
  };
  await act(async () =>
    root.render(
      <>
        <ProfileHeader person={person}>
          <SkillTags values={["Python", "Python", "Climate"]} />
        </ProfileHeader>
        <PersonRow person={person} fallback="alex" role="Captain" />
      </>,
    ),
  );
  expect(host.querySelector("script")).toBeNull();
  expect(host.querySelectorAll(".cx-tags li")).toHaveLength(2);
  expect(host.querySelector("a")!.rel).toContain("noopener");
  expect(host.textContent).toContain("Captain");
  await act(async () => root.unmount());
});
