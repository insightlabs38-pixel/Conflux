# Execution Interface (v2.1)

The separate execution-control pack is authoritative for agent logistics. Normal Claude/Codex invocations automatically select the next safe eligible lane-appropriate batch; explicit IDs are used only for deliberate out-of-order work and escalations. Agents use strict session isolation and targeted search-first repository reading (`rg`/`grep`/`sed` before broad file reads). Pre-kickoff VM provisioning/tool authentication/control-pack extraction is permitted, but Dogfood project source/scaffold/Git commits remain forbidden until kickoff.
