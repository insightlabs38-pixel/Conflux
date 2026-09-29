# Task and Batch Schema

## Batch

Required: id, title, phase, preferred_executor, dependencies, owned_paths, task_ids, completion_rule.

## Task

Required: id, batch, phase, title, status, batch_dependencies, task_dependencies, goal, preferred_executor, freebuff_eligible, risk, owned_paths, required_reading, acceptance, escalate_if.

## Status lifecycle

`BLOCKED → READY → CLAIMED → ACTIVE → REVIEW → DONE`, with `CORRECTIONS` looping back to REVIEW and `ESCALATED` as a side state requiring human/frontier action.

Stretch/Very Stretch remain blocked by gates/prerequisites until promoted; labels are implementation order, not judgments that the features are unimportant.
