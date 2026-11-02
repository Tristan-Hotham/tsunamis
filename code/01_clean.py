"""Read the NOAA NCEI tsunami events and runups (raw/noaa_tsunami_events_runups.json); check the code lists against the
data; label each event with its cause group, ocean region and a readable name; and clean the runups.

Events. One row per tsunami source event. Kept as they are; the headline set is eventValidity 3 or 4 (probable or
definite). Year is NCEI's (negative = BC). Deaths: NCEI gives two fields. 'deaths' is the number of people the tsunami
killed; 'deathsTotal' is the total for the whole event, including the earthquake, eruption or landslide that caused it.
The text ranks tsunamis by 'deaths' and reports 'deathsTotal' only where it says so.

Runups. One row per place where the water was observed (a runup, a tide gauge reading or an eyewitness report). Kept for
analysis: the source event has validity 3 or 4, and NCEI has not flagged the runup as doubtful. NCEI's 'doubtful' field
holds four values: 'n' (not doubtful), 'y' (doubtful), 'a' and 'm'. Checked below: 'a' marks water moved by the
atmospheric pressure wave of a great eruption (almost all are Hunga Tonga 2022 and Krakatau 1883) and 'm' marks
meteorological sources (almost all belong to cause code 9). Only 'y' is dropped.
Deep-ocean pressure gauges (typeMeasurementId 3, the DART buoys) are open-sea readings, not coasts: they are kept in the
data file but left out of the map, the country counts and the distance records. distFromSource is NCEI's great-circle
distance from the source in km; runupHt is the maximum water height NCEI gives for that place in m; travel time is
travHours + travMins."""
import numpy as np, pandas as pd
from common import *

RJ = jload(f"{RAW}/noaa_tsunami_events_runups.json")
E0 = pd.DataFrame(RJ["tsunamis/events"]); U0 = pd.DataFrame(RJ["tsunamis/runups"])
info_e = json.loads(RJ["tsunamis/events_info"]); info_u = json.loads(RJ["tsunamis/runups_info"])
assert len(E0) == info_e["totalItems"] == 3138 and len(U0) == info_u["totalItems"] == 35129, (len(E0), len(U0))
assert E0.id.is_unique and U0.id.is_unique
chk = {"events": len(E0), "runups": len(U0), "events_info": info_e, "runups_info": info_u}

# ---------- code lists checked against the data ----------
chk["validity"] = {int(k): int(v) for k, v in E0.eventValidity.value_counts().sort_index().items()}
chk["cause"] = {int(k): int(v) for k, v in E0.causeCode.dropna().astype(int).value_counts().sort_index().items()}
assert set(chk["validity"]) == set(VALIDITY) and set(chk["cause"]) <= set(CAUSE)
byid = E0.set_index("id")
# the cause codes as NCEI documents them, tested on events whose cause is not in doubt
assert byid.loc[2792].causeCode == 10 and "HALIFAX" in byid.loc[2792].locationName             # 1917 Halifax munitions ship explosion
assert byid.loc[5569].causeCode == 8 and "VAJONT" in byid.loc[5569].locationName                # 1963 Vajont dam landslide
assert byid.loc[1694].causeCode == 8 and "LITUYA" in byid.loc[1694].locationName                # 1936 Lituya Bay rockslide
assert byid.loc[5911].causeCode == 8 and "DICKSON" in byid.loc[5911].locationName               # 2023 Dickson Fjord rockslide
assert byid.loc[1142].causeCode == 6 and "KRAKATAU" in byid.loc[1142].locationName              # 1883 Krakatau eruption
assert byid.loc[5824].causeCode == 6 and "TONGA" in byid.loc[5824].locationName                 # 2022 Hunga Tonga eruption
assert byid.loc[5699].causeCode == 7 and "KRAKATAU" in byid.loc[5699].locationName              # 2018 Anak Krakatau flank collapse
assert byid.loc[568].causeCode == 5 and "SHIMABARA" in byid.loc[568].locationName               # 1792 Unzen: quake, collapse, eruption
assert byid.loc[1880].causeCode == 3 and "ALASKA" in byid.loc[1880].locationName                # 1958 Lituya Bay: quake and rockslide
met = E0[E0.causeCode == 9]
assert (met.eqMagnitude.isna().mean() > .95) and (met.country == "AUSTRALIA").sum() >= 10            # meteotsunamis: no quake, many in SW Australia
eq = E0[E0.causeCode == 1]
assert eq.eqMagnitude.notna().mean() > .6 and met.eqMagnitude.notna().mean() < .05
chk["cause_checks"] = "ok"
chk["met_with_magnitude"] = int(met.eqMagnitude.notna().sum()); chk["eq_with_magnitude_pct"] = round(100 * eq.eqMagnitude.notna().mean(), 1)
chk["volcano_id_by_cause"] = {int(c): round(100 * float(g.volcanoEventId.notna().mean()), 1) for c, g in E0.groupby(E0.causeCode.fillna(-9).astype(int)) if c >= 0}
assert min(chk["volcano_id_by_cause"][c] for c in (4, 5, 6, 7)) > 80 and max(chk["volcano_id_by_cause"][c] for c in (0, 1, 2, 3, 8, 9, 10, 11)) < 5 and chk["volcano_id_by_cause"][1] < 5 and chk["volcano_id_by_cause"][8] < 5
# region codes: one country dominates each
reg_top = {int(rc): g.country.value_counts().index[0] for rc, g in E0.groupby("regionCode")}
assert reg_top[85] == "JAPAN" and reg_top[86] == "RUSSIA" and reg_top[89] == "CHILE" and reg_top[50] == "GREECE" and reg_top[80] == "USA" and reg_top[60] == "INDONESIA"
chk["region_top_country"] = reg_top

# ---------- events ----------
E = E0.copy()
E["cause"] = E.causeCode.fillna(0).astype(int)
E["group"] = E.cause.map(CAUSE_GROUP)
E["valid"] = E.eventValidity.isin([3, 4]).astype(int)
E["ocean"] = E.regionCode.map(lambda r: REGION_OCEAN.get(int(r), "Unknown") if r == r else "Unknown")
E["ring"] = E.regionCode.map(lambda r: int(r == r and int(r) in RING))
E["place"] = E.locationName.map(tcase)
E["cname"] = E.country.map(country)
for c in ("deaths", "deathsTotal", "maxWaterHeight", "eqMagnitude", "damageMillionsDollarsTotal", "housesDestroyedTotal", "injuriesTotal", "missingTotal"):
    E[c] = pd.to_numeric(E[c], errors="coerce")
chk["deaths_gt_total"] = int((E.deaths > E.deathsTotal).sum())
assert chk["deaths_gt_total"] == 0
chk["no_coords"] = int(E.latitude.isna().sum()); chk["no_coords_valid"] = int((E.latitude.isna() & (E.valid == 1)).sum())

# ---------- runups ----------
U = U0.copy()
U["ev"] = U.sourceEventValidity
U["ok"] = ((U.ev.isin([3, 4])) & (U.doubtful != "y")).astype(int)
U["atm"] = (U.doubtful == "a").astype(int)
fa = U[U.doubtful == "a"].tsunamiEventId.value_counts(); fm = U[U.doubtful == "m"]
assert set(U.doubtful.unique()) == {"n", "y", "a", "m"}
assert (fa.get(5824, 0) + fa.get(1142, 0)) / fa.sum() > .95 and (fm.sourceCauseCode == 9).mean() > .95
U["deep"] = (U.typeMeasurementId == 3).astype(int)
U["ht"] = pd.to_numeric(U.runupHt, errors="coerce")
U["dist"] = pd.to_numeric(U.distFromSource, errors="coerce")
U["trav"] = np.where(U.travHours.notna() | U.travMins.notna(), U.travHours.fillna(0) + U.travMins.fillna(0) / 60, np.nan)
U.loc[U.trav <= 0, "trav"] = np.nan
U["place"] = U.locationName.map(tcase)
U["cname"] = U.country.map(country)
U["deaths"] = pd.to_numeric(U.deaths, errors="coerce")
chk["doubtful"] = U.doubtful.value_counts().to_dict()
chk["runup_types"] = {int(k): int(v) for k, v in U.typeMeasurementId.dropna().astype(int).value_counts().sort_index().items()}
deep_names = U[U.deep == 1].locationName.fillna("")
assert deep_names.str.contains(r"\bD\d{3,}|BPR|DART", regex=True).mean() > .8      # type 3 = deep-ocean pressure gauges
chk["runups_valid_src"] = int(U.ev.isin([3, 4]).sum()); chk["runups_ok"] = int(U.ok.sum())
chk["runups_ok_deep"] = int((U.ok & U.deep).sum())
ev_ids = set(E.id)
chk["runups_orphan"] = int((~U.tsunamiEventId.isin(ev_ids)).sum())
assert chk["runups_orphan"] == 0
vmap = E.set_index("id").eventValidity
assert (U.tsunamiEventId.map(vmap) == U.ev).all()

E.to_pickle(f"{WORK}/events.pkl"); U.to_pickle(f"{WORK}/runups.pkl")
jsave(chk, f"{WORK}/checks.json", indent=1)
print("events", len(E), "valid", int(E.valid.sum()), "runups", len(U), "kept", int(U.ok.sum()), "deep", chk["runups_ok_deep"])
print(chk["validity"], chk["cause"])
