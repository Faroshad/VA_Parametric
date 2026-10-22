"""Which rooms of the floor each body can reach (Staff brain, one room per run, fresh life folder each time).
Body values follow the VA Body family formulas for Farshad's type (Adult Male P50, stature 5.75 ft, shoulders 1.6 ft)."""
import copy, json, os, shutil, sys

from run_scenarios import snap0, rooms, entrance, FARSHAD, LEVEL, OUT, Simulation

BODIES = {  # mobility code, clear width ft, speed ft/s, eye height ft, in wheelchair
    "Ambulant":   (1, 1.6 + 0.25, 4.40, 0.936 * 5.75, 0),
    "Cane":       (3, 1.6 + 0.50, 2.66, 0.936 * 5.75, 0),
    "Walker":     (4, 2.50,       1.87, 0.936 * 5.75, 0),
    "Wheelchair": (2, 2.6667,     2.26, 1.6 + 0.45 * 5.75, 1),
}


def body_snap(name, brain="Staff"):
    code, clear, speed, eye, chair = BODIES[name]
    snap = copy.deepcopy(snap0)
    snap["agents"] = [a for a in snap["agents"] if a["uid"] == FARSHAD]
    p = snap["agents"][0]["params"]
    p.update({"Pawn Mobility Code": code, "Pawn Clear Width": clear, "Pawn Speed": speed, "Pawn Eye Height": eye,
              "Pawn In Wheelchair": chair, "Pawn Is Seated": chair, "Pawn Brain Profile": brain,
              "Pawn Mobility": name})
    return snap


if __name__ == "__main__":
    table = {}
    for body in BODIES:
        for n, r in sorted(rooms.items()):
            tag = f"reach_{body}_{n}"
            root = os.path.join(OUT, "reach_agents", tag)
            shutil.rmtree(root, ignore_errors=True)
            spec = {"sim": "Visit", "run_id": tag, "agents": [FARSHAD], "entrance": entrance,
                    "stops": [{"x": r["point"][0], "y": r["point"][1], "level": LEVEL, "wait": 1, "label": f"{n} {r['name']}"}]}
            rd = os.path.join(OUT, "reach_runs", tag); os.makedirs(rd, exist_ok=True)
            out = Simulation(body_snap(body), spec, root, rd, 7).run()
            act = out["agents"][FARSHAD]["final"]["Pawn Activity"]
            ok = act.startswith("visited 1 of 1")
            table.setdefault(body, {})[n] = {"ok": ok, "why": "" if ok else act.split("skipped ", 1)[-1]}
        print(body, " ".join(f"{n}:{'Y' if v['ok'] else 'n'}" for n, v in table[body].items()), flush=True)
    json.dump(table, open(os.path.join(OUT, "reach.json"), "w"), indent=1)
