"""Build index.html from code/page_template.html. Every number in the text is a {{path|format}} token filled from
data/results.json; page data (results, site.json, world.json, plates, country and ocean labels, cities) is embedded;
data/runups.json is loaded by the page. Facts stated in words are checked here. The full-screen map snippet
(code/fullscreen_snippet.html) is pasted before </body>. 10.5281/zenodo.23873531 and https://blog.tristanhotham.com/2026/10/31/tsunamis/ stay as placeholders for the publisher.
Needs only data/ (not raw/)."""
import json
from common import *

R = jload(f"{DATA}/results.json")
SITE = jload(f"{DATA}/site.json")
F, C, O, TR = R["famous"], R["causes"], R["oceans"], R["travel"]

# facts stated in words (page, blog, paper, collage)
assert R["source"]["first_year"] == -1610 and F["thera"]["validity"] == 4
assert C["Explosion"]["n"] == 2 and C["Explosion"]["codes"] == {"Explosion": 2}           # Halifax 1917 and Ripple Rock 1958
assert C["Volcano"]["deaths"] > 0 and (F["krakatau"]["deaths"] + 15000) / C["Volcano"]["deaths"] > .5   # "mostly Krakatau and Unzen (Shimabara, 15,000)"
assert [d for d in R["deadliest"] if d["year"] == 1792][0]["deaths"] == 15000 and [d for d in R["deadliest"] if d["year"] == 1792][0]["group"] == "Volcano"
assert C["Volcano"]["pct"] < 10 and C["Volcano"]["deaths_pct"] > C["Volcano"]["pct"]       # "few tsunamis but deadly ones"
assert O["Pacific"]["pct"] > 60 and 60 < R["ring"]["pct"] < 70                               # "two in three"
assert O["Indian Ocean"]["deaths_pct"] > 45 and R["deaths"]["y2004_pct"] > 40                 # "almost all from a single morning"
assert R["heights"]["ge100_landslide"] == R["heights"]["ge100_events"] == 9
assert R["highest"][0]["year"] == 1958 and R["highest"][1]["year"] == 2025 and "Tracy" in R["highest"][1]["place"]
assert (F["lituya"]["month"], F["lituya"]["day"]) == (7, 10) and (F["alaska"]["month"], F["alaska"]["day"]) == (3, 28)
assert (F["lisbon"]["month"], F["lisbon"]["day"]) == (11, 1) and (F["chile"]["month"], F["chile"]["day"]) == (5, 22) and (F["sumatra"]["month"], F["sumatra"]["day"]) == (12, 26)
assert (F["tohoku"]["month"], F["tohoku"]["day"]) == (3, 11) and (F["tonga"]["month"], F["tonga"]["day"]) == (1, 15) and (F["krakatau"]["month"], F["krakatau"]["day"]) == (8, 27)
assert (F["sanriku"]["month"], F["sanriku"]["day"]) == (6, 15) and (F["aleutian"]["month"], F["aleutian"]["day"]) == (4, 1) and F["cascadia"]["month"] == 1
assert F["lisbon"]["max_run_place"] == "Cadiz" and F["lisbon"]["far_country"] == "Dominican Republic" and F["sanriku"]["far_country"] == "Cook Islands"
assert F["aleutian"]["max_run_place"].startswith("Scotch Cap") and F["tohoku"]["max_run_place"].startswith("Iwate") and F["krakatau"]["max_run_place"].startswith("Merak")
assert F["cascadia"]["countries"] == 1 and R["cascadia_japan"]["n"] == F["cascadia"]["runups"]
assert F["alaska"]["far_country"] == "Antarctica" and F["sumatra"]["far_place"] == "Baltra Island"
assert R["reach"]["top"][0]["id"] == 5824 and R["reach"]["top"][1]["id"] == 2439                     # Tonga most countries; 2004 most of any sea wave
assert R["deadliest"][3]["id"] == 1234                                                                 # Sanriku fourth
assert [d["year"] for d in R["deadliest"][:6]] == [2004, 1755, 1883, 1896, 1868, 2011]
assert R["atm"]["tonga_far_country"] == "Ghana" and R["atm"]["krakatau_far_country"] == "Panama"
assert R["atm"]["tonga"] + R["atm"]["krakatau"] == R["atm"]["n"]
assert sum(1 for f in R["farthest"][1:10] if "Chile" in f["event"]) >= 6                               # "Chilean earthquakes fill most of the rest"
assert R["travel"]["aleut_hilo"]["first_h"] < 5                                                         # "less than five hours"
assert R["countries"][0]["country"] == "Japan" and R["countries"][1]["country"] == "United States" and R["countries"][2]["country"] == "Indonesia"
assert R["cent"]["c1900"] > R["cent"]["c1800"] > R["cent"]["c1700"] > R["cent"]["c1600"]
assert R["modern"]["met_since2000"] > 5 * R["modern"]["met_before1950"]
assert R["decades"][0]["d"] == 1900 and R["decades"][11]["d"] == 2010
assert R["mag"]["ge9"] == 7 and F["chile"]["mag"] == max(9.5, F["chile"]["mag"])


def build():
    tpl = open(os.path.join(ROOT, "code", "page_template.html"), encoding="utf-8").read()
    html = fill(tpl, R)
    left = re.findall(r"\{\{[^}]*\}\}", html)
    assert set(left) <= {"10.5281/zenodo.23873531", "https://blog.tristanhotham.com/2026/10/31/tsunamis/"}, left[:5]
    J = lambda o: json.dumps(o, ensure_ascii=False, separators=(",", ":"))
    RS = {k: v for k, v in R.items() if k not in ("source",)}
    RS["source"] = {k: v for k, v in R["source"].items() if k != "checks"}
    html = html.replace("/*RESULTS*/", J(RS)).replace("/*SITE*/", J(SITE))
    html = html.replace("/*WORLD*/", open(f"{DATA}/world.json", encoding="utf-8").read())
    html = html.replace("/*PLATES*/", open(f"{DATA}/plates.json", encoding="utf-8").read())
    html = html.replace("/*COUNTRIES*/", J({k: v for k, v in jload(f"{DATA}/countries.json").items() if v["pop"] > 2e5}))
    html = html.replace("/*OCEANS*/", J(jload(f"{DATA}/oceans.json")))
    html = html.replace("/*CITIES*/", J([c for c in jload(f"{DATA}/cities.json") if c["pop"] >= 4e5]))
    html = html.replace("/*FULLSCREEN*/", open(os.path.join(ROOT, "code", "fullscreen_snippet.html"), encoding="utf-8").read())
    vis = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", html, flags=re.S)
    vis = re.sub(r"<[^>]+>", " ", vis)
    for bad in ("—", "–", "--", "DSIT", "DCMS", "civil serv", "Civil Serv"):
        assert bad not in vis, bad
    for scr in re.findall(r"<script>(.*?)</script>", html, flags=re.S):
        for bad in ("—", "–"):
            assert bad not in scr, bad
    open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(html)
    print("index.html", len(html.encode()) // 1024, "KB")


if __name__ == "__main__":
    build()
