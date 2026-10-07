import type { ReactNode } from "react";

/**
 * The one icon set (V-ICON-1): 24-unit grid, 2px round stroke, currentColor, drawn at 16px.
 * Shapes follow the Lucide set (ISC licence). An icon never carries meaning alone: it sits next to
 * its word, or it has a `label` and becomes an image with that name; otherwise it is hidden from
 * assistive technology. Add a shape here rather than a one-off inline <svg>.
 */
const SHAPES = {
  check: ["M20 6 9 17l-5-5"],
  x: ["M18 6 6 18", "m6 6 12 12"],
  plus: ["M5 12h14", "M12 5v14"],
  minus: ["M5 12h14"],
  "chevron-down": ["m6 9 6 6 6-6"],
  "chevron-up": ["m18 15-6-6-6 6"],
  "chevron-right": ["m9 18 6-6-6-6"],
  "arrow-right": ["M5 12h14", "m12 5 7 7-7 7"],
  "external-link": [
    "M15 3h6v6",
    "M10 14 21 3",
    "M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6",
  ],
  info: ["M12 16v-4", "M12 8h.01"],
  "circle-check": ["m9 12 2 2 4-4"],
  "circle-x": ["m15 9-6 6", "m9 9 6 6"],
  "triangle-alert": [
    "m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3",
    "M12 9v4",
    "M12 17h.01",
  ],
  clock: ["M12 6v6l4 2"],
  lock: ["M7 11V7a5 5 0 0 1 10 0v4"],
  search: ["m21 21-4.3-4.3"],
  home: [
    "M15 21v-8a1 1 0 0 0-1-1h-4a1 1 0 0 0-1 1v8",
    "M3 10a2 2 0 0 1 .709-1.528l7-5.999a2 2 0 0 1 2.582 0l7 5.999A2 2 0 0 1 21 10v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z",
  ],
  sliders: [
    "M21 4h-7",
    "M10 4H3",
    "M21 12h-9",
    "M8 12H3",
    "M21 20h-5",
    "M12 20H3",
    "M14 2v4",
    "M8 10v4",
    "M16 18v4",
  ],
  users: [
    "M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2",
    "M22 21v-2a4 4 0 0 0-3-3.87",
    "M16 3.13a4 4 0 0 1 0 7.75",
  ],
  "file-text": [
    "M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z",
    "M14 2v4a2 2 0 0 0 2 2h4",
    "M10 9H8",
    "M16 13H8",
    "M16 17H8",
  ],
  trophy: [
    "M6 9H4.5a2.5 2.5 0 0 1 0-5H6",
    "M18 9h1.5a2.5 2.5 0 0 0 0-5H18",
    "M4 22h16",
    "M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20.24 7 22",
    "M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20.24 17 22",
    "M18 2H6v7a6 6 0 0 0 12 0V2Z",
  ],
  "message-square": [
    "M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z",
  ],
  "map-pin": ["M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"],
  plug: [
    "M12 22v-5",
    "M9 8V2",
    "M15 8V2",
    "M18 8v5a4 4 0 0 1-4 4h-4a4 4 0 0 1-4-4V8Z",
  ],
  shield: [
    "M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z",
  ],
  user: ["M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"],
  calendar: ["M8 2v4", "M16 2v4", "M3 10h18"],
  "list-checks": [
    "m3 17 2 2 4-4",
    "m3 7 2 2 4-4",
    "M13 6h8",
    "M13 12h8",
    "M13 18h8",
  ],
} as const;

/** Shapes that need a filled-outline primitive in addition to their path. */
const EXTRAS: Partial<Record<IconName, ReactNode>> = {
  info: <circle cx="12" cy="12" r="10" />,
  "circle-check": <circle cx="12" cy="12" r="10" />,
  "circle-x": <circle cx="12" cy="12" r="10" />,
  clock: <circle cx="12" cy="12" r="10" />,
  lock: <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />,
  search: <circle cx="11" cy="11" r="8" />,
  users: <circle cx="9" cy="7" r="4" />,
  "map-pin": <circle cx="12" cy="10" r="3" />,
  user: <circle cx="12" cy="7" r="4" />,
  calendar: <rect x="3" y="4" width="18" height="18" rx="2" />,
};

export type IconName = keyof typeof SHAPES;
export const ICON_NAMES = Object.keys(SHAPES) as IconName[];

export function Icon({
  name,
  label,
  size = 16,
}: {
  name: IconName;
  /** Only for an icon that stands alone; beside its word, leave it out. */
  label?: string;
  size?: 12 | 16 | 20;
}) {
  return (
    <svg
      className="cx-icon"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      role={label ? "img" : undefined}
      aria-label={label}
      aria-hidden={label ? undefined : true}
      focusable="false"
    >
      {EXTRAS[name]}
      {SHAPES[name].map((d) => (
        <path key={d} d={d} />
      ))}
    </svg>
  );
}
