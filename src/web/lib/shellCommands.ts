import { registerCommandProvider, type Command } from "./commands";

/**
 * The commands of the application shell. They are navigation and presentation only: going to a
 * place, switching event, choosing a theme, opening notification preferences, signing out. The
 * places and events come from `context.places` / `context.events`, which the palette fills from what
 * the shell already holds, so a place or event the person cannot see is never offered.
 */
registerCommandProvider((context) => {
  const commands: Command[] = [];
  for (const place of context.places)
    commands.push({
      id: `go.${place.id}`,
      label: `Go to ${place.label}`,
      group: "Go to",
      keywords: [place.label],
      shortcut: place.key ? `G then ${place.key.toUpperCase()}` : undefined,
      run: (ctx) => ctx.go(place.to),
    });
  for (const event of context.events)
    if (!event.current)
      commands.push({
        id: `event.${event.id}`,
        label: `Switch to ${event.name}`,
        group: "Events",
        keywords: ["event", event.name],
        run: (ctx) => ctx.go(ctx.target({ view: ctx.view, event: event.id })),
      });
  return commands;
});

registerCommandProvider(() => {
  const theme = (
    value: "system" | "light" | "dark",
    label: string,
  ): Command => ({
    id: `theme.${value}`,
    label,
    group: "Appearance",
    keywords: ["theme", "appearance", "colour", "color", value],
    when: (ctx) => !!ctx.capabilities.setTheme,
    run: (ctx) => ctx.capabilities.setTheme?.(value),
  });
  return [
    theme("system", "Use the system theme"),
    theme("light", "Use the light theme"),
    theme("dark", "Use the dark theme"),
  ];
});

registerCommandProvider(() => {
  const density = (
    value: "comfortable" | "compact" | "high",
    label: string,
  ): Command => ({
    id: `density.${value}`,
    label,
    group: "Appearance",
    keywords: ["density", "table", "rows", "spacing", value],
    when: (ctx) => !!ctx.capabilities.setDensity,
    run: (ctx) => ctx.capabilities.setDensity?.(value),
  });
  return [
    density("comfortable", "Use comfortable table density"),
    density("compact", "Use compact table density"),
    density("high", "Use high-density tables"),
  ];
});

registerCommandProvider((context) =>
  // only when the person holds more than one role here; viewing as another is choosing a screen
  context.roles.length < 2
    ? []
    : context.roles
        .filter((entry) => !entry.current)
        .map((entry): Command => ({
          id: `role.${entry.role}`,
          label: `View as ${entry.label}`,
          group: "Role",
          keywords: ["role", "switch", "view as", entry.role],
          run: (ctx) =>
            ctx.go(
              ctx.target({ view: "overview", params: { as: entry.role } }),
            ),
        })),
);

registerCommandProvider(() => [
  {
    id: "help.shortcuts",
    label: "Show keyboard shortcuts",
    group: "Help",
    keywords: ["keys", "keyboard", "help", "hotkeys"],
    shortcut: "?",
    when: (ctx) => !!ctx.capabilities.openShortcuts,
    run: (ctx) => ctx.capabilities.openShortcuts?.(),
  },
]);

registerCommandProvider(() => [
  {
    id: "account.notification-preferences",
    label: "Open notification preferences",
    group: "Account",
    keywords: ["notifications", "email", "settings", "profile"],
    when: (ctx) => ctx.role !== "",
    run: (ctx) =>
      ctx.go(ctx.target({ view: "profile" }) + "#notification-preferences"),
  },
  {
    id: "account.sign-out",
    label: "Sign out",
    group: "Account",
    keywords: ["log out", "logout", "exit"],
    when: (ctx) => !!ctx.capabilities.signOut,
    run: (ctx) => ctx.capabilities.signOut?.(),
  },
]);
