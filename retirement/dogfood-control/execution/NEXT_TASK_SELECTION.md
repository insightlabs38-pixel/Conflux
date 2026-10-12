# Bulk Next-Task Selection

Claude/Sol select senior batches through NEXT_BATCH_SELECTION.md. Luna/Freebuff select one fine-grained task with conflux-control next-task <lane>.

Selection requires satisfied task dependencies, unlocked batch phase/gates, bulk_eligible true, no DONE/ACTIVE/reserved state, no senior-exclusive batch reservation and no path ownership conflict. Exclude high risk and human-only work. Prefer Core, then Stretch, then Very Stretch; within a phase, prefer tasks that unblock downstream tasks. A selector returns a candidate; atomic claim makes the reservation.

Never let an autonomous session race another owner. A task may be bulk-eligible inside a Sol-preferred batch only while the batch is unreserved and paths do not conflict. Luna defaults to one active task; Freebuff has one top-level session and one active task.
