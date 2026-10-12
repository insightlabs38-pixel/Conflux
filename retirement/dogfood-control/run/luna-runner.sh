#!/usr/bin/env bash
set +e
cd /home/dogfood-control
printf "{\"at\":\"%s\",\"event\":\"runner_start\",\"lane\":\"luna\"}\n" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> /home/dogfood-control/logs/unattended/luna-runner.jsonl
(set -o pipefail; /usr/bin/python3 /home/dogfood-control/bin/conflux-unattended-worker luna 2>&1 | /home/dogfood-control/bin/conflux-redact-log >> /home/dogfood-control/logs/unattended/luna-runner.jsonl)
rc=$?
printf "{\"at\":\"%s\",\"event\":\"runner_exit\",\"lane\":\"luna\",\"exit_code\":%s}\n" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$rc" >> /home/dogfood-control/logs/unattended/luna-runner.jsonl
exit "$rc"
