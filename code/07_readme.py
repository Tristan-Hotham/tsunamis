"""README.md, LICENSE and reddit/post.md, with numbers from data/results.json. Needs only data/."""
from common import *

R = jload(f"{DATA}/results.json")
s, C, O, F, D, T = R["source"], R["causes"], R["oceans"], R["famous"], R["deaths"], R["travel"]
N = lambda v: f"{round(v):,}"
readme = f"""# Every tsunami on record: where tsunamis start, where the water went, and who died

A map and analysis of the {N(s['n'])} tsunamis that NOAA NCEI rates as definite or probable in its Global Historical Tsunami Database, from {s['first_name']} to {s['last_year']}, and the {N(s['runups_kept'])} records of places where their water was observed: causes, oceans, deaths, runup heights, distances and travel times.

Interactive page: {PAGE}
Paper: https://doi.org/{DOI}
Blog post: {BLOG}

## Headline results

- Count: {N(s['n'])} definite ({N(s['definite'])}) and probable ({N(s['probable'])}) tsunamis out of {N(s['events'])} source events in the database.
- Causes: earthquake alone {C['Earthquake']['pct']:.1f}%, earthquake and landslide {C['Earthquake and landslide']['pct']:.1f}%, landslide {C['Landslide']['pct']:.1f}%, volcano {C['Volcano']['pct']:.1f}%, meteorological {C['Meteorological']['pct']:.1f}%, explosion {C['Explosion']['n']}, unknown {C['Unknown']['pct']:.1f}%. {R['plates']['within100_pct']:.0f}% of earthquake sources lie within 100 km of a PB2002 plate boundary.
- Where: Pacific regions {O['Pacific']['pct']:.1f}%, Pacific rim (Ring of Fire, without Hawaii) {R['ring']['pct']:.1f}%, Japan alone {R['ring']['japan_pct']:.1f}%; Mediterranean {O['Mediterranean']['pct']:.1f}%; Atlantic and Caribbean {O['Atlantic and Caribbean']['pct']:.1f}%; Indian Ocean {O['Indian Ocean']['pct']:.1f}% of tsunamis but {O['Indian Ocean']['deaths_pct']:.1f}% of deaths.
- Deaths: {N(D['total'])} tsunami deaths recorded for {D['n_events']} tsunamis; 2004 Indian Ocean {N(R['deadliest'][0]['deaths'])} ({D['y2004_pct']:.1f}%); Lisbon 1755 {N(R['deadliest'][1]['deaths'])}; Krakatau 1883 {N(R['deadliest'][2]['deaths'])}; Sanriku 1896 {N(R['deadliest'][3]['deaths'])}; northern Chile 1868 {N(R['deadliest'][4]['deaths'])}; Tohoku 2011 {N(R['deadliest'][5]['deaths'])}. NCEI's whole-event total (with the earthquake) is a different field: Haiti 2010 {N(R['haiti']['deaths_total'])}, tsunami {R['haiti']['deaths']}.
- Heights: highest runup {F['lituya']['max_run']:.1f} m, Lituya Bay 1958; then Tracy Arm 2025 ({R['highest'][1]['ht']:.0f} m). All {R['heights']['ge100_events']} tsunamis with a runup of 100 m or more involved a landslide or a volcano.
- Distance and speed: farthest sea wave measurement {N(R['farthest'][0]['dist'])} km ({R['farthest'][0]['place']}, Galápagos, from Sumatra 2004, after {R['farthest'][0]['trav']:.1f} h). Median speed beyond 1,000 km {R['speed']['median_kmh']} km/h. Chile 1960 reached Hilo in {T['chile_hilo']['first_h']} h and Japan in {T['chile_japan']['first_h']} h; 2004 reached Kenya in {T['sum_kenya']['first_h']} h and South Africa in {T['sum_safrica']['first_h']} h.
- Countries: Japan reached by {R['countries'][0]['events']} different tsunamis, the United States {R['countries'][1]['events']}, Indonesia {R['countries'][2]['events']}. Hunga Tonga 2022 reached {F['tonga']['countries']} countries (mostly via its air wave); 2004 reached {F['sumatra']['countries']}.
- Time: {R['cent']['c1600']} tsunamis recorded in the 1600s, {R['cent']['c1800']} in the 1800s, {R['cent']['c1900']} in the 1900s. A recording effect, not a trend.

## Files

| File | What it is |
|---|---|
| `index.html` | The interactive page (built by `code/04_build_site.py`; page data embedded, `data/runups.json` loaded by the page). |
| `header.png` | Social card, 1200 x 630. |
| `data/tsunami_events.csv` | All {N(s['events'])} NCEI source events with validity, cause code and group, place, region, ocean, magnitude, maximum water height, tsunami deaths and whole-event deaths, distance to the nearest plate boundary. |
| `data/tsunami_runups.csv` | All {N(s['runups'])} runup records with the source, flags (kept, doubtful, deep-ocean gauge), place, height, distance, travel time and deaths at that place. |
| `data/tsunamis_by_century.csv`, `data/tsunamis_by_decade.csv` | Counts by century and cause, and by decade since 1900. |
| `data/tsunamis_by_cause.csv`, `data/tsunamis_by_ocean.csv` | Counts, shares and deaths by cause group and ocean. |
| `data/countries_hit.csv` | Per country or territory: different tsunamis recorded, place records, highest water. |
| `data/results.json` | Every number used in the page, paper, blog, collage and post. |
| `data/site.json`, `data/runups.json`, `data/world.json`, `data/plates.json`, `data/countries.json`, `data/oceans.json`, `data/cities.json` | Page and figure data. |
| `code/` | Scripts, run in order (below), and the page, paper and blog templates. |
| `release/` | Paper PDF and LaTeX source with figures (`paper/`), blog post, figures and meta (`blog/`), Zenodo files (`zenodo/`). |
| `reddit/` | Collage (`collage.py`, PNG) and post text. |
| `qa/` | Screenshots of the page at desktop and phone widths. |

## Method in brief

- Tsunamis: NCEI eventValidity 4 (definite) or 3 (probable). Validity codes: 4 definite, 3 probable, 2 questionable, 1 very doubtful, 0 seiche or inland disturbance only, -1 erroneous.
- Causes: NCEI codes 0 unknown, 1 earthquake, 2 questionable earthquake, 3 earthquake and landslide, 4 volcano and earthquake, 5 volcano, earthquake and landslide, 6 volcano, 7 volcano and landslide, 8 landslide, 9 meteorological, 10 explosion, 11 astronomical tide; checked against known events (Halifax 1917 = 10, Vajont 1963 = 8, Krakatau 1883 = 6) and grouped.
- Oceans: NCEI region codes (Pacific 80 to 89; Ring of Fire 81 to 89).
- Deaths: NCEI's tsunami deaths, never the whole-event total; runup-place deaths are not summed.
- Runups: kept if the source is definite or probable and NCEI does not flag the record as doubtful ('y'). Records flagged 'a' (moved by an eruption's air wave) and 'm' (meteorological) are kept; air wave places are left out of distance and speed. Deep-ocean gauges (measurement type 3) are left off the map and out of country and distance counts.
- Caveats: completeness falls steeply with age; old death tolls are estimates; survey effort varies hugely between events; {s['last_year']} is partial.

## How to rerun

Needs Python 3 with numpy, pandas, scipy, shapely, pyproj, matplotlib and fontTools, xelatex and pdftotext; node with Playwright for `code/qa.js`. Scripts 01 to 03 read the raw inputs (`raw/`, not part of the release: the NCEI API extract `noaa_tsunami_events_runups.json` and `PB2002_boundaries.json`) and Natural Earth (`/home/claude/newdata/raw/geo/`, set `TS_GEO`). Everything after 03 needs only `data/`. Intermediate files go to `/dev/shm/tsunamis/work` (set `TSTMP`).

```
python3 code/01_clean.py        # read NCEI events and runups, check code lists, label causes and oceans
python3 code/02_geo.py          # outlines, labels, plate boundaries, distance to plate boundary
python3 code/03_results.py      # results.json, data tables, page data
python3 code/04_build_site.py   # index.html
python3 code/05_figures.py      # header, blog and paper figures
python3 code/06_paper.py        # paper PDF
python3 reddit/collage.py       # collage
python3 code/07_readme.py       # README, LICENSE, Reddit post
python3 code/08_release.py      # blog post, Zenodo files
```

## Sources and licences

- National Geophysical Data Center / World Data Service (NGDC/WDS): NCEI/WDS Global Historical Tsunami Database. NOAA National Centers for Environmental Information. doi:10.7289/V5PN93H7. Fetched in {s['fetched']} from {API_URL}. US government work, public domain.
- Bird, P. (2003) An updated digital model of plate boundaries. Geochemistry, Geophysics, Geosystems 4(3), 1027. GeoJSON by Hugo Ahlenius, Nordpil (github.com/fraxen/tectonicplates). Open Data Commons Attribution License.
- Natural Earth countries and populated places (https://www.naturalearthdata.com/). Public domain.
- Sea floor tiles on the page (optional layer): © Esri, GEBCO, NOAA and other contributors.

## Citation

Hotham, T. (2026) Every tsunami on record: sources, runups and deaths in NOAA's Global Historical Tsunami Database. Zenodo. https://doi.org/{DOI}

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

{AI}
"""
open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8").write(readme)

lic = """MIT License

Copyright (c) 2026 Tristan Hotham

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE."""
lic += """


This licence covers the code in code/, reddit/collage.py and the page scripts.
The text of the page, paper and blog post, the figures and the derived data
files in data/ are released under CC BY 4.0. The tsunami data are derived from
the NCEI/WDS Global Historical Tsunami Database, NOAA National Centers for
Environmental Information (doi:10.7289/V5PN93H7), a US government work in the
public domain; NCEI asks that it be cited. Plate boundaries: Bird (2003),
PB2002, GeoJSON by Hugo Ahlenius, Open Data Commons Attribution License.
Natural Earth is public domain.
"""
open(os.path.join(ROOT, "LICENSE"), "w", encoding="utf-8").write(lic)

post = f"""## Title

[OC] Every tsunami on record: {N(s['n'])} since {s['first_name']}, mapped with the {N(R['page']['runups'])} places their water reached. {C['Earthquake']['pct']:.0f}% start with an earthquake, the highest ran {F['lituya']['max_run']:.0f} m up a mountain, and one day in 2004 accounts for {D['y2004_pct']:.0f}% of all recorded deaths

## Body

I mapped every tsunami NOAA's Global Historical Tsunami Database rates as definite or probable, {N(s['n'])} of them, and the places where their water was recorded. {R['ring']['pct']:.0f}% began on the rim of the Pacific, and {R['eq_any_pct']:.0f}% involved an earthquake. The deaths are concentrated: {N(D['total'])} tsunami deaths are recorded, {D['y2004_pct']:.0f}% of them from the 2004 Indian Ocean tsunami; the Indian Ocean has {O['Indian Ocean']['pct']:.0f}% of the tsunamis but {O['Indian Ocean']['deaths_pct']:.0f}% of the deaths. The highest water comes from landslides into fjords, led by Lituya Bay in Alaska ({F['lituya']['max_run']:.0f} m in 1958). Waves crossing oceans move at about {R['speed']['median_kmh']} km/h: Chile 1960 reached Japan in {T['chile_japan']['first_h']} hours. Caveats: the record grows from {R['cent']['c1600']} tsunamis in the 1600s to {R['cent']['c1900']} in the 1900s, which is better recording, not more tsunamis; old death tolls are estimates; deaths are the tsunami's own, not the earthquake's. Interactive map with a time slider, a tour of famous waves and lines from each source to every place it reached: {PAGE}

## Source comment

Source: NOAA NCEI/WDS Global Historical Tsunami Database (doi:10.7289/V5PN93H7, public domain), events and runups from the NCEI Hazard Service API, {s['fetched']}. Tsunamis = NCEI validity 3 (probable) or 4 (definite); deaths = NCEI's tsunami deaths; runups flagged doubtful dropped. Plate boundaries: Bird (2003) PB2002. Outlines: Natural Earth.

Tools: Python (pandas, shapely, pyproj, matplotlib); MapLibre for the interactive map.

Interactive version: {PAGE}
Paper: https://doi.org/{DOI}
Blog post: {BLOG}
"""
for t in (readme, post):
    for bad in ("—", "–", "--", "DSIT", "DCMS"):
        assert bad not in t.replace("```", "").replace("|---|---|", ""), bad
open(os.path.join(ROOT, "reddit", "post.md"), "w", encoding="utf-8").write(post)
print("readme, licence, post ok")
