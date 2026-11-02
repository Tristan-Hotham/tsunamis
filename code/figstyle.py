"""House style for static figures: fonts (static instances cut from the variable Fraunces in /home/claude/ref/fonts,
written to WORK), the palette, and Natural Earth outlines in a Pacific-centred Equal Earth projection (central
meridian 150 E, so the seam runs down the Atlantic at 30 W). Reads only data/."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Polygon as MPoly
import numpy as np
from pyproj import Transformer
from shapely.geometry import shape, box
from common import *

FD = os.path.join(WORK, "fonts"); os.makedirs(FD, exist_ok=True)
if not os.path.exists(f"{FD}/Fraunces-Black.ttf"):
    from fontTools.ttLib import TTFont
    from fontTools.varLib import instancer
    for w, nm in ((900, "Black"), (700, "Bold")):
        instancer.instantiateVariableFont(TTFont(f"{FONTS}/FrauncesVar.ttf"), {"wght": w, "opsz": 144, "SOFT": 0, "WONK": 0}).save(f"{FD}/Fraunces-{nm}.ttf")
DISP = fm.FontProperties(fname=f"{FD}/Fraunces-Black.ttf")
DISPB = fm.FontProperties(fname=f"{FD}/Fraunces-Bold.ttf")
SERP = fm.FontProperties(fname=f"{FONTS}/SourceSerif4-Regular.ttf")
SERB = fm.FontProperties(fname=f"{FONTS}/SourceSerif4-Semibold.ttf")
SERI = fm.FontProperties(fname=f"{FONTS}/SourceSerif4-It.ttf")
for f in ("IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf"):
    fm.fontManager.addfont(f"{FONTS}/{f}")
MONO = "IBM Plex Mono"
plt.rcParams.update({"font.family": MONO, "font.size": 12, "axes.edgecolor": "#636A72", "axes.labelcolor": "#1D2128",
                     "xtick.color": "#636A72", "ytick.color": "#636A72"})
BG, FG, MUT, LAND, RULE, SEA = "#F6F4EF", "#1D2128", "#636A72", "#E2DED3", "#DDD8CC", "#E8EEF1"
HOT, NAVY, DEAD, PLATE = "#C8322B", "#173F80", "#7A2A2A", "#B0504A"
HTC = [c for _, c in HT_BINS]

LON0 = 150
EE = Transformer.from_crs(4326, f"+proj=eqearth +lon_0={LON0} +datum=WGS84 +units=m", always_xy=True)
SEAM = LON0 - 180   # -30


def wrap(lon):
    """Longitude shifted into (SEAM, SEAM + 360) so nothing crosses the seam."""
    return (np.asarray(lon, float) - SEAM) % 360 + SEAM


def proj(lon, lat):
    lo = wrap(lon); lo = np.where(lo > 180, lo - 360, lo)
    return EE.transform(lo, np.asarray(lat, float))


W = jload(f"{DATA}/world.json")
SHAPES = []      # (iso, projected Nx2 array)
for f in W["features"]:
    g = shape(f["geometry"]).buffer(0)
    for half in (box(-180, -90, SEAM - 1e-3, 90), box(SEAM + 1e-3, -90, 180, 90)):
        q = g.intersection(half)
        if q.is_empty: continue
        for poly in (q.geoms if hasattr(q, "geoms") else [q]):
            if poly.geom_type != "Polygon": continue
            xy = np.array(poly.exterior.coords)
            x, y = EE.transform(xy[:, 0], np.clip(xy[:, 1], -89.5, 89.5))
            SHAPES.append((f["properties"]["iso"], np.column_stack([x, y])))
WORLD_EXT = (-17.0e6, 17.0e6, -8.75e6, 8.7e6)


def world(ax, lw=.3, ext=WORLD_EXT, ec="#FFFFFF", land=LAND, z=1, skip_ata=False):
    for iso, p in SHAPES:
        if skip_ata and iso == "ATA":
            continue
        ax.add_patch(MPoly(p, closed=True, fc=land, ec=ec, lw=lw, zorder=z))
    ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3]); ax.set_aspect("equal"); ax.axis("off")


def outline(ax, fc=None, lw=.8, ec=MUT, z=0):
    lat = np.linspace(-90, 90, 181)
    xl, yl = EE.transform(np.full_like(lat, SEAM + 1e-6), lat); xr, yr = EE.transform(np.full_like(lat, SEAM - 1e-6), lat[::-1])
    ax.add_patch(MPoly(np.column_stack([np.r_[xl, xr], np.r_[yl, yr]]), closed=True, fc=fc or "none", ec=ec, lw=lw, zorder=z))


def plates(ax, lw=.7, alpha=.5, z=1.5, col=PLATE):
    P = jload(f"{DATA}/plates.json")["geometry"]["coordinates"]
    for line in P:
        a = np.array(line); lo = wrap(a[:, 0])
        cut = np.where(np.abs(np.diff(lo)) > 180)[0] + 1      # split where a line crosses the seam
        for seg in np.split(np.column_stack([lo, a[:, 1]]), cut):
            if len(seg) < 2: continue
            x, y = EE.transform(np.where(seg[:, 0] > 180, seg[:, 0] - 360, seg[:, 0]), seg[:, 1])
            ax.plot(x, y, color=col, lw=lw, alpha=alpha, ls=(0, (3, 2)), zorder=z)


def join(lon0, lat0, lon1, lat1, n=24):
    """Projected points along a straight lon/lat join, the far end unwrapped next to the source."""
    l0 = float(wrap(lon0)); l1 = float(wrap(lon1))
    lo = np.linspace(l0, l1, n); la = np.linspace(lat0, lat1, n)
    return EE.transform(np.where(lo > 180, lo - 360, lo), la)


def spines(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


def hcol(h):
    if h is None or h != h: return "#9AA0A6"
    for ub, c in HT_BINS:
        if h < ub: return c
    return HT_BINS[-1][1]


def events():
    S = jload(f"{DATA}/site.json")
    return [dict(zip(S["cols"], r)) for r in S["rows"]]


def runups():
    U = jload(f"{DATA}/runups.json")
    return [dict(zip(U["cols"], r)) for r in U["rows"]], U["countries"]
