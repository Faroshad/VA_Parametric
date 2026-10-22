"""Brain and memory comparison for the VA page, run with the Pawn engine on COPIES (scratch folders only).

Same body (Farshad, Adult Male P50 with a walking frame, as placed in Project1_v01), same floor, same entrance and
four room stops. Runs:
  A  Visitor, first visit   (empty life folder)
  B  Visitor, second visit  (the life folder A left behind: its memory of this building)
  C  Staff                  (knows the plan; its own empty life folder)
Nothing is written under BIM\\Pawn: agents_root and run_dir are in this script's folder.
"""
import copy, json, os, sys, time

PAWN = r"E:\Academic\PhD\Fall 2026\BIM\Pawn"
JOB = os.path.join(PAWN, r"08_runs\20261021-190101 Visit Project1_v01\job.json")
sys.path.insert(0, os.path.join(PAWN, "04_engine"))
from pawn_engine.sim import Simulation  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "runs")
LEVEL = 1246930
FARSHAD = "d60e6acb-7bd2-4e44-8cb2-74caedad4ac2-0019a1c0"
STOPS = ["102", "100"]   # Office 02, Restroom: the two rooms this body can enter
WAIT = 20

job = json.load(open(JOB, encoding="utf-8-sig"))
snap0 = job["snapshot"]
rooms = {r["number"]: r for r in snap0["rooms"] if r["level"] == LEVEL}
entrance = job["spec"]["entrances"][FARSHAD]


def scenario(tag, brain, agents_root, seed=7):
    snap = copy.deepcopy(snap0)
    snap["agents"] = [a for a in snap["agents"] if a["uid"] == FARSHAD]
    snap["agents"][0]["params"]["Pawn Brain Profile"] = brain
    spec = {"sim": "Visit", "run_id": f"va-{tag}", "agents": [FARSHAD], "entrance": entrance,
            "stops": [{"x": rooms[n]["point"][0], "y": rooms[n]["point"][1], "level": LEVEL, "wait": WAIT,
                       "label": f"{n} {rooms[n]['name']}"} for n in STOPS]}
    run_dir = os.path.join(OUT, tag)
    os.makedirs(run_dir, exist_ok=True)
    t0 = time.time()
    out = Simulation(snap, spec, os.path.join(OUT, agents_root), run_dir, seed).run()
    a = out["agents"][FARSHAD]
    print(f"{tag}: brain {brain}, simulated {out['t_end']:.0f} s in {time.time() - t0:.0f} s; {a['final']['Pawn Activity']}; "
          f"time {a['final']['Pawn Run Time']}, dist {a['final']['Pawn Run Distance']:.0f}, detour {a['final']['Pawn Run Detour']}, "
          f"memory: {a['final']['Pawn Memory']}", flush=True)


if __name__ == "__main__":
    which = sys.argv[1:] or ["A", "B", "C"]
    if "A" in which: scenario("A_visit1", "Visitor", "agents_visitor")
    if "B" in which: scenario("B_visit2", "Visitor", "agents_visitor")
    if "B2" in which: scenario("B2_visit3", "Visitor", "agents_visitor")
    if "C" in which: scenario("C_staff", "Staff", "agents_staff")
