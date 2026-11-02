"""Every number used anywhere (data/results.json), the reusable data tables (data/*.csv) and the page data
(data/site.json embedded in the page, data/runups.json loaded by it).

Definitions (see 01_clean.py for codes):
  * a tsunami: a source event with eventValidity 3 (probable) or 4 (definite);
  * a runup: a place where NCEI records the water, for a tsunami, not flagged as doubtful; deep-ocean gauges left out of
    places, countries and distances;
  * deaths: NCEI's 'deaths' field (people killed by the tsunami); 'deathsTotal' includes the earthquake or eruption;
  * century: floor(year / 100), so 1900 to 1999 is the 1900s; years BC are negative;
  * travel time: NCEI's travHours and travMins; speed = distFromSource / travel time, for runups more than 1,000 km away;
  * Pacific: NCEI regions 80 to 89; Ring of Fire: regions 81 to 89 (the rim of the Pacific, without Hawaii)."""
import numpy as np, pandas as pd
from common import *

E = pd.read_pickle(f"{WORK}/events.pkl")
U = pd.read_pickle(f"{WORK}/runups.pkl")
CHK = jload(f"{WORK}/checks.json")
pc = lambda a, b: round(100 * float(a) / float(b), 2) if b else None
nz = lambda v: None if v is None or (isinstance(v, float) and np.isnan(v)) else (int(v) if float(v).is_integer() else round(float(v), 2))
D = E[E.valid == 1].copy()
UK = U[(U.ok == 1)].copy()                 # kept runups (valid source, not doubtful)
UC = UK[UK.deep == 0].copy()               # coastal and tide-gauge places
R = {}

# ---------- source ----------
R["source"] = {"events": CHK["events"], "runups": CHK["runups"], "n": len(D), "definite": int((D.eventValidity == 4).sum()), "probable": int((D.eventValidity == 3).sum()),
               "other": int(len(E) - len(D)), "validity": CHK["validity"], "first_year": int(D.year.min()), "last_year": LAST_YEAR,
               "first_name": yname(D.year.min()), "fetched": FETCHED, "ncei_doi": NCEI_DOI, "runups_kept": len(UK), "runups_coast": len(UC),
               "runups_deep": int(UK.deep.sum()), "runups_doubtful": int((U.ev.isin([3, 4]) & (U.doubtful != "n")).sum()),
               "runups_other_src": int((~U.ev.isin([3, 4])).sum()), "runups_coast_located": int(UC.latitude.notna().sum()),
               "no_coords": int(D.latitude.isna().sum()), "located": int(D.latitude.notna().sum()),
               "with_runups": int(D.id.isin(UK.tsunamiEventId).sum()), "checks": CHK}
s = R["source"]
assert s["n"] == 1699 and s["definite"] == 1110 and s["probable"] == 589 and s["first_year"] == -1610
s["definite_pct"] = pc(s["definite"], s["n"]); s["n_pct_all"] = pc(s["n"], s["events"])
s["y2026"] = int((D.year == 2026).sum()); s["last_month"] = int(D[D.year == 2026].month.max())

# ---------- causes ----------
cz = []
for g in GN:
    a = D[D.group == g]
    cz.append({"group": g, "n": len(a), "pct": pc(len(a), len(D)), "deaths": int(a.deaths.fillna(0).sum()), "deaths_pct": pc(a.deaths.fillna(0).sum(), D.deaths.fillna(0).sum()),
               "codes": {CAUSE[int(c)]: int(n) for c, n in a.cause.value_counts().items()}, "max_ht": nz(a.maxWaterHeight.max())})
R["causes"] = {c["group"]: c for c in cz}; R["causes_list"] = cz
C_ = R["causes"]
R["cause_codes"] = {CAUSE[int(c)]: int(n) for c, n in D.cause.value_counts().sort_index().items()}
R["eq_any_pct"] = pc(C_["Earthquake"]["n"] + C_["Earthquake and landslide"]["n"], len(D))
R["eq_any_n"] = C_["Earthquake"]["n"] + C_["Earthquake and landslide"]["n"]
eqm = D[D.group.isin(["Earthquake", "Earthquake and landslide"]) & D.eqMagnitude.notna()]
R["mag"] = {"n": len(eqm), "median": round(float(eqm.eqMagnitude.median()), 1), "ge7_pct": pc((eqm.eqMagnitude >= 7).sum(), len(eqm)),
            "ge8": int((eqm.eqMagnitude >= 8).sum()), "ge9": int((eqm.eqMagnitude >= 9).sum()), "min": round(float(eqm.eqMagnitude.min()), 1),
            "ge9_list": [f"{yname(r.year)} {r.place}" for r in eqm[eqm.eqMagnitude >= 9].sort_values("year").itertuples()]}
assert R["mag"]["ge9"] == 7, R["mag"]["ge9_list"]  # 1700 Cascadia, 1730 and 1960 Chile, 1952 Kamchatka, 1964 Alaska, 2004 Sumatra, 2011 Tohoku
pl = D[D.plate_km.notna() & D.group.isin(["Earthquake", "Earthquake and landslide"])]
R["plates"] = {"n": len(pl), "within100_pct": pc((pl.plate_km <= 100).sum(), len(pl)), "within250_pct": pc((pl.plate_km <= 250).sum(), len(pl)),
               "median_km": round(float(pl.plate_km.median()))}

# ---------- oceans ----------
oc = []
tot_d = D.deaths.fillna(0).sum()
for o, _ in OCEANS:
    a = D[D.ocean == o]
    oc.append({"ocean": o, "n": len(a), "pct": pc(len(a), len(D)), "deaths": int(a.deaths.fillna(0).sum()), "deaths_pct": pc(a.deaths.fillna(0).sum(), tot_d),
               "runups": int(UC.tsunamiEventId.isin(a.id).sum())})
R["oceans"] = {o["ocean"]: o for o in oc}; R["oceans_list"] = oc
R["ocean_unknown"] = int((D.ocean == "Unknown").sum())
assert sum(o["n"] for o in oc) + R["ocean_unknown"] == len(D) and R["ocean_unknown"] <= 1   # one event (1909, Utah) has no NCEI region
ring = D[D.ring == 1]
R["ring"] = {"n": len(ring), "pct": pc(len(ring), len(D)), "deaths": int(ring.deaths.fillna(0).sum()), "deaths_pct": pc(ring.deaths.fillna(0).sum(), tot_d),
             "runups_pct": pc(UC.tsunamiEventId.isin(ring.id).sum(), len(UC)), "japan": int((D.regionCode == 85).sum()), "japan_pct": pc((D.regionCode == 85).sum(), len(D)),
             "sunda": int(((D.regionCode == 60) & (D.country == "INDONESIA")).sum())}
R["ring"]["with_sunda_pct"] = pc(R["ring"]["n"] + R["ring"]["sunda"], len(D))
reg = D.regionCode.value_counts()
R["regions"] = [{"code": int(k), "name": REGION.get(int(k), str(k)), "n": int(v), "pct": pc(v, len(D))} for k, v in reg.items()]

# ---------- deaths ----------
dd = D[D.deaths.notna() & (D.deaths > 0)].sort_values("deaths", ascending=False)
def evrow(r):
    return {"id": int(r.id), "year": int(r.year), "yname": yname(r.year), "place": r.place, "country": r.cname, "group": r.group, "cause": CAUSE[int(r.cause)],
            "deaths": nz(r.deaths), "deaths_total": nz(r.deathsTotal), "mag": nz(r.eqMagnitude), "max_ht": nz(r.maxWaterHeight), "ocean": r.ocean}
R["deadliest"] = [evrow(r) for r in dd.head(15).itertuples()]
R["deaths"] = {"total": int(D.deaths.fillna(0).sum()), "n_events": len(dd), "n_events_pct": pc(len(dd), len(D)), "y2004": int(dd.iloc[0].deaths),
               "y2004_pct": pc(dd.iloc[0].deaths, D.deaths.fillna(0).sum()), "top10_pct": pc(dd.head(10).deaths.sum(), D.deaths.fillna(0).sum()),
               "since1900": int(D[D.year >= 1900].deaths.fillna(0).sum()), "since2000": int(D[D.year >= 2000].deaths.fillna(0).sum()),
               "over1000": int((dd.deaths >= 1000).sum()), "over10000": int((dd.deaths >= 10000).sum()),
               "only_order": int(((D.deaths.isna()) & D.deathsAmountOrder.notna()).sum()),
               "total_only": int((D.deaths.isna() & D.deathsTotal.notna()).sum())}
R["deaths"]["since1900_pct"] = pc(R["deaths"]["since1900"], R["deaths"]["total"]); R["deaths"]["since2000_pct"] = pc(R["deaths"]["since2000"], R["deaths"]["total"])
dl = R["deadliest"]
assert dl[0]["year"] == 2004 and dl[1]["year"] == 1755 and dl[2]["year"] == 1883 and dl[3]["year"] == 1896 and dl[5]["year"] == 2011, [(d["year"], d["deaths"]) for d in dl[:6]]
tt = D[D.deathsTotal.notna()].sort_values("deathsTotal", ascending=False)
R["deadliest_total"] = [evrow(r) for r in tt.head(10).itertuples()]
dt = R["deadliest_total"]
assert dt[0]["year"] == 2010 and dt[0]["country"] == "Haiti" and dt[0]["deaths"] <= 10 and dt[2]["year"] == 1923
R["haiti"] = dt[0]; R["kanto"] = dt[2]
R["deaths"]["sum_total_field"] = int(D.deathsTotal.fillna(0).sum())

# ---------- heights ----------
hr = UC[UC.ht.notna()]
mx = hr.loc[hr.groupby("tsunamiEventId").ht.idxmax()].sort_values("ht", ascending=False)
ev = D.set_index("id")
def runrow(r):
    e = ev.loc[r.tsunamiEventId]
    return {"id": int(r.tsunamiEventId), "year": int(e.year), "yname": yname(e.year), "event": e.place, "country": e.cname, "group": e.group,
            "place": r.place, "ht": round(float(r.ht), 1), "dist": nz(round(r.dist, 1)) if r.dist == r.dist else None, "deaths": nz(e.deaths)}
R["highest"] = [runrow(r) for r in mx.head(15).itertuples()]
hi = R["highest"]
assert hi[0]["year"] == 1958 and hi[0]["ht"] > 520 and hi[1]["year"] == 2025
R["heights"] = {"n_ht": len(hr), "median": round(float(hr.ht.median()), 2), "ge10_events": int((mx.ht >= 10).sum()), "ge30_events": int((mx.ht >= 30).sum()),
                "ge100_events": int((mx.ht >= 100).sum()), "ge100_landslide": int(sum(1 for r in mx[mx.ht >= 100].itertuples() if ev.loc[r.tsunamiEventId].group in ("Landslide", "Earthquake and landslide", "Volcano"))),
                "eq_max": runrow(mx[mx.tsunamiEventId.map(ev.group) == "Earthquake"].iloc[0]),
                "ge10_runups": int((hr.ht >= 10).sum()), "under1_pct": pc((hr.ht < 1).sum(), len(hr))}
R["heights"]["top_landslide_share"] = sum(1 for h in hi[:10] if h["group"] != "Earthquake")

# ---------- distance ----------
dr = UC[(UC.ht > 0) & UC.dist.notna() & (UC.atm == 0)]      # sea waves only: water moved by an eruption's air wave is counted apart below
fx = dr.loc[dr.groupby("tsunamiEventId").dist.idxmax()].sort_values("dist", ascending=False)
R["farthest"] = []
for r in fx.head(12).itertuples():
    row = runrow(r); row["trav"] = round(float(r.trav), 2) if r.trav == r.trav else None; row["rcountry"] = r.cname; R["farthest"].append(row)
fa = R["farthest"]
assert fa[0]["year"] == 2004 and "Baltra" in fa[0]["place"]
R["dist"] = {"over1000_events": int((fx.dist > 1000).sum()), "over10000_events": int((fx.dist > 10000).sum()),
             "over1000_pct": pc((fx.dist > 1000).sum(), D.id.isin(dr.tsunamiEventId).sum()), "events_with": int(D.id.isin(dr.tsunamiEventId).sum()),
             "runups_over1000_pct": pc((dr.dist > 1000).sum(), len(dr)), "median": round(float(dr.dist.median()))}
fa0 = fa[0]; fa0["trav_h"] = int(fa0["trav"]); fa0["trav_m"] = int(round((fa0["trav"] - int(fa0["trav"])) * 60))

atm = UC[UC.atm == 1]
R["atm"] = {"n": len(atm), "tonga": int((atm.tsunamiEventId == 5824).sum()), "krakatau": int((atm.tsunamiEventId == 1142).sum())}
for k, i in (("tonga", 5824), ("krakatau", 1142)):
    a = atm[(atm.tsunamiEventId == i) & atm.dist.notna()]; b = a[a.ht > 0]
    R["atm"][k + "_far_km"] = int(round(b.dist.max(), -1)); R["atm"][k + "_far_place"] = b.loc[b.dist.idxmax()].place; R["atm"][k + "_far_country"] = b.loc[b.dist.idxmax()].cname
    R["atm"][k + "_countries"] = int(a[a.cname != ""].cname.nunique())
    R["atm"][k + "_max_ht"] = round(float(b.ht.max()), 2)
    R["atm"][k + "_max_place"] = b.loc[b.ht.idxmax()].place

# ---------- speed and travel ----------
sp = UC[(UC.dist > 1000) & UC.trav.notna() & (UC.trav > 0) & (UC.atm == 0)].copy()
sp["kmh"] = sp.dist / sp.trav
R["speed"] = {"n": len(sp), "median_kmh": int(round(sp.kmh.median(), -1)), "q25": int(round(sp.kmh.quantile(.25), -1)), "q75": int(round(sp.kmh.quantile(.75), -1))}
# theory for a check: sqrt(g * 4000 m) in km/h
R["speed"]["theory_4km_kmh"] = int(round(np.sqrt(9.81 * 4000) * 3.6, -1))
assert 400 < R["speed"]["median_kmh"] < 800


def arrivals(eid, countries=None, places=None):
    a = UC[(UC.tsunamiEventId == eid)]
    if countries: a = a[a.cname.isin(countries)]
    if places: a = a[a.place.str.contains(places, case=False, regex=True)]
    t = a[a.trav.notna()]
    return {"n": len(a), "deaths": int(a.deaths.fillna(0).sum()), "deaths_max": int(a.deaths.fillna(0).max()) if len(a) else 0, "max_ht": round(float(a.ht.max()), 1) if a.ht.notna().any() else None,
            "first_h": round(float(t.trav.min()), 1) if len(t) else None, "median_h": round(float(t.trav.median()), 1) if len(t) else None,
            "dist": int(round(a.dist.median(), -1)) if a.dist.notna().any() else None, "n_trav": len(t)}


R["travel"] = {"chile_japan": arrivals(1902, ["Japan"]), "chile_hilo": arrivals(1902, places=r"^Hilo"), "chile_nz": arrivals(1902, ["New Zealand"]),
               "chile_ph": arrivals(1902, ["Philippines"]),
               "aleut_hilo": arrivals(1762, places=r"^Hilo"), "tohoku_chile": arrivals(5413, ["Chile"]), "tohoku_us": arrivals(5413, ["United States"]),
               "sum_somalia": arrivals(2439, ["Somalia"]), "sum_kenya": arrivals(2439, ["Kenya"]), "sum_tanzania": arrivals(2439, ["Tanzania"]),
               "sum_safrica": arrivals(2439, ["South Africa"]), "sum_srilanka": arrivals(2439, ["Sri Lanka"]), "sum_india": arrivals(2439, ["India"]),
               "sum_thailand": arrivals(2439, ["Thailand"]), "sum_madagascar": arrivals(2439, ["Madagascar"])}
TR = R["travel"]
# deaths summed over runup places can count the same people twice (town and prefecture entries), so the text never
# quotes them; travel times and heights only
assert 20 < TR["chile_japan"]["first_h"] < 25 and TR["sum_somalia"]["first_h"] is None and TR["sum_somalia"]["max_ht"] > 9
assert TR["sum_kenya"]["first_h"] < TR["sum_tanzania"]["first_h"] < TR["sum_safrica"]["first_h"] and TR["aleut_hilo"]["first_h"] < 6

# ---------- countries hit ----------
cc = UC[UC.cname != ""]
cty = cc.groupby("cname").agg(events=("tsunamiEventId", "nunique"), runups=("id", "size"), deaths=("deaths", "sum"), max_ht=("ht", "max")).sort_values(["events", "runups"], ascending=False)
R["countries"] = [{"country": k, "events": int(r.events), "runups": int(r.runups), "deaths": int(r.deaths), "max_ht": nz(round(r.max_ht, 1))} for k, r in cty.head(20).iterrows()]
R["n_countries"] = int(cc.cname.nunique())
R["countries_runups"] = [{"country": k, "runups": int(v)} for k, v in cc.cname.value_counts().head(10).items()]
assert R["countries"][0]["country"] == "Japan"
jp = UC[UC.tsunamiEventId == 5413]
R["japan"] = {"tohoku_runups": len(jp), "tohoku_pct_all": pc(len(jp), len(UC)), "japan_runups_pct": pc((cc.cname == "Japan").sum(), len(cc))}
R["reach"] = {"max_countries": None}
nc = cc.groupby("tsunamiEventId").cname.nunique().sort_values(ascending=False)
R["reach"] = {"top": [{"id": int(i), "yname": yname(ev.loc[i].year), "event": ev.loc[i].place, "countries": int(n)} for i, n in nc.head(8).items()],
              "ge10": int((nc >= 10).sum())}

# ---------- centuries and decades ----------
D["century"] = (np.floor(D.year / 100) * 100).astype(int)
cen = []
for c in range(int(D.century.min()), 2001, 100):
    a = D[D.century == c]
    row = {"c": c, "label": (f"{-c}s BC" if c < 0 else f"{c}s") if c != 0 else "AD 0s", "n": len(a)}
    for g in GN: row[g] = int((a.group == g).sum())
    cen.append(row)
R["centuries"] = cen
CN = {c["c"]: c["n"] for c in cen}
R["cent"] = {"c1900": CN[1900], "c1800": CN[1800], "c1700": CN[1700], "c1600": CN[1600], "c1500": CN[1500], "c2000": CN[2000],
             "before1500": int((D.year < 1500).sum()), "before0": int((D.year < 0).sum()), "since1900": int((D.year >= 1900).sum()),
             "since1900_pct": pc((D.year >= 1900).sum(), len(D)), "since1800_pct": pc((D.year >= 1800).sum(), len(D)),
             "peak": max((c for c in cen if c["c"] < 2000), key=lambda c: c["n"])["label"]}
assert R["cent"]["peak"] == "1900s"
dec = []
for d0 in range(1900, 2030, 10):
    a = D[(D.year >= d0) & (D.year < d0 + 10)]
    dec.append({"d": d0, "n": len(a), "deaths": int(a.deaths.fillna(0).sum()), "met": int((a.group == "Meteorological").sum()), "eq": int((a.group == "Earthquake").sum())})
R["decades"] = dec
mod = D[(D.year >= 1950) & (D.year <= 2025)]
R["modern"] = {"per_year": round(len(mod) / 76, 1), "n": len(mod), "deadly_per_year": round(int((mod.deaths > 0).sum()) / 76, 1),
               "met_before1950": int(((D.group == "Meteorological") & (D.year < 1950)).sum()), "met_since2000": int(((D.group == "Meteorological") & (D.year >= 2000)).sum())}

# ---------- famous waves ----------
FAM = [("thera", 3, "Thera (Santorini)"), ("lisbon", 456, "Lisbon"), ("cascadia", 361, "Cascadia"), ("krakatau", 1142, "Krakatau"),
       ("sanriku", 1234, "Meiji Sanriku"), ("aleutian", 1762, "Aleutian Islands"), ("lituya", 1880, "Lituya Bay"), ("chile", 1902, "Chile"),
       ("alaska", 1954, "Alaska"), ("sumatra", 2439, "Indian Ocean"), ("tohoku", 5413, "Tohoku"), ("tonga", 5824, "Hunga Tonga")]
fam = {}
for k, i, label in FAM:
    e = ev.loc[i]; a = UC[UC.tsunamiEventId == i]; h = a[a.ht.notna()]; far = a[(a.ht > 0) & a.dist.notna()]
    fam[k] = {"id": i, "label": label, "year": int(e.year), "yname": yname(e.year), "month": nz(e.month), "day": nz(e.day), "place": e.place, "country": e.cname,
              "group": e.group, "cause": CAUSE[int(e.cause)], "validity": int(e.eventValidity), "mag": nz(e.eqMagnitude), "max_ht": nz(e.maxWaterHeight),
              "deaths": nz(e.deaths), "deaths_total": nz(e.deathsTotal), "runups": len(a), "countries": int(a[a.cname != ""].cname.nunique()),
              "max_run": round(float(h.ht.max()), 1) if len(h) else None, "max_run_place": h.loc[h.ht.idxmax()].place if len(h) else None,
              "far_km": int(round(far.dist.max(), -1)) if len(far) else None, "far_place": far.loc[far.dist.idxmax()].place if len(far) else None,
              "far_country": far.loc[far.dist.idxmax()].cname if len(far) else None, "lat": nz(e.latitude), "lon": nz(e.longitude), "ocean": e.ocean}
R["famous"] = fam
F = fam
assert F["thera"]["year"] == -1610 and F["lituya"]["max_run"] > 520 and F["chile"]["mag"] == 9.5 and F["tonga"]["group"] == "Volcano"
assert F["cascadia"]["mag"] == 9.0 and F["cascadia"]["year"] == 1700 and "Japan" in set(UC[UC.tsunamiEventId == 361].cname)
R["famous_order"] = [k for k, _, _ in FAM]
R["cascadia_japan"] = arrivals(361, ["Japan"])
R["tonga_far"] = {"countries": F["tonga"]["countries"], "far_km": F["tonga"]["far_km"]}
cs = UC[UC.tsunamiEventId == 2439]
R["sumatra"] = {"countries": F["sumatra"]["countries"], "runups": len(cs), "deaths_indonesia": int(cs[cs.cname == "Indonesia"].deaths.fillna(0).sum())}
R["highest_n"], R["farthest_n"], R["deadliest_n"] = 12, 10, 12
R["meta"] = {"page": PAGE, "repo": REPO, "doi": DOI, "blog": BLOG, "slug": SLUG, "ncei_doi": NCEI_DOI, "api": API_URL}

# ---------- clean data out ----------
oe = E.copy()
oe["cause_name"] = oe.cause.map(CAUSE); oe["validity_name"] = oe.eventValidity.map(VALIDITY); oe["ncei_region"] = oe.regionCode.map(lambda r: REGION.get(int(r), "") if r == r else "")
oe["year_label"] = oe.year.map(yname)
oe = oe.rename(columns={"id": "ncei_id", "eventValidity": "validity", "causeCode": "cause_code", "group": "cause_group", "valid": "definite_or_probable",
                        "ring": "pacific_rim", "place": "location", "cname": "country_name", "maxWaterHeight": "max_water_height_m", "eqMagnitude": "eq_magnitude",
                        "deaths": "tsunami_deaths", "deathsTotal": "deaths_total_incl_source", "plate_km": "km_to_plate_boundary", "numRunups": "ncei_num_runups"})
cols = ["ncei_id", "year", "month", "day", "year_label", "validity", "validity_name", "definite_or_probable", "cause_code", "cause_name", "cause_group", "country", "country_name",
        "location", "latitude", "longitude", "regionCode", "ncei_region", "ocean", "pacific_rim", "eq_magnitude", "eqDepth", "max_water_height_m", "tsunami_deaths",
        "deaths_total_incl_source", "deathsAmountOrder", "deathsAmountOrderTotal", "injuriesTotal", "missingTotal", "damageMillionsDollarsTotal", "housesDestroyedTotal",
        "ncei_num_runups", "oceanicTsunami", "km_to_plate_boundary", "earthquakeEventId", "volcanoEventId"]
oe[cols].round({"km_to_plate_boundary": 0}).to_csv(f"{DATA}/tsunami_events.csv", index=False)
ou = U.rename(columns={"id": "ncei_runup_id", "tsunamiEventId": "ncei_event_id", "ev": "source_validity", "ok": "kept", "deep": "deep_ocean_gauge", "ht": "runup_height_m",
                       "dist": "km_from_source", "trav": "travel_hours", "place": "location", "cname": "country_name"})
ou[["ncei_runup_id", "ncei_event_id", "year", "month", "day", "source_validity", "sourceCauseCode", "kept", "doubtful", "deep_ocean_gauge", "typeMeasurementId", "country", "country_name", "location",
    "latitude", "longitude", "runup_height_m", "runupHoriz", "km_from_source", "travel_hours", "deaths", "injuries", "housesDestroyed", "period", "firstMotion"]] \
    .round({"km_from_source": 1, "travel_hours": 3}).to_csv(f"{DATA}/tsunami_runups.csv", index=False)
pd.DataFrame(cen).rename(columns={"c": "century_start", "label": "century", "n": "tsunamis"}).to_csv(f"{DATA}/tsunamis_by_century.csv", index=False)
pd.DataFrame(dec).rename(columns={"d": "decade", "n": "tsunamis", "deaths": "tsunami_deaths", "met": "meteorological", "eq": "earthquake"}).to_csv(f"{DATA}/tsunamis_by_decade.csv", index=False)
pd.DataFrame([{k: v for k, v in c.items() if k != "codes"} for c in cz]).to_csv(f"{DATA}/tsunamis_by_cause.csv", index=False)
pd.DataFrame(oc).to_csv(f"{DATA}/tsunamis_by_ocean.csv", index=False)
cty.reset_index().rename(columns={"cname": "country", "events": "tsunamis_observed", "runups": "runup_records", "deaths": "runup_deaths", "max_ht": "max_runup_m"}).round(2).to_csv(f"{DATA}/countries_hit.csv", index=False)

# ---------- page data ----------
GI = {g: i for i, g in enumerate(GN)}
OI = {o: i for i, (o, _) in enumerate(OCEANS)}
DS = D.sort_values(["year", "month", "day"], na_position="first").reset_index(drop=True)
EI = {int(i): k for k, i in enumerate(DS.id)}
loc = UC[UC.latitude.notna() & UC.longitude.notna()].copy()
loc["k"] = loc.tsunamiEventId.map(EI)
agg = loc.groupby("k").agg(n=("id", "size"), mh=("ht", "max"), md=("dist", "max"), nc=("cname", "nunique"))
def g0(v, k=2): return None if v is None or v != v else round(float(v), k)
rows = []
for k, r in DS.iterrows():
    a = agg.loc[k] if k in agg.index else None
    rows.append([int(r.id), int(r.year), nz(r.month), nz(r.day), g0(r.latitude, 3), g0(r.longitude, 3), GI[r.group], int(r.cause), r.place, r.cname,
                 g0(r.eqMagnitude, 1), g0(r.maxWaterHeight, 2), nz(r.deaths), nz(r.deathsTotal), int(a.n) if a is not None else 0,
                 g0(a.mh, 2) if a is not None else None, int(round(a.md)) if a is not None and a.md == a.md else None, int(a.nc) if a is not None else 0,
                 OI.get(r.ocean, -1), int(r.eventValidity)])
CI = {c: i for i, c in enumerate(sorted(loc.cname.unique()))}
loc = loc.sort_values(["k", "ht"], na_position="first")
rr = [[int(r.k), round(float(r.latitude), 3), round(float(r.longitude), 3), None if r.ht != r.ht else round(float(r.ht), 2), None if r.dist != r.dist else int(round(r.dist)),
       None if r.trav != r.trav else round(float(r.trav), 2), r.place, CI[r.cname], None if r.deaths != r.deaths else int(r.deaths)] for r in loc.itertuples()]
site = {"groups": GROUPS, "oceans": [o for o, _ in OCEANS], "ht_bins": HT_BINS[:-1] + [[None, HT_BINS[-1][1]]], "ht_labels": HT_LABELS, "causes": {int(k): v for k, v in CAUSE.items()},
        "cols": ["id", "year", "month", "day", "lat", "lon", "g", "cause", "place", "country", "mag", "maxht", "deaths", "deaths_total", "nrun", "maxrun", "maxdist", "ncty", "ocean", "validity"],
        "rows": rows, "famous": {k: EI[v["id"]] for k, v in fam.items()}, "famous_order": R["famous_order"]}
jsave(site, f"{DATA}/site.json")
jsave({"cols": ["e", "lat", "lon", "ht", "dist", "trav", "place", "country", "deaths"], "countries": sorted(CI, key=CI.get), "rows": rr}, f"{DATA}/runups.json")
R["page"] = {"events": len(rows), "events_located": int(DS.latitude.notna().sum()), "runups": len(rr)}
jsave(R, f"{DATA}/results.json", indent=1)
print("results ok", {k: os.path.getsize(f"{DATA}/{k}") // 1024 for k in ("site.json", "runups.json", "results.json")})
print({k: (v["n"], v["pct"]) for k, v in R["causes"].items()})
print({k: (v["n"], v["pct"], v["deaths_pct"]) for k, v in R["oceans"].items()}); print(R["ring"]); print(R["plates"]); print(R["mag"])
print("deaths", R["deaths"]); print([(d["yname"], d["place"], d["deaths"], d["deaths_total"]) for d in R["deadliest"][:12]])
print([(d["yname"], d["place"], d["deaths"], d["deaths_total"]) for d in R["deadliest_total"][:6]])
print([(h["yname"], h["event"], h["place"], h["ht"], h["group"]) for h in R["highest"][:12]]); print(R["heights"])
print([(h["yname"], h["event"], h["place"], h["rcountry"], h["dist"], h["trav"], h["ht"]) for h in R["farthest"][:10]]); print(R["dist"]); print(R["speed"])
for k, v in R["travel"].items(): print(k, v)
print(R["countries"][:15]); print(R["countries_runups"]); print(R["japan"], R["reach"]); print(R["cent"], R["modern"])
print([(c["label"], c["n"]) for c in cen]); print([(d["d"], d["n"], d["deaths"]) for d in dec])
for k, v in fam.items(): print(k, {x: v[x] for x in ("yname", "place", "group", "mag", "max_ht", "deaths", "deaths_total", "runups", "countries", "max_run", "max_run_place", "far_km", "far_place")})
print(R["atm"]); print(R["cascadia_japan"], R["sumatra"], R["page"])
