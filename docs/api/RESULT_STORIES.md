# Public result stories

The public results index lives at `/e/{event}/results/`, paginated in groups of
50 published awards with `?page=2`. An event must be public and opened (including
its closed/archived history). Unpublished awards are absent.

`results/awards/{award}/` presents the award description and public winning
project highlights. `results/projects/{project}/` presents the project's public
name, description, team/track and published awards, linking to its existing
project/artifact page. A project must currently have a finalized submission and
at least one published award. Reopening all its submissions removes its highlight
and card. Awards may remain published with no currently public project highlights.
Each winner must also belong to the same event. Selection evidence, private
artifacts, judge identities and fulfillment state are never included.

Each highlight has a canonical permalink, Open Graph metadata and a self-contained
1200×630 SVG card at the same path plus `card.svg`. `?download=1` serves an
attachment with a UUID-based filename. Cards use the established public palette,
wrap/truncate long names and remove XML-invalid controls. Their text is escaped;
they contain no scripts, external resources, private fields or user-controlled
markup. The project description uses the existing safe Markdown renderer; award
descriptions are plain text.

Result pages and cards send `no-store`. The public service worker respects that
policy, removes stale cached entries, and continues ordinary page offline caching.
Publication withdrawal therefore cannot create a new cached result copy. Shared
permalinks resolve current publication state rather than freezing a snapshot.
Previously downloaded images cannot be revoked.

The existing landing-page results block links to award highlights. No broad
navigation or page-builder changes were introduced. SVG cards can be downloaded
and shared directly; social platforms that require raster preview images may not
render the Open Graph image. No image proxy, raster renderer, AI-authored narrative
or unpublished-result preview is included.

Browser evidence: `docs/verification/VS40/` contains desktop/mobile/long-title
screenshots and the measured interaction/cache checks. No recorded-footage
manifest existed; these are new verification screenshots.
