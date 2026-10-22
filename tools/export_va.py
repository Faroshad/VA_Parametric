"""Data for the VA page (assets/data/va.js): the floor plan, the access table per body, and three runs of the same
person (Visitor 1st visit, Visitor 2nd visit, Staff) with the moment each 10 ft square, door and room enters memory.
Runs again on copies (scratch folders) with a recorder wrapped around Person.perceive; the engine itself is unchanged."""
import json, os, shutil, sys

import run_scenarios as rs
from pawn_engine import sim as S

OUT_JSON = r"E:\Academic\PhD\Fall 2026\BIM\VA_Parametric\assets\data\va.js"
snap, L = rs.snap0, rs.LEVEL
R1 = lambda v: round(v, 1)
STATE = {"walking": "w", "searching": "s", "waiting": "p", "done": "d", "queued": "q"}

# ---- record memory as it forms ------------------------------------------------------------------------------
LOG = {}
_orig = S.Person.perceive


def known(mem):
    return ({tuple(c) for c in mem.get("seen", [])}, set(mem.get("doors", {})), set(mem.get("rooms", {})))


def perceive(self):
    log = LOG.setdefault(self.name, {"prior": None, "events": []})
    before = known(self.mem)
    if log["prior"] is None:
        log["prior"] = before
    _orig(self)
    after = known(self.mem)
    t = round(self.sim.t, 1)
    for kind, b, a in zip("sdr", before, after):
        for k in sorted(a - b):
            log["events"].append([t, kind, list(k) if kind == "s" else k])


S.Person.perceive = perceive

# ---- plan ---------------------------------------------------------------------------------------------------
rooms = [r for r in snap["rooms"] if r["level"] == L]
room_no = {r["uid"]: r["number"] for r in rooms}
doors = [d for d in snap["doors"] if d["level"] == L]
door_ix = {d["uid"]: i for i, d in enumerate(doors)}
plan = {
    "walls": [{"w": round(w["width"], 2), "p": [[R1(x), R1(y)] for x, y in w["pts"]]} for w in snap["walls"] if w["level"] == L],
    "doors": [{"x": R1(d["xyz"][0]), "y": R1(d["xyz"][1]), "w": round(d["width"], 2), "f": [round(v, 3) for v in d["facing"]]} for d in doors],
    "rooms": [{"n": r["number"], "name": r["name"], "c": [R1(r["point"][0]), R1(r["point"][1])],
               "loops": [[[R1(x), R1(y)] for x, y in lp] for lp in r["loops"]]} for r in rooms],
    "furniture": [[R1(o["min"][0]), R1(o["min"][1]), R1(o["max"][0]), R1(o["max"][1])] for o in snap["obstacles"]
                  if o["level"] == L and o.get("cat") == "Furniture"],
}
xs = [x for w in plan["walls"] for x, _ in w["p"]]
ys = [y for w in plan["walls"] for _, y in w["p"]]
plan["bounds"] = [min(xs), min(ys), max(xs), max(ys)]

# ---- the three runs -----------------------------------------------------------------------------------------
for d in ("A_visit1", "B_visit2", "C_staff", "agents_visitor", "agents_staff"):
    shutil.rmtree(os.path.join(rs.OUT, d), ignore_errors=True)
runs = []
for tag, brain, root, label in [("A_visit1", "Visitor", "agents_visitor", "Visitor · 1st visit"),
                                ("B_visit2", "Visitor", "agents_visitor", "Visitor · 2nd visit"),
                                ("C_staff", "Staff", "agents_staff", "Staff")]:
    LOG.clear()
    rs.scenario(tag, brain, root)
    res = json.load(open(os.path.join(rs.OUT, tag, "results.json"), encoding="utf-8"))
    a = res["agents"][rs.FARSHAD]
    log = LOG["Farshad"]
    sq, dr, rm = log["prior"]
    conv = lambda k, v: v if k == "s" else (door_ix.get(v, -1) if k == "d" else room_no.get(v, "?"))
    runs.append({
        "key": tag, "label": label, "brain": brain,
        "time": a["final"]["Pawn Run Time"], "dist": round(a["final"]["Pawn Run Distance"]), "detour": a["final"]["Pawn Run Detour"],
        "memory": a["final"]["Pawn Memory"],
        "track": [[f[0], R1(f[1]), R1(f[2]), STATE.get(f[5], f[5][:1])] for f in a["frames"][::2]],   # every 1 s: t, x, y, state
        "prior": {"s": sorted(list(c) for c in sq), "d": sorted(door_ix[u] for u in dr if u in door_ix), "r": sorted(room_no.get(u, "?") for u in rm)},
        "events": [[t, k, conv(k, v)] for t, k, v in log["events"] if not (k == "d" and v not in door_ix)],
    })
    print(tag, len(runs[-1]["track"]), "samples,", len(runs[-1]["events"]), "memory events, prior", {k: len(v) for k, v in runs[-1]["prior"].items()})

reach = json.load(open(os.path.join(rs.OUT, "reach.json")))
data = {
    "note": "Pawn engine runs on Project1_v01 (floor at level id 1246930), feet. Generated for this page; see export_va.py.",
    "entrance": [R1(rs.entrance["x"]), R1(rs.entrance["y"])],
    "stops": [{"n": n, "c": [R1(r["c"][0]), R1(r["c"][1])]} for n in rs.STOPS for r in plan["rooms"] if r["n"] == n],
    "plan": plan,
    "reach": {b: {n: v["ok"] for n, v in t.items()} for b, t in reach.items()},
    "reach_why": {b: {n: v["why"].split(": ", 2)[-1] for n, v in t.items() if not v["ok"]} for b, t in reach.items()},
    "runs": runs,
}
os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
open(OUT_JSON, "w", encoding="utf-8").write("window.VA_DATA = " + json.dumps(data, separators=(",", ":"), ensure_ascii=False) + ";\n")
print("wrote", OUT_JSON, os.path.getsize(OUT_JSON) // 1024, "KB")
