"""r/dataisbeautiful collage for tsunamis: 2400 x 3200 px, light background. Numbers from data/results.json.
Map labels sit on open sea or on the paper around the globe, with a halo, and are checked against land, every source
circle, every runup dot and each other; a leader line, where needed, must not cross another label."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "code"))
from figstyle import *
import matplotlib.patheffects as pe
from matplotlib.patches import Patch, Circle
from matplotlib.lines import Line2D
from shapely.geometry import box as _box, Point as _Pt, LineString as _LS, Polygon as _Poly
from shapely.ops import unary_union, nearest_points
from shapely.prepared import prep as _prep
from shapely.strtree import STRtree

R = jload(f"{DATA}/results.json")
EV = events(); RU, RC = runups()
BGc = "#F7F5F0"; SEAc = "#E6EDF1"; LANDc = "#E2DDD1"
HALO = [pe.withStroke(linewidth=4, foreground=SEAc)]
HALOP = [pe.withStroke(linewidth=4, foreground=BGc)]
GCOLS = [c for _, c in GROUPS]
s, C, F, D = R["source"], R["causes"], R["famous"], R["deaths"]

fig = plt.figure(figsize=(12, 16.0), dpi=200, facecolor=BGc)
fig.text(.045, .9844, "Every tsunami on record", fontproperties=DISP, fontsize=46, color=FG, va="top")
fig.text(.045, .9375, f"{s['n']:,} tsunamis since {s['first_name']}, and the {R['page']['runups']:,} places where their water was recorded.\n"
         f"{C['Earthquake']['pct']:.0f}% started with an earthquake, {R['ring']['pct']:.0f}% on the rim of the Pacific. One morning in 2004 accounts\nfor {D['y2004_pct']:.0f}% of all {D['total']:,} recorded tsunami deaths.",
         fontproperties=SERP, fontsize=14, color=FG, va="top", linespacing=1.25)

# ---- map
ax = fig.add_axes([0, .495, 1, .375])
outline(ax, fc=SEAc, ec="#C9CDD0", lw=.8); world(ax, lw=.3, land=LANDc, ec=BGc); plates(ax, lw=.6, alpha=.45)
A = np.array([[r["lon"], r["lat"], r["ht"] if r["ht"] is not None else np.nan] for r in RU]); A = A[np.argsort(np.nan_to_num(A[:, 2], nan=-1))]
dx, dy = proj(A[:, 0], A[:, 1]); ax.scatter(dx, dy, s=1.1, c=[hcol(h) for h in A[:, 2]], lw=0, alpha=.75, zorder=3)
E = sorted([e for e in EV if e["lat"] is not None], key=lambda e: -(e["deaths"] or 0))
KS = 1.0
area = lambda d: KS * (5 + .03 * d) if d else 3.5 * KS
ex, ey = proj([e["lon"] for e in E], [e["lat"] for e in E])
ax.scatter(ex, ey, s=[area(e["deaths"] or 0) for e in E], c=[GCOLS[e["g"]] for e in E], alpha=.85, ec="#fff", lw=.4, zorder=4)

# ---- obstacles in map metres
fig.canvas.draw(); REN = fig.canvas.get_renderer()
m_per_pt = (ax.get_xlim()[1] - ax.get_xlim()[0]) / (ax.get_window_extent().width * 72 / fig.dpi)
_land = [_Poly(p).buffer(0) for _, p in SHAPES if len(p) >= 3]
LAND = unary_union(_land).buffer(4e4); LANDP = _prep(LAND)
BUB = [(float(x), float(y), max(np.sqrt(area(e["deaths"] or 0) / np.pi) * m_per_pt + 2e4, 6e4)) for x, y, e in zip(ex, ey, E)]
BUBT = STRtree([_Pt(x, y).buffer(r) for x, y, r in BUB])
DOTT = STRtree([_Pt(x, y) for x, y in zip(dx, dy)])
PLACED, LINES = [], []
NLEAD = [0]; WHY = []; import collections; STAT = collections.Counter()


def tbox(t):
    bb = t.get_window_extent(REN)
    (x0, y0), (x1, y1) = ax.transData.inverted().transform([[bb.x0 - 6, bb.y0 - 4], [bb.x1 + 6, bb.y1 + 4]])
    return _box(x0, y0, x1, y1)


def hits(b):
    return len(BUBT.query(b, predicate="intersects")) > 0 or len(DOTT.query(b, predicate="intersects")) > 0


def bad(b):
    x0, x1 = ax.get_xlim(); y0, y1 = ax.get_ylim()
    if not _box(x0 + 1e5, y0 + 1e5, x1 - 1e5, y1 - 1e5).contains(b): return True
    return LANDP.intersects(b) or hits(b) or any(b.intersects(o) for _, _, o in PLACED) or any(b.intersects(l) for _, l in LINES)


def place(name, txt, kf, pref, ha="center", col=FG, size=10, w="medium", lead_gap=2.5e5, maxr=40, step=1.0):
    f = F[kf]; tx, ty = proj(f["lon"], f["lat"]); tx, ty = float(tx), float(ty)
    rr = max(np.sqrt(area(f["deaths"] or 0) / np.pi) * m_per_pt, 6e4)
    t = ax.text(0, 0, txt, ha=ha, va="center", fontsize=size, color=col, family=MONO, linespacing=1.15, zorder=10, path_effects=HALO, fontweight=w)
    lon0, lat0 = pref
    STAT.clear(); NLEAD[0] = 0
    cands = [(lon0, lat0)] + [(lon0 + i * step, lat0 + j * step) for r in range(1, maxr + 1) for i in range(-r, r + 1) for j in range(-r, r + 1) if max(abs(i), abs(j)) == r]
    for lon, lat in cands:
        if abs(lat) > 80 or abs(float(wrap(lon)) - float(wrap(f["lon"]))) > 70: continue   # never across the seam
        x, y = proj(lon, lat); t.set_position((float(x), float(y))); b = tbox(t)
        STAT[("land" if LANDP.intersects(b) else "") + ("hit" if hits(b) else "")] += 1
        if bad(b):
            if not LANDP.intersects(b) and not hits(b): WHY.append([n for n, _, o in PLACED if b.intersects(o)] + [n for n, l in LINES if b.intersects(l)])
            continue
        c = _Pt(tx, ty); gap = b.distance(c) - rr; ln = None
        if gap > lead_gap:
            pb, _ = nearest_points(b, c); d = np.hypot(pb.x - c.x, pb.y - c.y)
            ln = _LS([(pb.x, pb.y), (c.x + (pb.x - c.x) * rr / d, c.y + (pb.y - c.y) * rr / d)])
            if any(ln.intersects(o) for _, _, o in PLACED): NLEAD[0] += 1; continue
        PLACED.append((name, t, b))
        if ln is not None:
            LINES.append((name, ln)); ax.plot(*ln.xy, color=FG, lw=.7, zorder=9)
        return
    t.remove(); fig.savefig("/tmp/claude-0/-home-claude/9791f396-0812-550b-8fd1-2ad33918f115/scratchpad/fail.png", dpi=60, facecolor=BGc)
    raise RuntimeError(f"no clean spot for {name} (leader conflicts {NLEAD[0]}, tried {len(cands)}) {STAT}")


dl = {d["id"]: d for d in R["deadliest"]}
place("lisbon", f"LISBON 1755\n{F['lisbon']['deaths']:,}", "lisbon", (-22, 30), lead_gap=6e5)
place("sumatra", f"INDIAN OCEAN 2004\n{F['sumatra']['deaths']:,} deaths", "sumatra", (72, -14))
place("krakatau", f"KRAKATAU 1883\n{F['krakatau']['deaths']:,}", "krakatau", (112, -30))
place("lituya", f"LITUYA BAY 1958\nwater {F['lituya']['max_run']:.0f} m up", "lituya", (-150, 48), col="#5B3F86")
place("japan", f"SANRIKU 1896 {F['sanriku']['deaths']:,}\nTOHOKU 2011 {F['tohoku']['deaths']:,}", "tohoku", (160, 28), size=9.5)
place("chile", f"CHILE 1960\nmagnitude {F['chile']['mag']}", "chile", (-95, -42))
place("tonga", "HUNGA TONGA 2022", "tonga", (-160, -28), col="#9A2620")
for nm, t, b in PLACED:
    assert not LANDP.intersects(b) and not hits(b), nm
    assert not any(b.intersects(o) for n2, _, o in PLACED if n2 != nm), nm
for nm, l in LINES:
    assert not any(l.intersects(o) for n2, _, o in PLACED if n2 != nm), nm
print("labels ok:", len(PLACED), "leaders:", [n for n, _ in LINES])

# size key on the paper, right of the cause legend (scatter sizes are in points, the same scale as the map)
k = fig.add_axes([.76, .425, .2, .045]); k.axis("off"); k.set_xlim(0, 3); k.set_ylim(0, 1)
for i, n in enumerate((1000, 10000, 50000)):
    k.scatter([.4 + i * 1.0], [.62], s=area(n), fc="none", ec=FG, lw=.9, clip_on=False)
    k.text(.4 + i * 1.0, -.15, f"{n:,}", ha="center", fontsize=9, color=FG)
k.text(1.4, 1.12, "tsunami deaths (circle area)", ha="center", fontsize=9, color=FG)

# ---- legend under the map
LP = SERP.copy(); LP.set_size(11.5)
fig.text(.045, .508, "Circles: tsunami sources, area = deaths caused by the tsunami, colour = cause. Dots: places the water was recorded, colour = height.", fontsize=9.4, color=MUT, va="top")
H = [Patch(color=c, label=g) for g, c in GROUPS] + [Line2D([], [], ls=(0, (3, 2)), color=PLATE, label="plate boundary")]
fig.legend(handles=H, loc="upper left", bbox_to_anchor=(.035, .497), ncol=4, frameon=False, prop=LP, handletextpad=.4, columnspacing=1.2, labelspacing=.5)
H2 = [Line2D([], [], ls="", marker="o", ms=6, mfc=c, mec="none", label=l) for c, l in zip(HTC, HT_LABELS)]
fig.text(.045, .447, "water height:", fontsize=10, color=FG, va="center")
fig.legend(handles=H2, loc="center left", bbox_to_anchor=(.15, .447), ncol=6, frameon=False, prop=LP, handletextpad=.1, columnspacing=.9)

# ---- numbers row
nums = [(f"{s['n']:,}", NAVY, f"definite and probable\ntsunamis since {s['first_name']}"),
        (f"{C['Earthquake']['pct']:.0f}%", GCOLS[0], "started with an\nearthquake alone"),
        (f"{F['lituya']['max_run']:.0f} m", "#5B3F86", "highest runup: Lituya\nBay, Alaska, 1958"),
        (f"{R['speed']['median_kmh']}", "#2763A6", "km/h: median speed of\nwaves crossing oceans")]
for i, (big, col, sm) in enumerate(nums):
    xx = .045 + i * .235
    fig.text(xx, .418, big, fontproperties=DISP, fontsize=34, color=col, va="top")
    fig.text(xx, .376, sm, family=MONO, fontsize=10.5, color=FG, va="top", linespacing=1.25)

# ---- panels: deadliest and highest
short = lambda p: p.replace("Off W. Coast of Sumatra", "Off Sumatra").replace(", AK", "").replace(" West, WA", "").replace(", Kyushu Island", "").replace(" Island", "")
for x0, rows, val, col, fmtv, title in ((.045, R["deadliest"][:8], "deaths", DEAD, lambda v: f"{v:,.0f}", "The deadliest: tsunami deaths"),
                                        (.535, R["highest"][:8], "ht", None, lambda v: f"{v:.0f} m", "The highest water: runup, metres")):
    a = fig.add_axes([x0 + .19, .185, .21, .125]); a.set_facecolor(BGc)
    v = [r[val] for r in rows][::-1]
    a.barh(range(len(v)), v, color=[col or GCOLS[GN.index(r["group"])] for r in rows][::-1], height=.68)
    for k, vv in enumerate(v): a.text(vv + max(v) * .03, k, fmtv(vv), va="center", fontsize=9)
    a.set_yticks(range(len(v))); a.set_yticklabels([f"{short(r['place'])} {r['yname']}" for r in rows][::-1], fontsize=9); a.tick_params(axis="y", length=0)
    a.set_xticks([]); a.set_xlim(0, max(v) * 1.32); spines(a); a.spines["bottom"].set_visible(False)
    fig.text(x0, .322, title, family=MONO, fontsize=12, color=FG, va="bottom")

# ---- strip: per century
Cn = [c for c in R["centuries"] if c["c"] >= 1000]
a = fig.add_axes([.075, .092, .875, .055]); a.set_facecolor(BGc)
base = np.zeros(len(Cn)); xs = np.arange(len(Cn))
for g, col in GROUPS:
    vv = np.array([c[g] for c in Cn]); a.bar(xs, vv, bottom=base, color=col, width=.78); base += vv
for x, c in zip(xs, Cn): a.text(x, c["n"] + 15, str(c["n"]), ha="center", fontsize=9)
a.set_xticks(xs); a.set_xticklabels([f"{c['c']}s" for c in Cn], fontsize=9); spines(a); a.set_yticks([]); a.spines["left"].set_visible(False); a.set_ylim(0, 820)
fig.text(.045, .158, "Tsunamis recorded per century: more people and instruments watching, not more tsunamis", family=MONO, fontsize=12, color=FG, va="bottom")

fig.text(.045, .006, f"Source: NOAA NCEI/WDS Global Historical Tsunami Database (doi:10.7289/V5PN93H7, public domain), {s['fetched']}. Plates: Bird (2003) PB2002.\n"
         "Outlines: Natural Earth. Tsunamis = NCEI validity definite or probable. 2000s partial.\n"
         "Deaths = deaths caused by the tsunami (not the earthquake); old figures are estimates.\n"
         "Analysis and chart: Tristan Hotham, with Python and matplotlib  ·  maps.tristanhotham.com/tsunamis", family=MONO, fontsize=8.4, color=MUT, linespacing=1.5, va="bottom")
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "every_tsunami_on_record.png")
fig.savefig(out, facecolor=BGc, dpi=200)
print("ok", out)
