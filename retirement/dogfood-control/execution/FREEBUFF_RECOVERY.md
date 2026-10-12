## Freebuff Working Build Pin

- Launcher: `/home/dogfood-control/bin/freebuff-working`
- Source checkout: `/home/insightlabs38/src/freebuff`
- Executable: `/home/insightlabs38/src/freebuff/cli/bin/freebuff` (ARM64 source-tree build)
- Working CLI version: 0.0.189-base2.1
- Git commit: 1c7005e38693719d32bee3427db690b217718e85
- Git description: v1.0.679-3177-g1c7005e38-dirty
- Node: v24.21.0
- Config location: /home/insightlabs38/.config/manicode/freebuff (owner-managed; not read or modified)
- Source tree has existing local modifications; leave them and the executable untouched.
- Do not update, rebuild, npm-reinstall, or switch builds during kickoff prep.
- Custom Conflux/Dogfood user-agent definitions were moved to `/home/dogfood-control/backups/freebuff-custom-agents-disabled/`; do not restore them.
- Reboot recovery: run `/home/dogfood-control/bin/freebuff-working --version`, then launch `/home/dogfood-control/bin/freebuff-working` in the Freebuff tmux window after owner authentication is already available.


The source checkout contains the built-in helper harness and provider-supplied helper flow (including file pickers, code searchers, web/docs researchers and bashers). No authenticated top-level session was launched or inspected during setup.
