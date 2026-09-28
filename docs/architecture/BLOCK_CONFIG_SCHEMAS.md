# Page-block configuration schemas

`presentation.block_types.BLOCK_TYPES` is the code-owned page-block catalog.
Each type declares a title and a bounded configuration schema. The server's
`clean_config` validates/normalizes that schema before storage; the page builder
uses the checked generated catalog to render its controls and validate edits.
Organizer requests cannot supply schemas or execute extension code.

Supported shapes are objects, bounded strings, bounded integers, and bounded
arrays of objects. This is a documented JSON Schema subset, not a general JSON
Schema implementation. `additionalProperties` controls unknown-field rejection;
permissive existing top-level configurations still discard unknown keys during
normalization. Strict list rows/live blocks reject them. Defaults apply only to
omitted fields; explicit nulls remain invalid. Integers exclude booleans/fractions.

`title` supplies control labels; `x-widget: textarea` selects multiline text;
`x-nonblank` requires non-whitespace text. `x-create-default` provides valid
starter content when adding a block, independently of persisted omission rules.
Array rows render recursively and their declared item limit disables adding.
Server rich-text sanitization remains mandatory after schema normalization and
again on rendering. A schema never expands URL/HTML permissions.

After changing a declaration, run `make block-schema-generate`, review the
generated TypeScript, and run `make block-schema-check`. `verify-fast` includes
the freshness check. Add positive/negative schema and API tests. A new block kind
also needs model choices/migrations and a public renderer; schema registration
alone does not introduce a supported runtime type.

Existing labels, controls, field limits, configuration defaults and public
renderers are retained. Valid starter content now makes required-text blocks
creatable directly from the builder. No public-page redesign is involved.
