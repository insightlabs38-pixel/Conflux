# Project showcase

Public gallery, project detail and published result stories use the existing
publication, finalized-submission and gallery visibility gates. Search, stage/track
filters, alphabetical order and pagination retain their existing behavior and URLs.

Cards reuse actual descriptions, search tags, track/team identity and published
awards. Initials are the deterministic cover fallback; there is no invented tagline,
technology stack or thumbnail. Team people appear only with explicitly public
account profiles; private/member identities are not disclosed by public HTML.

Project detail separates the story/media/team from public artifact and finalized
version evidence. Digests and version identifiers stay available in native keyboard
accessible disclosures. Result stories retain canonical/share/download routes and
award-category hierarchy; internal selection evidence never enters templates.

Media uses only PUBLIC/READY stored raster images (PNG/JPEG/GIF/WebP) and native
MP4/WebM playback. SVG, HTML, submitted code, documents and external video URLs are
never embedded. Existing signed attachment URLs and artifact trust boundaries stay
unchanged. No public API or submission/scoring semantics changed.

Theme-derived surfaces and compact/visual project-card treatments share the same
components. Mobile stacks the project story and evidence; wider layouts place
evidence beside the story. Screenshots are in `docs/verification/UIV2-B05`; viewport
and theme browser matrices use the existing Playwright harness.
