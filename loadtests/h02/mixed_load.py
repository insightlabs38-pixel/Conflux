"""Mixed-workload HTTP driver for PVS-H02 (stdlib only).

    python loadtests/h02/mixed_load.py PROFILE.json OUT.json [--base URL --seconds N --scale K]

Concurrent actor classes exercise the real service: anonymous gallery/search
browsing, participants autosaving and finalizing (with idempotent retries),
judges drafting and submitting ballots, organizers polling progress, voters,
and a results publication at the end. Each request is recorded by endpoint
name; only 2xx responses to first-time writes count towards `successes`, which
`seed.py verify` reconciles against the database.
"""

import argparse
import http.client
import json
import random
import threading
import time
from collections import defaultdict
from urllib.parse import urlsplit

p = argparse.ArgumentParser()
p.add_argument("profile")
p.add_argument("out")
p.add_argument("--base", default="http://127.0.0.1:18100")
p.add_argument("--seconds", type=int, default=45)
p.add_argument("--scale", type=float, default=1.0)
args = p.parse_args()
P = json.load(open(args.profile))
W, E, S, PL = P["workspace"], P["event"], P["stage"], P["plan"]
B = f"/api/v1/workspaces/{W}/events/{E}"
PLAN = f"{B}/stages/{S}/evaluation-plans/{PL}"
host = urlsplit(args.base)
lock = threading.Lock()
lat = defaultdict(list)
status = defaultdict(lambda: defaultdict(int))
successes = defaultdict(int)
mismatches = []
stop_at = time.monotonic() + args.seconds


class Client:
    seq = 0

    def __init__(self, token=None):
        self.token = token
        self.conn = None
        with lock:
            Client.seq += 1
            self.ip = f"10.{Client.seq // 65536 % 256}.{Client.seq // 256 % 256}.{Client.seq % 256}"

    def call(self, name, method, path, body=None, expect=(200,), first_write=None):
        headers = {"Host": "localhost", "Content-Type": "application/json",
                   "X-Forwarded-For": self.ip}
        if self.token:
            headers["Cookie"] = f"session={self.token}"
        data = json.dumps(body) if body is not None else None
        t0 = time.perf_counter()
        try:
            if self.conn is None:
                self.conn = http.client.HTTPConnection(host.hostname, host.port, timeout=60)
            self.conn.request(method, path, body=data, headers=headers)
            r = self.conn.getresponse()
            raw = r.read()
            code = r.status
        except Exception:
            self.conn = None
            code, raw = 599, b""
        ms = (time.perf_counter() - t0) * 1000
        with lock:
            lat[name].append(ms)
            status[name][code] += 1
            if first_write and code in first_write:
                successes[first_write[code]] += 1
            if code not in expect and not (first_write and code in first_write):
                mismatches.append((name, code, raw[:120].decode("utf8", "replace")))
        try:
            return code, json.loads(raw) if raw else None
        except ValueError:
            return code, None


def running():
    return time.monotonic() < stop_at


def browser():
    c, r = Client(), random.Random()
    while running():
        c.call("gallery", "GET", f"/api/v1/events/{E}/gallery/")
        c.call("search", "GET", f"/api/v1/events/{E}/search/?q={r.choice(['atlas', 'beacon', 'ledger'])}")
        c.call("health", "GET", "/api/v1/health/")
        time.sleep(r.uniform(0.05, 0.3))


def participant(i):
    who = P["participants"][i]
    c = Client(who["token"])
    base = f"{B}/projects/{who['project']}/submissions/"
    c.call("sub_list", "GET", base)
    rev = 0
    for n in range(4):
        code, body = c.call(
            "autosave", "PUT", f"{base}{S}/",
            {"draft_payload": {"notes": f"draft {n} " * 40}, "draft_revision": rev},
        )
        if code == 200:
            rev = body["draft_revision"]
        time.sleep(random.uniform(0.05, 0.4))
    c.call("finalize", "POST", f"{base}{S}/finalize/", {"draft_revision": rev},
           expect=(201,), first_write={201: "finalize"})
    c.call("finalize_retry", "POST", f"{base}{S}/finalize/", {"draft_revision": rev}, expect=(200,))
    c.call("sub_list", "GET", base)
    c.call("vote", "POST", f"{B}/voting/votes/",
           {"project": random.choice(P["finalized_projects"])}, expect=(201,),
           first_write={201: "vote"})
    c.call("vote_dupe", "POST", f"{B}/voting/votes/",
           {"project": random.choice(P["finalized_projects"])}, expect=(400,))


def judge(j):
    c, r = Client(P["judges"][j]), random.Random(j)
    projects = P["finalized_projects"][:]
    r.shuffle(projects)
    c.call("judge_events", "GET", f"/api/v1/workspaces/{W}/judge-events/")
    for proj in projects:
        if not running():
            break
        c.call("ballot_list", "GET", f"{PLAN}/ballots/")
        c.call("ballot_draft_put", "PUT", f"{PLAN}/ballots/{proj}/draft/",
               {"responses": {"impact": r.randint(0, 10)}, "comment": "wip"})
        c.call("ballot_draft_get", "GET", f"{PLAN}/ballots/{proj}/draft/")
        c.call("ballot_submit", "POST", f"{PLAN}/ballots/",
               {"project": proj, "comment": "ok", "responses": [
                   {"criterion_id": "impact", "score": r.randint(0, 10)},
                   {"criterion_id": "polish", "score": r.randint(0, 10)}]},
               expect=(201,), first_write={201: "ballot"})
        time.sleep(r.uniform(0.1, 0.6))


def organizer():
    c = Client(P["organizer"])
    while running():
        c.call("progress", "GET", f"{PLAN}/progress/")
        c.call("vote_results_org", "GET", f"{B}/voting/results/")
        time.sleep(0.5)


def spawn(target, *a):
    t = threading.Thread(target=target, args=a)
    t.start()
    return t


RACE = 20
live = [i for i in range(len(P["participants"]) - RACE) if i >= P["finalized"]]
n_part = min(len(live), int(len(live) * args.scale))
n_judge = min(len(P["judges"]), max(1, int(len(P["judges"]) * args.scale)))
n_browse = max(1, int(24 * args.scale))
threads = [spawn(participant, i) for i in live[:n_part]]
threads += [spawn(judge, j) for j in range(n_judge)]
threads += [spawn(browser) for _ in range(n_browse)]
threads += [spawn(organizer) for _ in range(2)]
t0 = time.monotonic()
for t in threads:
    t.join()
wall = time.monotonic() - t0



def race(label, n, fn):
    """Fire n identical requests at once; return the multiset of status codes."""
    barrier, codes = threading.Barrier(n), []

    def go():
        barrier.wait()
        codes.append(fn())

    ts = [threading.Thread(target=go) for _ in range(n)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    return label, sorted(codes)


race_results = []
fresh = list(range(len(P["participants"]) - RACE, len(P["participants"])))
for i in fresh:
    who = P["participants"][i]
    base = f"{B}/projects/{who['project']}/submissions/{S}/"
    tok = who["token"]
    race_results.append(race("autosave_same_revision", 8, lambda: Client(tok).call(
        "race_autosave", "PUT", base, {"draft_payload": {"notes": "race"}, "draft_revision": 0},
        expect=(200, 400))[0]))
    race_results.append(race("finalize", 8, lambda: Client(tok).call(
        "race_finalize", "POST", base + "finalize/", {"draft_revision": 1},
        expect=(200, 201))[0]))
    race_results.append(race("vote_same_user", 8, lambda: Client(tok).call(
        "race_vote", "POST", f"{B}/voting/votes/", {"project": P["finalized_projects"][0]},
        expect=(201, 400), first_write={201: "race_vote"})[0]))
for j in range(min(10, len(P["judges"]))):
    proj = P["finalized_projects"][-1 - j]
    body = {"project": proj, "responses": [{"criterion_id": "impact", "score": 5},
                                           {"criterion_id": "polish", "score": 5}]}
    race_results.append(race("ballot_same_judge_project", 8, lambda: Client(P["judges"][j]).call(
        "race_ballot", "POST", f"{PLAN}/ballots/", body, expect=(201, 400),
        first_write={201: "race_ballot"})[0]))
race_bad = [
    (label, codes) for label, codes in race_results
    if (label == "autosave_same_revision" and codes.count(200) != 1)
    or (label == "finalize" and codes.count(201) != 1)
    or (label == "vote_same_user" and codes.count(201) != 1)
    or (label == "ballot_same_judge_project" and codes.count(201) > 1)
    or any(c >= 500 for c in codes)
]
successes["ballot"] += successes.pop("race_ballot", 0)
successes["vote"] += successes.pop("race_vote", 0)
successes["finalize"] += sum(codes.count(201) for label, codes in race_results if label == "finalize")

org = Client(P["organizer"])
code, run = org.call("normalize", "POST", f"{PLAN}/normalization-runs/", {}, expect=(200, 201))
if code in (200, 201) and run:
    org.call("publish_results", "POST", f"{PLAN}/publish-results/",
             {"normalization_run": run["public_id"]}, expect=(200, 201))
for _ in range(5):
    org.call("results", "GET", f"{PLAN}/results/")
    org.call("results_csv", "GET", f"{PLAN}/results.csv")


def pct(xs, q):
    xs = sorted(xs)
    return round(xs[min(len(xs) - 1, int(len(xs) * q))], 1)


summary = {
    name: {"n": len(v), "p50": pct(v, 0.5), "p95": pct(v, 0.95), "p99": pct(v, 0.99),
           "max": round(max(v), 1), "status": dict(status[name])}
    for name, v in sorted(lat.items())
}
total = sum(len(v) for v in lat.values())
out = {
    "wall_s": round(wall, 1), "requests": total, "rps": round(total / wall, 1),
    "actors": {"participants": n_part, "judges": n_judge, "browsers": n_browse, "organizers": 2},
    "server_errors": sum(c for s in status.values() for k, c in s.items() if k >= 500),
    "successes": {k: successes[k] for k in ("ballot", "vote", "finalize")},
    "races": {"total": len(race_results), "violations": race_bad[:10]},
    "unexpected": mismatches[:20], "unexpected_count": len(mismatches), "endpoints": summary,
}
json.dump(out, open(args.out, "w"), indent=1)
print(json.dumps({k: out[k] for k in ("wall_s", "requests", "rps", "actors", "server_errors", "successes", "unexpected_count", "races")}))
for k, v in summary.items():
    print(f"{k:18} n={v['n']:5} p50={v['p50']:7} p95={v['p95']:8} p99={v['p99']:8} max={v['max']:8} {v['status']}")
for m in mismatches[:8]:
    print("UNEXPECTED", m)
