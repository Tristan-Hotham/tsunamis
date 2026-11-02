"""Blog post and meta (release/blog), Zenodo files and metadata (release/zenodo).
10.5281/zenodo.23873531, https://doi.org/10.5281/zenodo.23873531 and https://blog.tristanhotham.com/2026/10/31/tsunamis/ stay as placeholders for the publisher. Needs only data/, code/, the figures and
the paper PDF: raw/ is not used and is not packed."""
import json as _json, shutil, zipfile, importlib.util
from common import *

R = jload(f"{DATA}/results.json")
REL = os.path.join(ROOT, "release"); NAME = "Hotham_Every_Tsunami_on_Record"

# the page build checks the shared facts; these are numbers written in words or alt text in the blog and collage
spec = importlib.util.spec_from_file_location("b", os.path.join(ROOT, "code", "04_build_site.py")); spec.loader.exec_module(importlib.util.module_from_spec(spec))
C, O = R["causes"], R["oceans"]
assert (round(C["Earthquake"]["pct"]), round(C["Earthquake"]["deaths_pct"]), round(C["Volcano"]["pct"]), round(C["Volcano"]["deaths_pct"]), round(C["Landslide"]["pct"])) == (72, 85, 6, 10, 8) and C["Landslide"]["deaths_pct"] < 1
assert (round(O["Pacific"]["pct"]), round(O["Pacific"]["deaths_pct"]), round(O["Indian Ocean"]["pct"]), round(O["Indian Ocean"]["deaths_pct"])) == (67, 38, 6, 50)
assert [d["deaths"] for d in R["deadliest"][:6]] == [227899, 50000, 34417, 27122, 25000, 18423]
assert [round(h["ht"]) for h in R["highest"][:5]] == [524, 481, 250, 235, 200] and min(h["ht"] for h in R["highest"][:12]) >= 90
assert sum(h["group"] == "Landslide" for h in R["highest"][:12]) >= 8                                    # "almost all purple"
assert [R["cent"][k] for k in ("c1600", "c1700", "c1800", "c1900")] == [63, 88, 282, 718] and all(c["n"] < 10 for c in R["centuries"] if 1000 <= c["c"] < 1400)
f0 = R["farthest"][0]; assert f0["dist"] > 19000 and f0["trav"] > 29
assert R["famous"]["sumatra"]["countries"] == 48 and R["famous"]["chile"]["countries"] == 35

post = open(os.path.join(ROOT, "code", "blog_template.html"), encoding="utf-8").read()
post = fill(post, R)
used = re.findall(r"\{\{IMG\|([^|]+)\|", post)
assert 5 <= len(used) <= 8, len(used)
assert all(re.search(r"^\{\{IMG\|" + re.escape(u), post, re.M) for u in used) and "wp:image" not in post
for img in used:
    assert os.path.exists(f"{REL}/blog/{img}"), img
    from PIL import Image
    assert Image.open(f"{REL}/blog/{img}").size[0] == 1800, img
for fn in os.listdir(f"{REL}/blog"):
    if fn.startswith("b_") and fn not in used:
        os.remove(f"{REL}/blog/{fn}")
assert set(re.findall(r"\{\{[^|}]+\}\}", post)) <= {"https://doi.org/10.5281/zenodo.23873531"}
vis = re.sub(r"<!--.*?-->", "", post, flags=re.S)
for bad in ("\u2014", "\u2013", "--", "DSIT", "DCMS"):
    assert bad not in vis, bad
open(f"{REL}/blog/post.html", "w", encoding="utf-8").write(post)
words = len(re.sub(r"<[^>]+>|\{\{IMG\|[^}]*\}\}", " ", vis).split())
s = R["source"]
meta = {"title": "Every tsunami on record: where they start, where the water went, and who died",
        "slug": "tsunamis",
        "excerpt": f"I mapped all {s['n']:,} tsunamis in NOAA's Global Historical Tsunami Database since {s['first_name']} and the places their water reached. {C['Earthquake']['pct']:.0f}% started with an earthquake, the highest ran {R['famous']['lituya']['max_run']:.0f} m up a mountainside, and 2004 alone accounts for {R['deaths']['y2004_pct']:.0f}% of recorded deaths.",
        "seo_description": f"A map of {s['n']:,} tsunamis since {s['first_name']}: causes, the places the water reached, the deadliest, the highest and the farthest waves.",
        "tags": ["tsunamis", "natural hazards", "earthquakes", "maps", "data visualisation", "NOAA", "history", "oceans"],
        "header_alt": f"Title card reading 'Every tsunami on record' in black and deep blue on pale paper, beside a Pacific-centred world map with orange and red circles for tsunami sources along the plate boundaries, the largest off Sumatra, and blue dots along the coasts their water reached. Text: {s['n']:,} tsunamis since {s['first_name']}; the highest ran {R['famous']['lituya']['max_run']:.0f} m up a mountainside."}
assert len(meta["seo_description"]) < 160, len(meta["seo_description"])
jsave(meta, f"{REL}/blog/meta.json", indent=2)

# Zenodo
Z = f"{REL}/zenodo"; os.makedirs(Z, exist_ok=True)
for fn in os.listdir(Z):
    os.remove(os.path.join(Z, fn))
shutil.copy(f"{REL}/paper/{NAME}.pdf", f"{Z}/{NAME}.pdf")
zp = f"{Z}/tsunamis_data_and_code.zip"
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for d in ("code", "data"):
        for fn in sorted(os.listdir(os.path.join(ROOT, d))):
            if fn.endswith(".pyc") or fn == "__pycache__":
                continue
            z.write(os.path.join(ROOT, d, fn), f"tsunamis/{d}/{fn}")
    for fn in ("README.md", "LICENSE"):
        z.write(os.path.join(ROOT, fn), f"tsunamis/{fn}")
    z.write(os.path.join(ROOT, "reddit", "collage.py"), "tsunamis/reddit/collage.py")
tex = open(f"{REL}/paper/{NAME}.tex", encoding="utf-8").read()
ab = re.search(r"\\begin\{center\}\\textbf\{Abstract\}\\end\{center\}\n(.*?)\n\n\\textbf\{Keywords", tex, re.S).group(1)
ab = ab.replace("\\%", "%").replace("\\&", "&")
zmeta = {"title": "Every Tsunami on Record: Sources, Runups and Deaths in NOAA's Global Historical Tsunami Database",
         "upload_type": "publication", "publication_type": "workingpaper",
         "description": f"<p>{ab}</p><p>Interactive version: <a href=\"{PAGE}\">{PAGE}</a>. Data and code: <a href=\"{REPO}\">{REPO}</a>. Blog post: {BLOG}.</p><p>Tsunami data: NOAA NCEI/WDS Global Historical Tsunami Database, doi:10.7289/V5PN93H7 (public domain).</p>",
         "creators": [{"name": "Hotham, Tristan", "affiliation": "Independent researcher", "orcid": "0000-0003-4931-9349"}],
         "keywords": ["tsunamis", "natural hazards", "earthquakes", "landslides", "volcanoes", "tsunami runup", "disaster mortality", "NOAA NCEI", "open data", "maps"],
         "license": "cc-by-4.0", "language": "eng",
         "related_identifiers": [{"identifier": REPO, "relation": "isSupplementedBy", "resource_type": "software"},
                                 {"identifier": PAGE, "relation": "isSupplementedBy", "resource_type": "other"},
                                 {"identifier": "10.7289/V5PN93H7", "relation": "isDerivedFrom", "resource_type": "dataset", "scheme": "doi"},
                                 {"identifier": "10.1029/2001GC000252", "relation": "references", "resource_type": "publication-article", "scheme": "doi"},
                                 {"identifier": "https://www.naturalearthdata.com/", "relation": "isDerivedFrom", "resource_type": "dataset"}],
         "files": sorted(os.listdir(Z))}
sj = _json.dumps(zmeta, ensure_ascii=False) + _json.dumps(meta, ensure_ascii=False)
assert "\u2014" not in sj and "\u2013" not in sj and "--" not in sj
jsave(zmeta, f"{Z}/metadata.json", indent=2)
print("blog words", words, "figures", len(used), "; zenodo", sorted(os.listdir(Z)), os.path.getsize(zp) // 1024, "KB zip")
