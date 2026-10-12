# Agent Instructions
- Before the owner-configured campaign start, do not clone/initialize Conflux Git, create source/scaffolds/manifests/Compose, start BOOT-B00, or make product commits. If no campaign start is configured, the work remains locked.
- This is the external control pack, not the submission repo. Resolve control files under $CONFLUX_CONTROL_ROOT and plans under $CONFLUX_PLAN_ROOT.
- Use conflux-control for canonical queue, reservation and ownership mutations. Do not race-edit YAML.
- Claude/Sol select senior batches; Luna/Freebuff select one bulk task. Respect gates and path ownership.
- Never control another session/pane/authentication/private transcript. The owner's existing Claude session remains owner-controlled; the unattended service may start only its own fresh, pinned, subscription-authenticated `claude -p` invocation after the documented systemd auth check. Freebuff must not invoke custom agents.
- Use targeted reads and concise receipts.
