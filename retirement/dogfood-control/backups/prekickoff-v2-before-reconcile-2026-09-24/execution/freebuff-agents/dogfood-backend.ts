export default {
  id: 'dogfood-backend',
  displayName: 'Dogfood Backend',
  model: 'z-ai/glm-5.3-flash',
  reasoningOptions: { enabled: true, effort: 'max' },
  toolNames: ["read_files", "write_file", "str_replace", "code_search", "run_terminal_command", "end_turn"],
  spawnableAgents: [],
  instructionsPrompt: "Django/domain/API scoped implementation. Search before reading broadly: use rg/grep/git grep and sed ranges first. Respect task ownership. Do not communicate with or control any other agent session. Do not start a competing full application stack. Preserve frozen architecture and emit concise evidence.",
}
