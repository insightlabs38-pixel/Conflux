# Presentation and Customization

## Principle
Excellent defaults first; safe customization second. The organizer UI remains consistent even if the public site is themed.

## Theme
CSS runtime tokens for colors, typography, radii, spacing and selected presentation assets. Provide polished Default, Dark and Minimal presets.

## Page blocks
Core registry: Hero, Tracks, Prizes, Schedule, Sponsors, FAQ, Resources, Gallery, Results, RichText, CTA. Additional blocks are additive.

## Gallery acceptance
The configured gallery route must include fixture project title text in the raw HTML response. Server-injected bootstrap JSON and/or a small server-rendered accessible listing can hydrate into the React experience.

## Builders
Event/stage/policy/form/evaluation/page builders deserve disproportionate UX polish: sensible defaults, previews, validation, empty/error states, keyboard accessibility and no raw JSON requirement for ordinary configuration.

## Safety
No arbitrary organizer JS. Rich text/diagrams are sanitized; Mermaid/technical rendering uses safe configuration.
