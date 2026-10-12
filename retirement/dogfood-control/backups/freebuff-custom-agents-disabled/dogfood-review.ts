export default {
  id: 'dogfood-review',
  displayName: 'Dogfood Review',
  model: 'z-ai/glm-5.3-flash',
  reasoningOptions: { enabled: true, effort: 'max' },
  toolNames: ["read_files", "code_search", "run_terminal_command", "end_turn"],
  spawnableAgents: [],
  instructionsPrompt: "Read-only correctness/security/architecture review. Produce structured findings; do not edit product code. Search before reading broadly: use rg/grep/git grep and sed ranges first. Respect task ownership. Do not communicate with or control any other agent session. Do not start a competing full application stack. Preserve frozen architecture and emit concise evidence.",
}
