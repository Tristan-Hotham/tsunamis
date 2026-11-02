"""Shared paths, groupings and helpers for the tsunamis project.

Raw inputs (read in place by 01 and 02, never modified; raw/ is not needed once data/ is built):
  raw/noaa_tsunami_events_runups.json   NOAA NCEI Hazard Service API (https://www.ngdc.noaa.gov/hazel/hazard-service/api/v1/),
      endpoints tsunamis/events (3,138 source events) and tsunamis/runups (35,129 places where the water was observed),
      fetched 2 November 2026. Each list sits under its endpoint name; the two *_info strings hold the API's totals.
      NOAA National Centers for Environmental Information (NCEI/WDS), Global Historical Tsunami Database,
      doi:10.7289/V5PN93H7. US government work, public domain; NCEI asks to be cited.
  raw/PB2002_boundaries.json            Bird (2003) plate boundary model (PB2002) as GeoJSON by Hugo Ahlenius, Nordpil,
      github.com/fraxen/tectonicplates. Open Data Commons Attribution License 1.0.
  /home/claude/newdata/raw/geo/ne_50m_admin_0_countries.geojson, ne_50m_land.geojson, ne_10m_populated_places_simple.geojson
      Natural Earth, public domain.

NCEI codes, as documented by NCEI and checked against the distributions in 01_clean.py:
  eventValidity  4 definite tsunami, 3 probable, 2 questionable, 1 very doubtful, 0 an event that only caused a seiche or a
                 disturbance in an inland river or lake, -1 erroneous entry. Headline counts use 3 and 4.
  causeCode      0 unknown, 1 earthquake, 2 questionable earthquake, 3 earthquake and landslide, 4 volcano and earthquake,
                 5 volcano, earthquake and landslide, 6 volcano, 7 volcano and landslide, 8 landslide, 9 meteorological,
                 10 explosion, 11 astronomical tide.
  regionCode     NCEI's geographic regions (30 Red Sea and Persian Gulf, 40 Black Sea and Caspian, 50 Mediterranean,
                 60 Indian Ocean, 70 to 77 Atlantic and Caribbean coasts, 78 Central Africa, 80 Hawaii, 81 to 89 the
                 rim of the Pacific), grouped into oceans in OCEANS below.
"""
import json, gzip, os, re, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.environ.get("TS_RAW", os.path.join(ROOT, "raw"))
GEO = os.environ.get("TS_GEO", "/home/claude/newdata/raw/geo")
FONTS = os.environ.get("TS_FONTS", "/home/claude/ref/fonts")
DATA = os.path.join(ROOT, "data")
WORK = os.path.join(os.environ.get("TSTMP", "/dev/shm/tsunamis"), "work")   # intermediates live in memory, not in the repo
for d in (DATA, WORK):
    os.makedirs(d, exist_ok=True)

SLUG = "tsunamis"
PAGE = f"https://maps.tristanhotham.com/{SLUG}/"
REPO = f"https://github.com/Tristan-Hotham/{SLUG}"
DOI = "10.5281/zenodo.23873531"                # filled in by the publisher
BLOG = "https://blog.tristanhotham.com/2026/10/31/tsunamis/"          # filled in by the publisher
NCEI_DOI = "10.7289/V5PN93H7"
NCEI_URL = "https://www.ncei.noaa.gov/products/natural-hazards/tsunamis-earthquakes-volcanoes/tsunamis"
API_URL = "https://www.ngdc.noaa.gov/hazel/hazard-service/api/v1/"
FETCHED = "2026"                # fetched 2 November 2026; year only in public copy
AI = ("I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped "
      "prepare the analysis code. I reviewed and checked all text and results.")
LAST_YEAR = 2026               # the database runs to autumn 2026: the last year is partial

VALIDITY = {4: "Definite tsunami", 3: "Probable tsunami", 2: "Questionable tsunami", 1: "Very doubtful tsunami",
            0: "Seiche or disturbance in an inland river or lake only", -1: "Erroneous entry"}
CAUSE = {0: "Unknown", 1: "Earthquake", 2: "Questionable earthquake", 3: "Earthquake and landslide", 4: "Volcano and earthquake",
         5: "Volcano, earthquake and landslide", 6: "Volcano", 7: "Volcano and landslide", 8: "Landslide", 9: "Meteorological",
         10: "Explosion", 11: "Astronomical tide"}
# cause groups for maps and charts. Order = legend and stack order.
GROUPS = [("Earthquake", "#D9822B"), ("Earthquake and landslide", "#9C4F2E"), ("Volcano", "#C8322B"), ("Landslide", "#7B57A8"),
          ("Meteorological", "#2E9A8C"), ("Explosion", "#3B3B3B"), ("Unknown", "#A79F94")]
CAUSE_GROUP = {1: "Earthquake", 2: "Earthquake", 3: "Earthquake and landslide", 4: "Volcano", 5: "Volcano", 6: "Volcano", 7: "Volcano",
               8: "Landslide", 9: "Meteorological", 10: "Explosion", 11: "Unknown", 0: "Unknown"}
GN = [g for g, _ in GROUPS]; GCOL = dict(GROUPS)

OCEANS = [("Pacific", range(80, 90)), ("Indian Ocean", [60]), ("Atlantic and Caribbean", range(70, 78)), ("Mediterranean", [50]),
          ("Black Sea and Caspian", [40]), ("Red Sea and Persian Gulf", [30]), ("Inland Africa", [78])]
REGION_OCEAN = {c: o for o, cs in OCEANS for c in cs}
RING = set(range(81, 90))      # the rim of the Pacific (Ring of Fire); 80 (Hawaii) is mid-plate and left out
REGION = {30: "Red Sea and Persian Gulf", 40: "Black Sea and Caspian Sea", 50: "Mediterranean", 60: "Indian Ocean (with Sumatra and Java)",
          70: "Southeast Atlantic", 71: "Southwest Atlantic", 72: "Northwest Atlantic and Greenland", 73: "Northeast Atlantic",
          74: "Caribbean", 75: "East coast of North America", 76: "Gulf of Mexico", 77: "West coast of Africa", 78: "Central Africa",
          80: "Hawaii", 81: "New Zealand, eastern Australia and the South Pacific islands", 82: "New Guinea, Solomon Islands, Vanuatu, New Caledonia",
          83: "Eastern Indonesia", 84: "China, Korea, Philippines, Taiwan", 85: "Japan", 86: "Kamchatka and the Kuril Islands",
          87: "Alaska and the Aleutians", 88: "Pacific coast of North and Central America", 89: "Pacific coast of South America"}

# runup height classes (m) for dots and lines: upper bounds and colours (water: pale to deep blue)
HT_BINS = [(0.5, "#A9D3E8"), (2, "#6FB2D9"), (5, "#3D8BC4"), (10, "#2763A6"), (30, "#173F80"), (1e9, "#0A1F4F")]
HT_LABELS = ["under 0.5 m", "0.5 to 2 m", "2 to 5 m", "5 to 10 m", "10 to 30 m", "over 30 m"]

COUNTRY_FIX = {"USA": "United States", "USA TERRITORY": "US territories", "UK": "United Kingdom", "UK TERRITORY": "UK territories",
               "MYANMAR (BURMA)": "Myanmar", "NAOERO": "Nauru", "HOLLAND": "Netherlands", "UAE": "United Arab Emirates",
               "MICRONESIA, FED. STATES OF": "Micronesia", "MARSHALL ISLANDS, REP. OF": "Marshall Islands", "KOREA": "Korea",
               "EAST TIMOR": "Timor-Leste", "AZORES (PORTUGAL)": "Azores (Portugal)", "AFRICA, NORTH COAST": "North Africa",
               "SAINT MARTIN (FRENCH AND DUTCH TERRITORIES)": "Saint Martin", "FRENCH SOUTHERN AND ANTARCTIC TERRITORIES": "French Southern Territories",
               "SCOTLAND": "United Kingdom"}
SMALL = {"and", "of", "the", "de", "la", "del", "da", "do", "on", "at", "in"}


def country(s):
    if s is None or s != s: return ""
    s = str(s).strip()
    if s in COUNTRY_FIX: return COUNTRY_FIX[s]
    s = re.sub(r"\((FRENCH|UK|DUTCH) TERRITORY\)", lambda m: "(" + {"FRENCH": "France", "UK": "UK", "DUTCH": "Netherlands"}[m.group(1)] + ")", s)
    return tcase(s)


def tcase(s):
    """NCEI upper case place names to title case, keeping state codes (AK, HI), directions (N., SE.) and roman numerals."""
    if s is None or s != s: return ""
    out = []
    for i, w in enumerate(re.split(r"(\s+|,|-|/|\()", str(s))):
        if not w or re.fullmatch(r"\s+|,|-|/|\(", w): out.append(w); continue
        core = w.strip(".)")
        if re.fullmatch(r"(N|S|E|W|NE|NW|SE|SW|NNE|ENE|ESE|SSE|SSW|WSW|WNW|NNW)\.?", w.rstrip(")")): out.append(w.upper()); continue
        if len(core) == 2 and core.isalpha() and out and "".join(out).rstrip().endswith(","): out.append(w.upper()); continue
        if re.fullmatch(r"[IVX]+", core) and len(core) > 1 or core in ("USA", "UK", "BC", "DART", "BPR", "NOAA"): out.append(w); continue
        lw = w.lower()
        out.append(lw if lw in SMALL and i > 0 else lw[:1].upper() + lw[1:])
    s = "".join(out)
    return re.sub(r"\bMc([a-z])", lambda m: "Mc" + m.group(1).upper(), s)


def yname(y):
    y = int(y)
    return f"{-y} BC" if y < 0 else (f"AD {y}" if y < 1000 else str(y))


def jload(path):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def dash(v):
    """Remove em and en dashes and double hyphens from text (house style)."""
    if isinstance(v, str):
        v = re.sub(r"(\d)\s*[–—]\s*(\d)", r"\1 to \2", v)
        v = v.replace(" — ", ", ").replace("—", ", ").replace(" – ", ", ").replace("–", "-")
        while "--" in v:
            v = v.replace("--", "-")
        return v
    if isinstance(v, list):
        return [dash(x) for x in v]
    if isinstance(v, dict):
        return {k: dash(x) for k, x in v.items()}
    return v


def jsave(obj, path, indent=None):
    if os.path.abspath(path).startswith(DATA):
        obj = dash(obj)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=indent, separators=None if indent else (",", ":"))


def norm(s):
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(ch for ch in s if not unicodedata.combining(ch)).lower()
    return re.sub(r"[\W_]+", " ", s).strip()


def get(R, path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f=None):
    if f is None or f == "raw": return str(v)
    if f == "int": return f"{round(float(v)):,}"
    if f == "pc": return f"{round(float(v))}%"
    if f == "pc1": return f"{float(v):.1f}%"
    if f == "f1": return f"{float(v):.1f}"
    if f == "f2": return f"{float(v):.2f}"
    if f == "k": return f"{float(v) / 1000:.1f}"
    if f == "yr": return yname(v)
    raise ValueError(f)


def fill(text, R, f=fmt):
    """Replace {{path|format}} tokens with numbers from R, leaving the publisher's tokens (10.5281/zenodo.23873531, https://doi.org/10.5281/zenodo.23873531, https://blog.tristanhotham.com/2026/10/31/tsunamis/),
    image tokens ({{IMG|...}}) and table tokens ({{TABLE_...}}) alone."""
    return re.sub(r"\{\{(?!IMG\||DOI\}\}|DOI_URL\}\}|BLOG_URL\}\}|TABLE_)([^}|]+)(\|(\w+))?\}\}", lambda m: f(get(R, m.group(1)), m.group(3)), text)
