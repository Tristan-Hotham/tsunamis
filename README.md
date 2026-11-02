# Every tsunami on record: where tsunamis start, where the water went, and who died

A map and analysis of the 1,699 tsunamis that NOAA NCEI rates as definite or probable in its Global Historical Tsunami Database, from 1610 BC to 2026, and the 33,532 records of places where their water was observed: causes, oceans, deaths, runup heights, distances and travel times.

Interactive page: https://maps.tristanhotham.com/tsunamis/
Paper: https://doi.org/10.5281/zenodo.23873531
Blog post: https://blog.tristanhotham.com/2026/10/31/tsunamis/

## Headline results

- Count: 1,699 definite (1,110) and probable (589) tsunamis out of 3,138 source events in the database.
- Causes: earthquake alone 72.0%, earthquake and landslide 6.8%, landslide 7.7%, volcano 6.1%, meteorological 4.5%, explosion 2, unknown 2.8%. 63% of earthquake sources lie within 100 km of a PB2002 plate boundary.
- Where: Pacific regions 67.2%, Pacific rim (Ring of Fire, without Hawaii) 66.6%, Japan alone 17.9%; Mediterranean 13.7%; Atlantic and Caribbean 11.6%; Indian Ocean 5.8% of tsunamis but 50.1% of deaths.
- Deaths: 545,939 tsunami deaths recorded for 244 tsunamis; 2004 Indian Ocean 227,899 (41.7%); Lisbon 1755 50,000; Krakatau 1883 34,417; Sanriku 1896 27,122; northern Chile 1868 25,000; Tohoku 2011 18,423. NCEI's whole-event total (with the earthquake) is a different field: Haiti 2010 316,000, tsunami 7.
- Heights: highest runup 524.3 m, Lituya Bay 1958; then Tracy Arm 2025 (481 m). All 9 tsunamis with a runup of 100 m or more involved a landslide or a volcano.
- Distance and speed: farthest sea wave measurement 19,266 km (Baltra Island, Galápagos, from Sumatra 2004, after 29.1 h). Median speed beyond 1,000 km 680 km/h. Chile 1960 reached Hilo in 14.8 h and Japan in 22.4 h; 2004 reached Kenya in 8.9 h and South Africa in 11.1 h.
- Countries: Japan reached by 395 different tsunamis, the United States 264, Indonesia 138. Hunga Tonga 2022 reached 67 countries (mostly via its air wave); 2004 reached 48.
- Time: 63 tsunamis recorded in the 1600s, 282 in the 1800s, 718 in the 1900s. A recording effect, not a trend.

## Files

| File | What it is |
|---|---|
| `index.html` | The interactive page (built by `code/04_build_site.py`; page data embedded, `data/runups.json` loaded by the page). |
| `header.png` | Social card, 1200 x 630. |
| `data/tsunami_events.csv` | All 3,138 NCEI source events with validity, cause code and group, place, region, ocean, magnitude, maximum water height, tsunami deaths and whole-event deaths, distance to the nearest plate boundary. |
| `data/tsunami_runups.csv` | All 35,129 runup records with the source, flags (kept, doubtful, deep-ocean gauge), place, height, distance, travel time and deaths at that place. |
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
- Caveats: completeness falls steeply with age; old death tolls are estimates; survey effort varies hugely between events; 2026 is partial.

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

- National Geophysical Data Center / World Data Service (NGDC/WDS): NCEI/WDS Global Historical Tsunami Database. NOAA National Centers for Environmental Information. doi:10.7289/V5PN93H7. Fetched in 2026 from https://www.ngdc.noaa.gov/hazel/hazard-service/api/v1/. US government work, public domain.
- Bird, P. (2003) An updated digital model of plate boundaries. Geochemistry, Geophysics, Geosystems 4(3), 1027. GeoJSON by Hugo Ahlenius, Nordpil (github.com/fraxen/tectonicplates). Open Data Commons Attribution License.
- Natural Earth countries and populated places (https://www.naturalearthdata.com/). Public domain.
- Sea floor tiles on the page (optional layer): © Esri, GEBCO, NOAA and other contributors.

## Citation

Hotham, T. (2026) Every tsunami on record: sources, runups and deaths in NOAA's Global Historical Tsunami Database. Zenodo. https://doi.org/10.5281/zenodo.23873531

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
