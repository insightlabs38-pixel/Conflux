# DOGFOODHACK master

`./master.sh` keeps exactly one Claude Code or Codex worker attached to this repository. It starts with Claude, alternates first preference on each polling cycle, and waits 30 seconds when neither provider is available.

The shared worker instructions are in `master/worker_prompt.md`. The worker must create `.dogfood/master.complete` when the campaign is complete; that signal makes the supervisor exit without relaunching an agent.

Run `./master.sh stop` for a safe stop. It creates `.dogfood/master.stop`; it sends no signal to the worker, which is left untouched and allowed to finish. Remove the signal with `./master.sh resume` when restarting is wanted. Ctrl+C has the same supervisor-only stop behavior. Lock and PID files prevent a restart from creating another worker if a prior worker is still alive.

For a scheduled start, invoke `./master.sh` at the desired time, for example 10:14 AM UTC in this environment.
