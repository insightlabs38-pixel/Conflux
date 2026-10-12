#!/usr/bin/env bash
set +e
cd /home/dogfood-control
printf "{\"at\":\"%s\",\"event\":\"runner_start\",\"lane\":\"freebuff\"}\n" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> /home/dogfood-control/logs/unattended/freebuff-runner.jsonl
(set -o pipefail; /usr/bin/python3 /home/dogfood-control/bin/conflux-unattended-freebuff freebuff 2>&1 | /home/dogfood-control/bin/conflux-redact-log >> /home/dogfood-control/logs/unattended/freebuff-runner.jsonl)
rc=$?
printf "{\"at\":\"%s\",\"event\":\"runner_exit\",\"lane\":\"freebuff\",\"exit_code\":%s}\n" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$rc" >> /home/dogfood-control/logs/unattended/freebuff-runner.jsonl
exit "$rc"
