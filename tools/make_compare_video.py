"""Farshad and X, the real run in Project1_v01 (20261021-190101): what each saw (Revit's own first-person renders, one
per simulated second) above the plan, where each one's track and memory (10 ft squares seen, doors known) grow.
The run is simulated again on a copy with a recorder on perception; the tracks are checked against the saved results.
Output: VA_Parametric/assets/video/Farshad_X_compare.mp4, 1280x720, 24 fps = 24 simulated seconds per second."""
import csv, json, os, shutil, subprocess, sys

import run_scenarios as rs
from pawn_engine import sim as S
from PIL import Image, ImageDraw, ImageFont

PAWN = rs.PAWN
RUN = os.path.join(PAWN, r"08_runs\20261021-190101 Visit Project1_v01")
EGO = {n: os.path.join(PAWN, rf"07_agents\{n}\runs\20261021-190101 Visit Project1_v01\ego") for n in ("Farshad", "X")}
OUT = r"E:\Academic\PhD\Fall 2026\BIM\VA_Parametric\assets\video\Farshad_X_compare.mp4"
COL = {"Farshad": (90, 162, 219), "X": (76, 187, 110)}
W, H, FPS = 1280, 720, 24

# ---- memory along the SAVED tracks (the ones Revit rendered) -----------------------------------------------------
# A fresh simulation of this job is not bit-identical to the saved one (iteration order differs between processes),
# so the saved tracks are used and the engine's own perception tests are replayed at each saved position:
# the 10 ft squares around the body, the doors a sight line from the eyes reaches, the rooms entered.
import math
from pawn_engine.settings import SIGHT
job = json.load(open(os.path.join(RUN, "job.json"), encoding="utf-8-sig"))
saved = json.load(open(os.path.join(RUN, "results.json"), encoding="utf-8"))
scratch = os.path.join(rs.OUT, "realrun")
shutil.rmtree(scratch, ignore_errors=True)
sim0 = S.Simulation(job["snapshot"], job["spec"], os.path.join(scratch, "agents"), os.path.join(scratch, "run"), job.get("seed", 7))
world, L = sim0.world, rs.LEVEL
grid = world.grid(L)
eye = {p.name: p.eye for p in sim0.people}
tracks = {a["name"]: a["frames"] for a in saved["agents"].values()}
LOG = {}
for n, fr in tracks.items():
    seen, dk, rk, lg = set(), set(), set(), []
    for t, x, y, *_ in fr:
        i0, j0 = int(x // 10), int(y // 10)
        for di in (-1, 0, 1):
            for dj in (-1, 0, 1):
                c = (i0 + di, j0 + dj)
                if c not in seen:
                    seen.add(c); lg.append((t, "s", c))
        r = grid.room_at(x, y)
        if r and r not in rk:
            rk.add(r); lg.append((t, "r", r))
        for d in world.doors.values():
            if d.level == L and d.uid not in dk and math.hypot(d.x - x, d.y - y) <= SIGHT and grid.sees_door(x, y, d, eye[n]):
                dk.add(d.uid); lg.append((t, "d", d.uid))
    LOG[n] = lg
    print(n, "eye", round(eye[n], 2), "squares", len(seen), "doors", len(dk), "rooms", len(rk), flush=True)
T = int(max(f[-1][0] for f in tracks.values())) + 1

# ---- plan geometry --------------------------------------------------------------------------------------------
snap = job["snapshot"]
doors = {d["uid"]: d for d in snap["doors"] if d["level"] == L}
PX, PY, PS = 460, 368, 344          # plan box: left, top, size (px); the floor is 121.6 ft across
x0, y0, x1, y1 = -61.5, -61.5, 61.5, 61.5
sc = PS / (x1 - x0)
P = lambda x, y: (PX + (x - x0) * sc, PY + (y1 - y) * sc)

bg = Image.new("RGB", (W, H), (0, 0, 0))
d = ImageDraw.Draw(bg)
for o in snap["obstacles"]:
    if o["level"] == L and o.get("cat") == "Furniture":
        a, b = P(o["min"][0], o["max"][1]), P(o["max"][0], o["min"][1])
        d.rectangle([a, b], fill=(34, 34, 38))
for w in snap["walls"]:
    if w["level"] == L:
        d.line([P(x, y) for x, y in w["pts"]], fill=(150, 150, 158), width=max(1, round(w["width"] * sc * 0.6)))
for dd in doors.values():
    x, y, hw = dd["xyz"][0], dd["xyz"][1], dd["width"] / 2
    fx, fy = dd["facing"]
    d.line([P(x - fy * hw, y + fx * hw), P(x + fy * hw, y - fx * hw)], fill=(0, 0, 0), width=3)

mono = lambda s: ImageFont.truetype(r"C:\Windows\Fonts\consola.ttf", s)
F12, F14, F18 = mono(12), mono(14), mono(18)


def ego_frames(name):
    rows = list(csv.DictReader(open(os.path.join(EGO[name], "frames.csv"))))
    return [(float(r["t_s"]), os.path.join(EGO[name], f"frame_{int(r['frame']):05d}.png")) for r in rows]


EG = {n: ego_frames(n) for n in COL}
ev = {n: sorted(LOG[n], key=lambda e: e[0]) for n in COL}
mem_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
trk_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
md, td = ImageDraw.Draw(mem_layer), ImageDraw.Draw(trk_layer)
ei = {n: 0 for n in COL}
fi = {n: 0 for n in COL}
known = {n: {"s": 0, "d": set(), "r": set()} for n in COL}
last = {n: None for n in COL}
STATE = {"searching": "searching", "walking": "walking", "waiting": "waiting", "done": "done"}

ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                       "-c:v", "libx264", "-preset", "slow", "-crf", "26", "-pix_fmt", "yuv420p", "-movflags", "+faststart", OUT],
                      stdin=subprocess.PIPE)
for k in range(T + FPS * 2):                       # one frame per simulated second, 2 s hold at the end
    t = min(k, T)
    for n, c in COL.items():
        while ei[n] < len(ev[n]) and ev[n][ei[n]][0] <= t:
            _, kind, v = ev[n][ei[n]]; ei[n] += 1
            if kind == "s":
                known[n]["s"] += 1
                i, j = v
                md.rectangle([P(i * 10, j * 10 + 10), P(i * 10 + 10, j * 10)], fill=c + (34,))
            elif kind == "d":
                known[n]["d"].add(v)
                if v in doors:
                    x, y = doors[v]["xyz"][:2]; q = P(x, y)
                    md.ellipse([q[0] - 3, q[1] - 3, q[0] + 3, q[1] + 3], outline=c + (255,), width=2)
            else:
                known[n]["r"].add(v)
        fr = tracks[n]
        while fi[n] < len(fr) and fr[fi[n]][0] <= t:
            q = P(fr[fi[n]][1], fr[fi[n]][2])
            if last[n]:
                td.line([last[n], q], fill=c + (230,), width=2)
            last[n] = q; fi[n] += 1
    img = bg.copy().convert("RGBA")
    img.alpha_composite(mem_layer); img.alpha_composite(trk_layer)
    dr = ImageDraw.Draw(img)
    for side, (n, c) in enumerate(COL.items()):
        fr = tracks[n][max(0, fi[n] - 1)]
        done = t >= fr[0] + 0.5 and fi[n] >= len(tracks[n])
        state = "done" if done else fr[5]
        q = P(fr[1], fr[2]); dr.ellipse([q[0] - 5, q[1] - 5, q[0] + 5, q[1] + 5], fill=c + (255,), outline=(255, 255, 255, 255))
        # first-person frame (the last render at or before t)
        frames = EG[n]
        j = min(range(len(frames)), key=lambda m: abs(frames[m][0] - min(t, frames[-1][0])))
        eg = Image.open(frames[j][1]).convert("RGB")
        if done:
            eg = Image.blend(eg, Image.new("RGB", eg.size, (0, 0, 0)), 0.55)
        img.paste(eg, (side * 640, 0))
        dr.rectangle([side * 640, 0, side * 640 + 639, 359], outline=(40, 40, 44))
        dr.rectangle([side * 640 + 12, 12, side * 640 + 22, 22], fill=c)
        dr.text((side * 640 + 30, 9), n.upper(), font=F18, fill=(236, 236, 238))
        dr.text((side * 640 + 30, 32), "what he saw · Revit render", font=F12, fill=(170, 170, 178))
        # numbers beside the plan
        tx = 40 if side == 0 else 860
        walked = sum(((a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2) ** 0.5 for a, b in zip(tracks[n][1:fi[n]], tracks[n][:fi[n] - 1]))
        lines = [(n.upper(), F18, (236, 236, 238)), (state, F14, c), ("", F12, None),
                 (f"walked   {walked:6.0f} ft", F14, (236, 236, 238)),
                 (f"memory   {known[n]['s'] * 100:6d} ft² seen", F14, (236, 236, 238)),
                 (f"         {len(known[n]['d']):6d} doors known", F14, (236, 236, 238)),
                 (f"         {len(known[n]['r']):6d} rooms entered", F14, (236, 236, 238))]
        yy = 420
        for s_, f_, c_ in lines:
            if c_: dr.text((tx, yy), s_, font=f_, fill=c_)
            yy += 26 if f_ is F18 else 22
    mm, ss = divmod(t, 60)
    dr.text((W // 2, 694), f"t = {mm:02d}:{ss:02d}   ·   24× real time   ·   Pawn engine, Project1_v01", font=F12, fill=(141, 141, 148), anchor="mm")
    dr.rectangle([0, H - 4, int(W * t / T), H], fill=(141, 141, 148))
    ff.stdin.write(img.convert("RGB").tobytes())
    if k % 300 == 0:
        print("frame", k, "of", T, flush=True)
ff.stdin.close(); ff.wait()
print("wrote", OUT, os.path.getsize(OUT) // 1024, "KB")
