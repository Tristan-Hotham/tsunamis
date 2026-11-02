"""Header card, blog figures (release/blog/b_*.png, 1800 px wide) and paper figures (release/paper/f_*.png).
Numbers from data/results.json; points from data/site.json and data/runups.json. Needs only data/."""
import matplotlib.patheffects as pe
from matplotlib.patches import Patch, Circle
from matplotlib.lines import Line2D
from figstyle import *

R = jload(f"{DATA}/results.json")
BL = os.path.join(ROOT, "release", "blog"); PA = os.path.join(ROOT, "release", "paper")
os.makedirs(BL, exist_ok=True); os.makedirs(PA, exist_ok=True)
HALO = [pe.withStroke(linewidth=3.5, foreground=SEA)]
HALOP = [pe.withStroke(linewidth=3.5, foreground=BG)]
EV = events(); RU, RC = runups()
GCOLS = [c for _, c in GROUPS]


def both(fig, name, blog=True):
    """Paper at 200 dpi; blog at exactly 1800 px wide."""
    fig.savefig(os.path.join(PA, "f_" + name + ".png"), dpi=200, facecolor=fig.get_facecolor())
    if blog:
        fig.savefig(os.path.join(BL, "b_" + name + ".png"), dpi=1800 / fig.get_figwidth(), facecolor=fig.get_facecolor())
    plt.close(fig)


def rad(d, k=1.0):     # marker area (points^2) for deaths
    return k * (6 + 0.035 * d) if d else 5 * k


# ---------- world map: sources and places ----------
def sources_map(ax, k=1.0, dots=True, dot_s=1.6, lw=.35):
    outline(ax, fc=SEA, ec="#C9CDD0"); world(ax, ec=BG, lw=lw); plates(ax)
    if dots:
        a = np.array([[r["lon"], r["lat"], r["ht"] if r["ht"] is not None else np.nan] for r in RU])
        o = np.argsort(np.nan_to_num(a[:, 2], nan=-1)); a = a[o]
        x, y = proj(a[:, 0], a[:, 1]); ax.scatter(x, y, s=dot_s, c=[hcol(h) for h in a[:, 2]], lw=0, alpha=.7, zorder=3)
    E = sorted([e for e in EV if e["lat"] is not None], key=lambda e: -(e["deaths"] or 0))
    x, y = proj([e["lon"] for e in E], [e["lat"] for e in E])
    ax.scatter(x, y, s=[rad(e["deaths"] or 0, k) for e in E], c=[GCOLS[e["g"]] for e in E], alpha=.82, ec="#fff", lw=.45 * k ** .5, zorder=4)


fig = plt.figure(figsize=(12, 7.1), facecolor=BG); ax = fig.add_axes([0, .08, 1, .82])
sources_map(ax)
F = R["famous"]
LAB = {"sumatra": (-1.2e6, -1.6e6, "right", "Indian Ocean 2004"), "lisbon": (-1.0e6, -9e5, "right", "Lisbon 1755"), "krakatau": (3e5, -1.7e6, "center", "Krakatau 1883"),
       "tohoku": (1.8e6, -1.3e6, "left", "Tohoku 2011"), "chile": (-1.2e6, -1.0e6, "right", "Chile 1960"), "lituya": (5e5, -3.3e6, "left", "Lituya Bay 1958"),
       "tonga": (1.0e6, -6e5, "left", "Hunga Tonga 2022"), "sanriku": (2.4e6, 4e5, "left", "Sanriku 1896")}
for kf, (dx, dy, ha, t) in LAB.items():
    f = F[kf]; x, y = proj(f["lon"], f["lat"])
    ax.annotate(t, (x, y), (x + dx, y + dy), ha=ha, va="center", fontsize=9.5, color=FG, path_effects=HALO, zorder=7,
                arrowprops=dict(arrowstyle="-", color=FG, lw=.6, shrinkA=2, shrinkB=4))
fig.text(.02, .975, f"{R['source']['n']:,} tsunamis, {R['source']['first_name']} to {R['source']['last_year']}. Large circles: sources, area = tsunami deaths, colour = cause.\nSmall dots: the {R['page']['runups']:,} places with a position where the water was recorded, colour = height.", fontsize=10.5, color=FG, va="top", linespacing=1.4)
H = [Patch(color=c, label=g) for g, c in GROUPS] + [Line2D([], [], ls=(0, (3, 2)), color=PLATE, label="plate boundary")]
fig.legend(handles=H, loc="lower left", ncol=4, frameon=False, fontsize=9, bbox_to_anchor=(.02, .0))
H2 = [Line2D([], [], ls="", marker="o", ms=5, mfc=c, mec="none", label=l) for c, l in zip(HTC, HT_LABELS)]
fig.legend(handles=H2, loc="lower right", ncol=3, frameon=False, fontsize=9, bbox_to_anchor=(.99, .0), title="water height", title_fontsize=9)
both(fig, "map")

# ---------- lines: 1960 and 2004 ----------
fig, axs = plt.subplots(2, 1, figsize=(12, 12.6), facecolor=BG); fig.subplots_adjust(left=0, right=1, top=.95, bottom=.03, hspace=.1)
EI = {e["id"]: i for i, e in enumerate(EV)}
for ax, kf, t in ((axs[0], "chile", "Chile, 22 May 1960"), (axs[1], "sumatra", "Indian Ocean, 26 December 2004")):
    outline(ax, fc=SEA, ec="#C9CDD0"); world(ax, ec=BG); f = F[kf]; i = EI[f["id"]]
    rs = sorted([r for r in RU if r["e"] == i], key=lambda r: r["ht"] if r["ht"] is not None else -1)
    for r in rs:
        x, y = join(f["lon"], f["lat"], r["lon"], r["lat"]); ax.plot(x, y, color=hcol(r["ht"]), lw=.45, alpha=.45, zorder=3)
    x, y = proj([r["lon"] for r in rs], [r["lat"] for r in rs]); ax.scatter(x, y, s=7, c=[hcol(r["ht"]) for r in rs], ec="#fff", lw=.2, zorder=4)
    x, y = proj(f["lon"], f["lat"]); ax.scatter([x], [y], s=110, c=GCOLS[0], ec=FG, lw=1.4, zorder=5)
    ax.set_title(f"{t}: {f['runups']:,} places in {f['countries']} countries, magnitude {f['mag']}, {f['deaths']:,} tsunami deaths", fontsize=11.5, color=FG, loc="left", x=.02)
fig.legend(handles=H2, loc="lower center", ncol=6, frameon=False, fontsize=9.5, bbox_to_anchor=(.5, -.005), title="water height (lines are straight joins, not the wave's path)", title_fontsize=9.5)
both(fig, "lines")

# ---------- causes and oceans ----------
fig, axs = plt.subplots(2, 2, figsize=(11, 7.4), facecolor=BG, gridspec_kw={"height_ratios": [7, 6]}); fig.subplots_adjust(left=.22, right=.96, top=.92, bottom=.04, wspace=.15, hspace=.32)
OCOL = {"Pacific": NAVY, "Indian Ocean": "#3D8BC4", "Atlantic and Caribbean": "#2E9A8C", "Mediterranean": "#D9822B", "Black Sea and Caspian": "#7B57A8", "Red Sea and Persian Gulf": "#A79F94"}
for row, rows, key, cols in ((0, R["causes_list"], "group", GCOLS), (1, [o for o in R["oceans_list"] if o["n"] > 1], "ocean", None)):
    for c, (fld, t) in enumerate((("pct", "share of tsunamis"), ("deaths_pct", "share of tsunami deaths"))):
        ax = axs[row, c]; ax.set_facecolor(BG); nm = [r[key] for r in rows][::-1]; v = [r[fld] for r in rows][::-1]
        col = (cols[::-1] if cols else [OCOL[n] for n in nm])
        ax.barh(range(len(nm)), v, color=col, height=.66)
        for k, vv in enumerate(v): ax.text(vv + 1.2, k, (f"{vv:.0f}%" if vv >= 9.5 else f"{vv:.1f}%"), va="center", fontsize=9.5)
        ax.set_yticks(range(len(nm))); ax.set_yticklabels(nm if c == 0 else [], fontsize=10); ax.set_xlim(0, 100); ax.set_xticks([]); spines(ax); ax.spines["bottom"].set_visible(False); ax.tick_params(axis="y", length=0)
        ax.set_title(("By cause: " if row == 0 else "By ocean: ") + t, loc="left", fontsize=11, color=FG)
both(fig, "causes")

# ---------- centuries ----------
C = [c for c in R["centuries"] if c["c"] >= 1000]
fig = plt.figure(figsize=(11, 5.2), facecolor=BG); ax = fig.add_axes([.07, .12, .91, .72]); ax.set_facecolor(BG)
base = np.zeros(len(C)); xs = np.arange(len(C))
for g, col in GROUPS:
    v = np.array([c[g] for c in C]); ax.bar(xs, v, bottom=base, color=col, width=.78, label=g); base += v
for x, c in zip(xs, C): ax.text(x, c["n"] + 8, f"{c['n']}", ha="center", fontsize=10)
ax.set_xticks(xs); ax.set_xticklabels([f"{c['c']}s" for c in C], fontsize=10); spines(ax); ax.set_ylabel("tsunamis recorded"); ax.grid(axis="y", color=RULE); ax.set_axisbelow(True)
ax.text(len(C) - 1, R["cent"]["c2000"] + 60, f"{R['source']['last_year']}\nso far", ha="center", fontsize=9, color=MUT)
fig.legend(handles=[Patch(color=c, label=g) for g, c in GROUPS], loc="upper left", ncol=4, frameon=False, fontsize=9.5, bbox_to_anchor=(.06, .99))
both(fig, "century")


def hbar(rows, val, lab, col, fmtv, title, name, xlab=None, blog=True):
    fig = plt.figure(figsize=(11, .44 * len(rows) + 1.1), facecolor=BG); ax = fig.add_axes([.33, .04, .58, 1 - 1.0 / (.44 * len(rows) + 1.1)]); ax.set_facecolor(BG)
    v = [val(r) for r in rows][::-1]; ax.barh(range(len(rows)), v, color=[col(r) for r in rows][::-1], height=.68)
    for k, vv in enumerate(v): ax.text(vv + max(v) * .012, k, fmtv(vv), va="center", fontsize=10)
    ax.set_yticks(range(len(rows))); ax.set_yticklabels([lab(r) for r in rows][::-1], fontsize=10); ax.tick_params(axis="y", length=0); ax.set_xticks([]); spines(ax); ax.spines["bottom"].set_visible(False)
    ax.set_xlim(0, max(v) * 1.13)
    if title: fig.text(.02, 1 - .45 / (.44 * len(rows) + 1.1), title, fontsize=11, color=FG, va="center")
    return fig


short = lambda s: s.replace("Off W. Coast of Sumatra", "Off Sumatra").replace(", AK", "").replace(", WA", "")
fig = hbar(R["deadliest"][:12], lambda r: r["deaths"], lambda r: f"{short(r['place'])}, {r['yname']}", lambda r: DEAD, lambda v: f"{v:,.0f}", "Deaths caused by the tsunami, as NCEI records them (old figures are estimates)", "deadliest")
both(fig, "deadliest")
fig = hbar(R["highest"][:12], lambda r: r["ht"], lambda r: f"{short(r['place'])}, {r['yname']}", lambda r: GCOLS[GN.index(r["group"])], lambda v: f"{v:,.0f} m" if v >= 100 else f"{v:.0f} m", "Highest runup recorded for each tsunami, metres above sea level; colour: cause", "highest")
ax = fig.axes[0]; ax.legend(handles=[Patch(color=GCOLS[k], label=GN[k]) for k in (1, 2, 3)], loc="lower right", frameon=False, fontsize=9.5)
both(fig, "highest")
fig = hbar(R["countries"][:15], lambda r: r["events"], lambda r: r["country"], lambda r: "#2763A6", lambda v: f"{v:,.0f}", "Number of different tsunamis recorded in each country or territory", "countries")
both(fig, "countries")

# ---------- travel ----------
P = [r for r in RU if r["dist"] and r["trav"] and r["dist"] <= 20000 and r["trav"] <= 36]
fig = plt.figure(figsize=(11, 6.2), facecolor=BG); ax = fig.add_axes([.08, .11, .89, .78]); ax.set_facecolor(BG)
P.sort(key=lambda r: r["ht"] if r["ht"] is not None else -1)
ax.scatter([r["dist"] for r in P], [r["trav"] for r in P], s=7, c=[hcol(r["ht"]) for r in P], lw=0, alpha=.75)
for v, s in ((400, "400 km/h"), (700, "700 km/h")):
    t1 = min(36, 20000 / v); ax.plot([0, t1 * v], [0, t1], color=MUT, ls=(0, (5, 4)), lw=1)
    xl = 11600 if v == 400 else 18300; ax.text(xl + 250, xl / v - 1.2, s, ha="left", va="top", fontsize=10, color=MUT, path_effects=HALOP)
T = R["travel"]
fa0 = R["farthest"][0]; ax.scatter([fa0["dist"]], [fa0["trav"]], s=40, fc="none", ec=FG, lw=1.1, zorder=5); ax.text(fa0["dist"] - 250, fa0["trav"] + .9, f"{fa0['place']}, Galápagos, 2004", ha="right", fontsize=9.5, path_effects=HALOP)
ax.set_xlim(0, 20000); ax.set_ylim(0, 36); spines(ax); ax.grid(color=RULE); ax.set_axisbelow(True)
ax.set_xlabel("km from the source"); ax.set_ylabel("hours to arrive"); ax.set_yticks(range(0, 37, 6))
ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, p: f"{v:,.0f}"))
fig.text(.02, .95, f"{len(P):,} places with a recorded travel time; median speed beyond 1,000 km: {R['speed']['median_kmh']} km/h", fontsize=11, color=FG)
fig.legend(handles=H2, loc="upper right", ncol=6, frameon=False, fontsize=8.6, bbox_to_anchor=(.99, .935))
both(fig, "travel")

# ---------- header card 1200 x 630 ----------
fig = plt.figure(figsize=(12, 6.3), dpi=100, facecolor=BG)
ax = fig.add_axes([.38, .05, .62, .9]); sources_map(ax, k=.55, dot_s=.6, lw=.2)
fig.text(.04, .86, "Every", fontproperties=DISP, fontsize=54, color=FG, va="top")
fig.text(.04, .70, "tsunami", fontproperties=DISP, fontsize=54, color=NAVY, va="top")
fig.text(.04, .54, "on record", fontproperties=DISP, fontsize=54, color=FG, va="top")
fig.text(.04, .36, f"{R['source']['n']:,} tsunamis since {R['source']['first_name']}\nand the {R['page']['runups']:,} places their water reached.\nThe highest ran {R['famous']['lituya']['max_run']:.0f} m up a mountainside.", fontproperties=SERP, fontsize=14, color=FG, va="top", linespacing=1.35)
fig.text(.04, .05, "maps.tristanhotham.com/tsunamis", fontsize=11, color=MUT)
fig.savefig(os.path.join(ROOT, "header.png"), dpi=100, facecolor=BG)
plt.close(fig)
print("figures done", sorted(os.listdir(BL)), sorted(x for x in os.listdir(PA) if x.endswith(".png")))
