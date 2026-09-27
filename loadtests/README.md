# C-B31 load scenarios

Use a disposable, seeded stack. Keep the profile and its credentials outside Git. Run each scenario separately so its latency/error evidence is attributable:

```sh
for scenario in baseline deadline_storm judging_open voting_spike gallery_spike; do
  k6 run loadtests/run.js -e DISPOSABLE_TARGET=1 -e PROFILE=/tmp/conflux-load-profile.json -e SCENARIO="$scenario" --summary-export="/tmp/conflux-$scenario.json"
done
```

The profile is a JSON object keyed by those five names. Each value has `vus` and a `requests` array; every request has `method` (`GET`, `POST`, `PUT`, or `PATCH`), absolute `url`, and expected `expect` status (2xx). Optional `headers`, `body`, and `maxDuration` are accepted. Example:

```json
{
  "baseline": {
    "vus": 2,
    "requests": [
      {
        "method": "GET",
        "url": "http://127.0.0.1:8088/api/v1/health/",
        "expect": 200
      }
    ]
  }
}
```

Provide requests for the selected scenario. Use distinct resource IDs or bodies for every write; the runner rejects duplicate writes in one scenario. Include the actual draft/finalize, ballot, and vote requests in deadline, judging, and voting scenarios, with credentials and valid stage windows from the disposable seed. Record the app image/commit, database size, host CPU/RAM, VUs, request counts, status failures, and per-scenario p95 from the JSON summaries. The `shared-iterations` executor sends each listed request once across the configured VUs; request count and concurrency are explicit rather than inferred from elapsed time.
