# Event themes

The existing Default/Dark/Minimal mode remains. `Page.theme_config` is optional
and accepts only typed presets: typography, corner treatment, density, width,
hero layout, background and project cards, plus accent and HTTP(S) logo/banner
image URLs. No organizer CSS or script is stored or executed. Images are optional;
event initials provide the fallback. Fonts use the local system, serif and code stacks.

Accent needs 4.5:1 contrast on canvas and raised surfaces. Control foreground is
derived from contrast; focus uses that validated accent, and hover also underlines.
The existing accessibility audit reports invalid imported/directly stored settings.
Both Django public pages and the React public page consume the same resolved settings.
The editor saves theme mode and configuration together, shows errors, and opens the
real public page as its preview. Block schemas and publication gates remain unchanged.

Repeatable demo presets use the existing `demo_scenario create --theme-preset`
command: `technical` (Conflux Builders), `student` (Campus Build Weekend), and
`conference` (Open Systems Forum). Use separate seeds for simultaneous examples.
The B03 local examples are seeds 81, 82 and 83; they use real synthetic workflows.

v1 config/full and Event-as-Code accept the optional settings. Final archive v4
includes them in its exact page fields; frozen v2/v3 readers remain available and
restore default settings. Source signatures, provenance and evidence stay intact.
