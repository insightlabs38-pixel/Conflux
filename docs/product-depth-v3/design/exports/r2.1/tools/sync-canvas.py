#!/usr/bin/env python3
"""Keeps canvas.json in step with the *.dc.html boards (size from $preview, new boards laid out in rows).
Usage: python3 docs/product-depth-v3/design/exports/r2.1/tools/sync-canvas.py"""
import json, re, pathlib
P = pathlib.Path(__file__).resolve().parent.parent / "canvas/project"
idx = json.loads((P / "canvas.json").read_text())
NEW = {  # file -> (row, title)
 "Sys-Dark.dc.html": ("dark", "D1 · Dark foundations & components"),
 "Dark-Organizer.dc.html": ("dark", "D13 · Dark · organizer shell + data surface"),
 "Dark-Judge.dc.html": ("dark", "D13 · Dark · judge review"),
 "Dark-MyEvent.dc.html": ("dark2", "D13 · Dark · participant My Event"),
 "Dark-Overlays.dc.html": ("dark2", "D13 · Dark · overlays, dialogs, focus"),
 "Resp-1024.dc.html": ("resp", "D14 · 1024 organizer / tablet"),
 "Resp-768.dc.html": ("resp", "D14 · 768 judge review (narrow tablet)"),
 "Wide-1920.dc.html": ("wide", "D14 · 1920 wide operator + 5,000-person stress fixture"),
 "Pairwise-Compare.dc.html": ("pair", "D6b · Pairwise judging · compare"),
 "Pairwise-States.dc.html": ("pair2", "D6b · Pairwise · recusal, tie, hybrid, history"),
 "Pairwise-Narrow.dc.html": ("pair2", "D6b · Pairwise · narrow fallback"),
}
ROWY = {"dark": 18000, "dark2": 19400, "resp": 20800, "wide": 22100, "pair": 23800, "pair2": 24900}
NOTES = {"t-dark": ("D13 — Dark mode (representative)", 17770, 4480), "t-resp": ("D14 — Intermediate & wide responsive", 20570, 4480), "t-pair": ("D6b — Pairwise judging", 23570, 4480)}
cur = {}
for f in sorted(P.glob("*.dc.html")):
    m = re.search(r'\$preview":\{"width":(\d+),"height":(\d+)', f.read_text())
    w, h = int(m[1]), int(m[2])
    b = idx["boards"].get(f.name)
    if b is None:
        row, title = NEW[f.name]
        x = cur.get(row, 0); cur[row] = x + w + 80
        b = {"title": title, "x": x, "y": ROWY[row]}
        idx["boards"][f.name] = b
        if f.name not in idx["order"]: idx["order"].append(f.name)
    b["w"], b["h"] = w, h
for k, (t, y, mw) in NOTES.items():
    idx["notes"][k] = {"kind": "title1", "maxW": mw, "text": t, "w": 240, "x": 0, "y": y}
idx["boards"]["Main.dc.html"]["title"] = "00 · Index & revision r2.1"
idx["title"] = "Conflux v3 Design r2.1"
(P / "canvas.json").write_text(json.dumps(idx, indent=2, sort_keys=True))
print(len(idx["boards"]), "boards")
