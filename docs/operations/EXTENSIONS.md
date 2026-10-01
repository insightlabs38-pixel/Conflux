# Extensions inventory (EXTENSION_MANIFEST)

Conflux has **no plugin loader**. Everything extensible is application source that registers into one of the platform's registries when Django starts (page blocks, artifact validators, advancement strategies, bulk actions, job kinds, approval policies, thread subjects, timeline providers, queryable entities, preview and version sources, notification categories, rich-content profiles). A **manifest** is how a source of such code (a Django app) declares itself, so the deployment can say what it provides and needs, and fail to start when the claims are wrong. Code: `core/manifest.py` (model and `check()`/`snapshot()`), `core/manifest_core.py` (the capabilities backed by `core` registries and core's own manifest), `core/checks.py` (startup gate), `core/manifest_views.py` (endpoint). Web: `lib/extensions.ts` and `features/operations/ExtensionsPanel.tsx` (Operations > Extensions). Each app declares itself in `<app>/manifest.py`, imported from its `AppConfig.ready()`.

## The model

```python
manifest.register_capability(manifest.Capability(
    "page_block", "Page block", "A block an organizer can add.",
    live=lambda: {key: block["title"] for key, block in BLOCK_TYPES.items()}))
manifest.register_manifest(manifest.Manifest(
    id="presentation", version="1.0.0", label="Public pages",   # api_version defaults to 1
    provides=(("page_block", "hero"), ("page_block", "faq")),
    requires=(("manifest", "core"),)))
```

- A **capability** is a kind of thing a deployment can provide. Named after its registry, `live()` reads the registry's entries (`{id: label}`). A kind without a runtime registry (archive exporter, importer and converter, assignment strategy) is **declared only**: listed, and requirements resolve against it, but there is nothing to verify it against.
- A **manifest** has an id, a version, a label, an `api_version`, what it `provides` and what it `requires`. A requirement on `("manifest", "core")` needs that source; on any other kind, that entry must be provided by some manifest or live in its registry.
- Registration is idempotent for an identical value and raises on a conflicting one (never a silent replacement).

## What is checked

`manifest.check()` returns every disagreement with a code, severity, manifest and message, in a stable order. Errors fail `manage.py check` (so `migrate` and `runserver`) through `core.manifest.<code>`:

| Code                      | Severity | Meaning                                                                    |
| ------------------------- | -------- | -------------------------------------------------------------------------- |
| `incomplete`              | error    | No id, version or label                                                    |
| `unsupported_api_version` | error    | `api_version` is not in `SUPPORTED_API_VERSIONS` (currently `(1,)`)        |
| `unknown_capability`      | error    | Provides a kind nobody registered                                          |
| `not_registered`          | error    | Declares an entry its registry does not contain                            |
| `duplicate_claim`         | error    | Two manifests claim the same entry                                         |
| `unresolved_requirement`  | error    | A requirement nothing provides                                             |
| `unclaimed`               | warning  | A live registry entry no manifest declares (a feature in progress is fine) |

## The endpoint and the page

`GET /api/v1/workspaces/{id}/extensions/` (organizers and admins; everyone else 403; `Cache-Control: private, no-store`; no write method exists) returns `{api_version, supported_api_versions, manifests[], capabilities[], problems[], ok}`. Each provided entry has a `state` of `live`, `declared` or `missing`; each capability lists its entries with the manifest that owns them. The page lists sources first, findings at the top (an alert for errors, a status for warnings), and capabilities closed behind details. There is nothing to install, enable, edit or upload.

## Adding an extension source

1. Register the entry in its own registry as today (and in its domain tests).
2. Add it to the app's `manifest.py` `provides`; require `("manifest", "core")` and anything else it uses.
3. `manage.py check` and `tests/integration/test_extension_manifest.py` fail until the declaration and the registry agree. A new registry becomes a capability with one `register_capability` call.

## Boundaries and compatibility

Read-only and stateless: no table, no migration, no audit row (nothing mutates; changing what is provided is a source change reviewed in Git). No loader, no runtime permission model, no organizer-supplied code or manifest, and the inventory never decides a permission, score or deadline. An `api_version` bump is the migration lever: a build declares the versions it supports and refuses to start with a manifest written for another. Existing registries and the internal extension SDK ([EXTENSION_SDK.md](../architecture/EXTENSION_SDK.md)) are unchanged.

## Verification

`tests/integration/test_extension_manifest.py`: the real deployment is consistent and passes `manage.py check`; every live entry is claimed exactly once; the inventory reads each real registry; the six SDK families and archive formats are described; each failure code is reported with its manifest; an independent source declares itself without touching the platform; registration is idempotent; startup gate and warnings; the endpoint's role boundaries, cache header, read-only methods and a broken deployment reported rather than hidden. Web: `ExtensionsPanel.test.tsx`. Browser: `tests/e2e/extensions.spec.ts` at 390 and 1440 (axe clean, no overflow, no writes).
