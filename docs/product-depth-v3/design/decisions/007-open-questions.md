# D-007 · Open questions (none block implementation)
Foundation design is **frozen for implementation as of r2.1**. Items below are owner/product inputs, not design-system defects.

## Still open (non-blocking)
1. **Brand mark**: "C" monogram is a placeholder; confirm Conflux logo/wordmark.
2. **Font hosting**: confirm Plex/Source Serif licensing acceptable to self-host (OFL) or choose system stack for air-gapped installs.
3. **Wallet pass** (Apple/Google) is drawn as a button only; confirm scope.
4. **Immersive hero** and organizer custom CSS were intentionally not designed beyond the Advanced entry point.
5. **Realtime co-editing** presence chip is shown in the story editor; full collaborative cursor design deferred (EXPERT tier).
6. **Localization/RTL** not exercised in prototypes.

## Moved to the judging/product spec (r2.1)
- Pairwise default tie-share cap; whether strength-of-preference ships (D-010). UI is parameterised for both.

## Resolved
- ~~Pairwise judge mode~~ — r2 (D-010).
- ~~Organizer density default~~ — r2.1: Standard default; Dense is an explicit option suggested on ≈1800px+ displays; never auto-switched by viewport (D-009).
- ~~`.btn` default border contrast~~ — r2.1: outlined buttons use `line-3` in light and dark; hairlines unchanged (D-008).
- ~~Public "Dark base" preset~~ — r2.1: keep as an optional organizer-selectable preset, independent of the app theme; no extra board set (D-008).

## Intentionally deferred
Final logo/brand mark · immersive hero beyond its Advanced entry · full wallet-pass internals · live collaborative cursors · exhaustive RTL/localization · every later Product Depth v3 surface (see `../LATER_DESIGN_PASSES.md`).
