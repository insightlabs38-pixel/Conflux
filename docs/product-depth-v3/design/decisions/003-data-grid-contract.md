# D-003 · Data grid & saved views
- One typed query model shared by URL, saved views, bulk targets, export, CLI, MCP. UI shows chips; "Query" reveals the equivalent text (`registration:confirmed AND waiver:!signed AND (track:a OR track:b)`).
- Nested filters: max depth 3 in UI; AND/OR groups; operators by field type.
- Selection ≠ cursor. "Select all N matching" freezes a membership snapshot; bulk action → plan (effects, skips, reversibility) → approve (if policy) → apply as async job with progress and partial-failure retry.
- Inline edit validates per cell, Esc reverts. Restricted columns are masked and say why.
- Virtualized rows; total count always visible; sticky header; grouping shows aggregates in the group row.
- Narrow: row-list + detail page; filters/views in bottom sheet; bulk bar bottom.
