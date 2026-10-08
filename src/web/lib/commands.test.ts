import "./shellCommands";
import { afterEach, describe, expect, it } from "vitest";
import {
  commandsFor,
  rankCommands,
  registerCommandProvider,
  score,
  type Command,
  type CommandContext,
} from "./commands";

const context = (over: Partial<CommandContext> = {}): CommandContext => ({
  role: "organizer",
  workspaceId: "w",
  eventId: "",
  view: "overview",
  selection: null,
  places: [],
  events: [],
  go: () => {},
  target: (t) => `/w/w/${t.view}`,
  roles: [],
  pinned: [],
  recentViews: [],
  capabilities: {},
  ...over,
});
const cmd = (
  id: string,
  label: string,
  over: Partial<Command> = {},
): Command => ({
  id,
  label,
  group: "Test",
  run: () => {},
  ...over,
});

describe("command ranking", () => {
  it("scores exact over prefix over word prefix over substring over subsequence", () => {
    const c = cmd("a", "Go to Judging");
    expect(score(c, "go to judging")).toBe(100);
    expect(score(c, "go to")).toBe(80);
    expect(score(c, "jud")).toBe(60);
    expect(score(c, "go jud")).toBe(55); // every typed word starts a word
    expect(score(c, "dgin")).toBe(40);
    expect(score(c, "gtj")).toBe(20);
    expect(score(c, "zzz")).toBe(0);
  });

  it("finds a command by its keywords", () => {
    const c = cmd("a", "Sign out", { keywords: ["log out", "exit"] });
    expect(score(c, "exit")).toBeGreaterThanOrEqual(60);
    expect(score(c, "log")).toBeGreaterThanOrEqual(60);
  });

  it("orders by score, then by recent use, then by registration order, the same every time", () => {
    const list = [
      cmd("one", "Go to Overview"),
      cmd("two", "Go to Judging"),
      cmd("three", "Go to Results"),
      cmd("four", "Judging rules"),
    ];
    const ids = (q: string, recent: string[] = []) =>
      rankCommands(list, q, recent).map((c) => c.id);
    expect(ids("judging")).toEqual(["four", "two"]); // prefix before word prefix
    expect(ids("go to")).toEqual(["one", "two", "three"]); // ties keep registration order
    expect(ids("go to", ["three"])).toEqual(["three", "one", "two"]); // a recent one wins a tie
    expect(ids("go to", ["three", "two"])).toEqual(["three", "two", "one"]);
    expect(ids("go to")).toEqual(ids("go to")); // deterministic
    expect(ids("")).toEqual(["one", "two", "three", "four"]);
    expect(ids("", ["four"])).toEqual(["four", "one", "two", "three"]);
  });

  it("matches nothing for text no command contains", () => {
    expect(rankCommands([cmd("a", "Sign out")], "qqq")).toEqual([]);
  });
});

describe("command registry", () => {
  const remove: (() => void)[] = [];
  afterEach(() => remove.splice(0).forEach((fn) => fn()));

  it("offers what providers contribute for the context, each id once, in order", () => {
    remove.push(
      registerCommandProvider(() => [cmd("t.a", "A"), cmd("t.dup", "First")]),
      registerCommandProvider(() => [cmd("t.dup", "Second"), cmd("t.b", "B")]),
    );
    const ids = commandsFor(context())
      .filter((c) => c.id.startsWith("t."))
      .map((c) => `${c.id}:${c.label}`);
    expect(ids).toEqual(["t.a:A", "t.dup:First", "t.b:B"]);
  });

  it("drops a command whose when() says it does not apply, without running it", () => {
    let ran = false;
    remove.push(
      registerCommandProvider(() => [
        cmd("t.org", "Organizer only", {
          when: (ctx) => ctx.role === "organizer",
          run: () => (ran = true),
        }),
      ]),
    );
    const has = (role: string) =>
      commandsFor(context({ role })).some((c) => c.id === "t.org");
    expect(has("organizer")).toBe(true);
    expect(has("judge")).toBe(false);
    expect(ran).toBe(false);
  });

  it("the shell's own commands are navigation and presentation only", () => {
    const ctx = context({
      places: [{ id: "judging", label: "Judging", to: "/w/w/judging" }],
      events: [
        { id: "e1", name: "Gauss Hack", current: true },
        { id: "e2", name: "Noether Night", current: false },
      ],
      capabilities: { signOut: () => {}, setTheme: () => {} },
    });
    const ids = commandsFor(ctx).map((c) => c.id);
    expect(ids).toEqual(
      expect.arrayContaining([
        "go.judging",
        "event.e2",
        "theme.dark",
        "account.sign-out",
        "account.notification-preferences",
      ]),
    );
    expect(ids).not.toContain("event.e1"); // the current event is not a switch
    // without the capabilities the commands that need them are not offered
    const bare = commandsFor(context()).map((c) => c.id);
    expect(bare).not.toContain("account.sign-out");
    expect(bare).not.toContain("theme.dark");
  });

  it("offers View as another role only to a person who holds more than one, and keeps the event", () => {
    const one = commandsFor(
      context({ roles: [{ role: "judge", label: "Judge", current: true }] }),
    );
    expect(one.some((c) => c.id.startsWith("role."))).toBe(false);
    const gone: string[] = [];
    const two = commandsFor(
      context({
        roles: [
          { role: "organizer", label: "Organizer", current: true },
          { role: "participant", label: "Participant", current: false },
        ],
        go: (to) => gone.push(to),
        target: (t) => `/w/w/${t.view}?as=${t.params?.as}`,
      }),
    );
    const role = two.filter((c) => c.id.startsWith("role."));
    expect(role.map((c) => c.label)).toEqual(["View as Participant"]);
    role[0].run(
      context({
        go: (to) => gone.push(to),
        target: (t) => `/w/w/${t.view}?as=${t.params?.as}`,
      }),
    );
    expect(gone).toEqual(["/w/w/overview?as=participant"]);
  });

  it("offers Preview as only to organizers and admins, and only when the shell can open it", () => {
    const open = () => {};
    const has = (role: string, capable = true) =>
      commandsFor(
        context({ role, capabilities: capable ? { openPreview: open } : {} }),
      )
        .filter((c) => c.id.startsWith("preview."))
        .map((c) => c.label);
    expect(has("organizer")).toEqual([
      "Preview as participant",
      "Preview as judge",
      "Preview as public",
    ]);
    expect(has("admin")).toHaveLength(3);
    expect(has("judge")).toEqual([]);
    expect(has("participant")).toEqual([]);
    expect(has("organizer", false)).toEqual([]);
  });
});

describe("selection commands", () => {
  it("are offered only while something is selected, named for the list", () => {
    const none = commandsFor(context());
    expect(none.some((c) => c.id.startsWith("selection."))).toBe(false);
    const ran: string[] = [];
    const some = commandsFor(
      context({
        selection: {
          entity: "projects",
          noun: "projects",
          count: 2,
          commands: [
            {
              id: "x",
              label: "Move 2 projects to A",
              run: () => ran.push("x"),
            },
          ],
        },
      }),
    );
    const found = some.find((c) => c.id === "selection.projects.x")!;
    expect(found.group).toBe("Selected projects");
    found.run(context());
    expect(ran).toEqual(["x"]);
  });
});
