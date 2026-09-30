#!/usr/bin/env python3
"""PD-B03-T01 evidence probe: do per-seed demo scenarios isolate mutable browser state?

Runs against the approved shared stack (BASE, default http://localhost:8080). Seeds are
created/purged through the canonical `demo_scenario` command; all checks go through the
public HTTP API like the browser does. Prints one line per check and exits non-zero on any
failure. Probe seeds are purged at the end; seed 7 (the shared demo) is never modified.
"""
import http.cookiejar
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

BASE = os.environ.get("BASE", "http://localhost:8080")
PW = "demo-pass-iso"
A, B, SHARED = 9201, 9202, int(os.environ.get("E2E_DEMO_SEED", "7"))
failures = []


def manage(*args):
    t = time.monotonic()
    out = subprocess.run(
        ["docker", "compose", "exec", "-T", "app", "python", "manage.py", *args],
        capture_output=True, text=True,
    )
    return out.returncode, (out.stdout + out.stderr).strip().splitlines()[-1:], time.monotonic() - t


class Session:
    def __init__(self, user, password):
        self.jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar))
        self.user = user
        self.call("POST", "/api/v1/accounts/login/", {"username": user, "password": password})

    def call(self, method, path, body=None):
        req = urllib.request.Request(
            BASE + path, method=method,
            data=None if body is None else json.dumps(body).encode(),
            headers={"Content-Type": "application/json"},
        )
        try:
            with self.opener.open(req) as r:
                raw = r.read()
                return r.status, (json.loads(raw) if raw else None)
        except urllib.error.HTTPError as e:
            return e.code, None


def check(name, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + name + (f" — {detail}" if detail else ""))
    if not ok:
        failures.append(name)


def org(seed):
    s = Session(f"demo-hackathon-{seed}-organizer", PW if seed != SHARED else os.environ.get("E2E_DEMO_PASSWORD", "demo-pass-7"))
    _, me = s.call("GET", "/api/v1/accounts/me/")
    ws = me["memberships"][0]["workspace"]
    _, events = s.call("GET", f"/api/v1/workspaces/{ws}/events/")
    return s, ws, events[0]


def main():
    for seed in (A, B):
        manage("demo_scenario", "purge", f"demo-hackathon-{seed}")
    times = {}
    for seed in (A, B):
        rc, tail, secs = manage("demo_scenario", "create", "--seed", str(seed), "--participants", "4",
                                "--judges", "2", "--live", "2", "--password", PW, "--checkpoint", "submitted")
        times[seed] = secs
        check(f"create seed {seed} (4p/2j submitted)", rc == 0, f"{secs:.1f}s")
    try:
        sa, wa, ea = org(A)
        sb, wb, eb = org(B)
        check("distinct workspaces and event ids per seed", wa != wb and ea["public_id"] != eb["public_id"])
        check("per-seed organizer sees exactly one workspace/event",
              len(sa.call("GET", "/api/v1/accounts/me/")[1]["memberships"]) == 1)
        # isolated mutation: rename event A; B and shared seed must not change
        _, sh_ws, sh_ev = org(SHARED)
        before = (eb["name"], sh_ev["name"])
        code, _ = sa.call("PATCH", f"/api/v1/workspaces/{wa}/events/{ea['public_id']}/", {"name": "Mutated by probe A"})
        _, evs_a = sa.call("GET", f"/api/v1/workspaces/{wa}/events/")
        _, evs_b = sb.call("GET", f"/api/v1/workspaces/{wb}/events/")
        _, _, sh_ev2 = org(SHARED)
        check("mutation accepted on seed A", code == 200 and evs_a[0]["name"] == "Mutated by probe A", f"HTTP {code}")
        check("mutation on A invisible to seed B and shared seed", (evs_b[0]["name"], sh_ev2["name"]) == before)
        # negative: organizer A cannot read B's event
        code, _ = sa.call("GET", f"/api/v1/workspaces/{wb}/events/{eb['public_id']}/")
        check("cross-seed read denied (negative)", code in (403, 404), f"HTTP {code}")
        code, _ = sa.call("PATCH", f"/api/v1/workspaces/{wb}/events/{eb['public_id']}/", {"name": "x"})
        check("cross-seed write denied (negative)", code in (403, 404), f"HTTP {code}")
        # negative: duplicate seed is refused, not silently reused
        rc, tail, _ = manage("demo_scenario", "create", "--seed", str(A), "--participants", "4", "--judges", "2",
                             "--live", "2", "--password", PW, "--checkpoint", "submitted")
        check("duplicate seed refused with diagnostic (negative)", rc != 0 and "already exists" in " ".join(tail), " ".join(tail)[:120])
        # negative: live default invalid for tiny events
        rc, tail, _ = manage("demo_scenario", "create", "--seed", "9299", "--participants", "3", "--judges", "2",
                             "--password", PW, "--checkpoint", "submitted")
        check("3p/2j without --live 1 refused (negative)", rc != 0 and "live" in " ".join(tail), " ".join(tail)[:120])
        # purge leaves the other seed and shared seed intact
        manage("demo_scenario", "purge", f"demo-hackathon-{A}")
        _, evs_b2 = sb.call("GET", f"/api/v1/workspaces/{wb}/events/")
        check("purging A leaves B intact", evs_b2 and evs_b2[0]["name"] == before[0])
    finally:
        for seed in (A, B):
            manage("demo_scenario", "purge", f"demo-hackathon-{seed}")
        _, tail, _ = manage("demo_scenario", "list")
        check("probe seeds purged; shared seed still listed",
              f"demo-hackathon-{SHARED}" in subprocess.run(
                  ["docker", "compose", "exec", "-T", "app", "python", "manage.py", "demo_scenario", "list"],
                  capture_output=True, text=True).stdout)
    sys.exit(1 if failures else 0)


main()
