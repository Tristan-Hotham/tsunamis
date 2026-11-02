"""Geography: a light world outline file for the page and figures (Natural Earth 1:50m), country label positions and
names, city names for map labels, ocean label positions, and the plate boundaries (PB2002, simplified) for the page and
figures. Also: the distance from each source event to the nearest plate boundary (used for one statement in the text)."""
import numpy as np
from shapely.geometry import shape, mapping, LineString, MultiLineString, Point
from shapely.strtree import STRtree
import pandas as pd
from common import *

iso_of = lambda p: p["ISO_A3_EH"] if p.get("ISO_A3_EH") not in ("-99", None) else p["ADM0_A3"]
FIX = {"CNM": "CYP", "ESB": "CYP", "WSB": "CYP", "PSX": "PSE", "SAH": "ESH", "KAS": "IND", "SOL": "SOM"}


def rnd(c, k=2):
    if isinstance(c, (list, tuple)) and c and isinstance(c[0], (int, float)):
        return [round(c[0], k), round(c[1], k)]
    return [rnd(x, k) for x in c]


W50 = jload(f"{GEO}/ne_50m_admin_0_countries.geojson")
feats, meta = [], {}
for f in W50["features"]:
    p = f["properties"]; iso = FIX.get(iso_of(p), iso_of(p))
    gs = shape(f["geometry"]).simplify(0.04, preserve_topology=True)
    if gs.is_empty:
        continue
    gm = mapping(gs)
    feats.append({"type": "Feature", "properties": {"iso": iso}, "geometry": {"type": gm["type"], "coordinates": rnd(gm["coordinates"])}})
    if iso not in meta:
        nm = (p.get("NAME_EN") or p["NAME"]).replace("People's Republic of China", "China").replace("United States of America", "United States")
        meta[iso] = {"name": nm, "lx": round(p["LABEL_X"], 2), "ly": round(p["LABEL_Y"], 2), "pop": float(p.get("POP_EST") or 0)}
meta.get("CYP", {}).update(name="Cyprus")
jsave({"type": "FeatureCollection", "features": feats}, f"{DATA}/world.json")
jsave(meta, f"{DATA}/countries.json")

P = jload(f"{GEO}/ne_10m_populated_places_simple.geojson")
cities = []
for f in P["features"]:
    p = f["properties"]; pop = p.get("pop_max") or 0
    if pop >= 300000 or p.get("adm0cap") == 1:
        cities.append({"name": re.sub(r"\s+", " ", p["name"]), "lat": round(p["latitude"], 3), "lon": round(p["longitude"], 3), "pop": int(pop)})
cities.sort(key=lambda c: -c["pop"])
jsave(cities, f"{DATA}/cities.json")

# ocean and sea labels (my positions, on open water)
OL = [("PACIFIC OCEAN", -150, 25, 1), ("PACIFIC OCEAN", -125, -28, 1), ("ATLANTIC OCEAN", -40, 30, 1), ("ATLANTIC OCEAN", -15, -25, 1), ("INDIAN OCEAN", 78, -18, 1),
      ("SOUTHERN OCEAN", 60, -58, 1), ("Mediterranean Sea", 17, 35, 2), ("Caribbean Sea", -76, 15, 2), ("Bering Sea", -178, 58, 2),
      ("South China Sea", 114, 14, 2), ("Philippine Sea", 133, 20, 2), ("Coral Sea", 155, -16, 2), ("Tasman Sea", 161, -38, 2), ("Bay of Bengal", 89, 15, 2),
      ("Arabian Sea", 64, 15, 2), ("Gulf of Alaska", -145, 55.5, 2), ("Sea of Japan", 134.5, 40.5, 2), ("Black Sea", 34.5, 43.3, 2), ("Banda Sea", 127, -5.6, 2)]
jsave([{"name": n, "lon": lo, "lat": la, "rank": r} for n, lo, la, r in OL], f"{DATA}/oceans.json")

# plate boundaries, simplified for the page (about 0.1 degree)
PB = jload(f"{RAW}/PB2002_boundaries.json")
pl, lines = [], []
for f in PB["features"]:
    g = shape(f["geometry"]); lines.append(g)
    gs = g.simplify(0.08)
    cs = [gs] if gs.geom_type == "LineString" else list(gs.geoms)
    for c in cs:
        xy = rnd([list(t) for t in c.coords])
        if len(xy) >= 2: pl.append(xy)
jsave({"type": "Feature", "properties": {}, "geometry": {"type": "MultiLineString", "coordinates": pl}}, f"{DATA}/plates.json")

# distance from each source event to the nearest plate boundary (km, on a sphere, via dense sampling of the lines)
pts = []
for g in lines:
    cs = [g] if g.geom_type == "LineString" else list(g.geoms)
    for c in cs:
        L = np.array(c.coords); seg = np.hypot(*np.diff(L, axis=0).T)
        for (a, b), s in zip(zip(L[:-1], L[1:]), seg):
            k = max(1, int(np.ceil(s / 0.1)))
            for t in np.linspace(0, 1, k, endpoint=False): pts.append(a + (b - a) * t)
        pts.append(L[-1])
pts = np.radians(np.array(pts)); X = np.column_stack([np.cos(pts[:, 1]) * np.cos(pts[:, 0]), np.cos(pts[:, 1]) * np.sin(pts[:, 0]), np.sin(pts[:, 1])])
from scipy.spatial import cKDTree
T = cKDTree(X)
E = pd.read_pickle(f"{WORK}/events.pkl")
m = E.latitude.notna() & E.longitude.notna()
la, lo = np.radians(E.loc[m, "latitude"].values), np.radians(E.loc[m, "longitude"].values)
Q = np.column_stack([np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)])
d, _ = T.query(Q)
E["plate_km"] = np.nan
E.loc[m, "plate_km"] = 6371.0 * 2 * np.arcsin(np.clip(d / 2, 0, 1))
E.to_pickle(f"{WORK}/events.pkl")
print("countries", len(meta), "cities", len(cities), "plates", len(pl), "lines;", "world", os.path.getsize(f"{DATA}/world.json") // 1024, "KB;",
      "plates", os.path.getsize(f"{DATA}/plates.json") // 1024, "KB; median km to plate", round(float(np.nanmedian(E.plate_km)), 1))
