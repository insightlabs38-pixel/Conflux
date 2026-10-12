export default {
  id: 'dogfood-orchestrator',
  displayName: 'Dogfood Orchestrator',
  model: 'z-ai/glm-5.3-flash',
  reasoningOptions: { enabled: true, effort: 'max' },
  toolNames: ['read_files','code_search','run_terminal_command','spawn_agents','end_turn'],
  spawnableAgents: ['dogfood-frontend', 'dogfood-backend', 'dogfood-integration', 'dogfood-verification', 'dogfood-review', 'dogfood-polish', 'dogfood-ops'],
  instructionsPrompt: 'Persistent DOGFOOD scheduler/control plane. Read execution control state and schedule only ready nonconflicting work. Do not edit product code. You may launch/manage Freebuff worker CLI processes through approved tmux/worktree wrapper procedures, but never control Claude or Codex sessions. Never message/type into another agent except Freebuff worker processes you explicitly own as orchestrator. Use rg/grep/sed targeted retrieval before broad reads. Maintain queue/attention/escalation evidence through approved control commands/files.',
}
