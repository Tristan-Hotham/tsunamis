"""Build the paper: fill code/paper_template.tex from data/results.json, add tables, compile with xelatex.
Output: release/paper/<NAME>.pdf and .tex (figures f_*.png sit beside them). The DOI stays as the 10.5281/zenodo.23873531 placeholder.
Needs only data/ and the figures."""
import subprocess
from common import *

R = jload(f"{DATA}/results.json")
OUT = os.path.join(ROOT, "release", "paper"); NAME = "Hotham_Every_Tsunami_on_Record"
tex = lambda s: str(s).replace("\\", "").replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#").replace("$", "\\$")

# statements made in words in the paper only
assert R["deadliest"][0]["deaths"] > R["deaths"]["since1900"] - R["deadliest"][0]["deaths"]          # 2004 > all others since 1900 combined
assert R["ring"]["with_sunda_pct"] - R["ring"]["pct"] < 5                                               # "a few points"
assert R["highest"][2]["year"] == 1980 and "Spirit Lake" in R["highest"][2]["place"] and R["highest"][3]["year"] == 1963 and R["highest"][4]["year"] == 2023
assert R["oceans"]["Atlantic and Caribbean"]["deaths"] > 0 and 50000 / R["oceans"]["Atlantic and Caribbean"]["deaths"] > .5   # "mostly Lisbon"
assert R["atm"]["tonga"] + R["atm"]["krakatau"] == R["atm"]["n"]


def tfmt(v, f):
    if f == "int": return f"{int(round(float(v))):,}"
    if f == "pc": return f"{round(float(v))}\\%"
    if f == "pc1": return f"{float(v):.1f}\\%"
    if f == "f1": return f"{float(v):.1f}"
    if f == "f2": return f"{float(v):.2f}"
    if f == "yr": return yname(v)
    return tex(str(v))


n = lambda v: "" if v is None else f"{v:,.0f}"
hrs = lambda v: "" if v is None else f"{v:.1f}"
rows = "".join(f"{c} & {tex(CAUSE[c])} & {tex(CAUSE_GROUP[c])} & {R['cause_codes'].get(CAUSE[c], 0):,}\\\\\n" for c in sorted(CAUSE))
TC = ("\\begin{table}[tbp]\\centering\\small\\caption{Definite and probable tsunamis by NCEI cause code, and the groups used here.}\\label{tab:causes}"
      "\\begin{tabular}{rllr}\\toprule Code & NCEI cause & Group & Tsunamis\\\\\\midrule\n" + rows + f"\\midrule & All & & {R['source']['n']:,}\\\\\\bottomrule\\end{{tabular}}\\end{{table}}")
rows = "".join(f"{tex(d['place'])} & {tex(d['yname'])} & {tex(d['country'])} & {tex(d['group'])} & {d['mag'] if d['mag'] else ''} & {n(d['deaths'])} & {n(d['deaths_total'])}\\\\\n" for d in R["deadliest"][:12])
TD = ("\\begin{table}[tbp]\\centering\\footnotesize\\setlength{\\tabcolsep}{4pt}\\caption{The twelve deadliest tsunamis: NCEI's tsunami deaths and its total for the whole event (including the earthquake or eruption).}\\label{tab:deaths}"
      "\\begin{tabular}{lllllrr}\\toprule Source & Year & Country & Cause & Mag. & Tsunami deaths & Whole event\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
rows = "".join(f"{tex(h['place'])} & {tex(h['yname'])} & {tex(h['country'])} & {tex(h['group'])} & {h['ht']:.1f}\\\\\n" for h in R["highest"][:12])
TH = ("\\begin{table}[tbp]\\centering\\footnotesize\\caption{The highest runup recorded for each tsunami: the top twelve.}\\label{tab:highest}"
      "\\begin{tabular}{llllr}\\toprule Place & Year & Country & Cause & Metres\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
rows = "".join(f"{tex(f['event'])}, {tex(f['yname'])} & {tex(f['place'])}, {tex(f['rcountry'])} & {f['dist']:,.0f} & {f['ht']:.2f} & {hrs(f['trav'])}\\\\\n" for f in R["farthest"][:10])
TF = ("\\begin{table}[tbp]\\centering\\footnotesize\\setlength{\\tabcolsep}{4pt}\\caption{The farthest place where each tsunami's water was measured (sea waves only, height above zero): the top ten.}\\label{tab:far}"
      "\\begin{tabular}{llrrr}\\toprule Tsunami & Farthest place & km & Metres & Hours\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
t = open(os.path.join(ROOT, "code", "paper_template.tex"), encoding="utf-8").read()
for k in ("page", "repo", "api"):
    t = t.replace("\\url{{{meta.%s}}}" % k, "\\url{%s}" % R["meta"][k])
t = t.replace("\\href{https://doi.org/{{meta.doi}}}{https://doi.org/{{meta.doi}}}", "https://doi.org/\\{\\{DOI\\}\\}")
t = t.replace("\\url{https://doi.org/{{meta.doi}}}", "https://doi.org/\\{\\{DOI\\}\\}")
t = fill(t, R, f=lambda v, f: tfmt(v, f or "raw"))
for k, v in (("CAUSES", TC), ("DEATHS", TD), ("HIGHEST", TH), ("FAR", TF)):
    t = t.replace("{{TABLE_%s}}" % k, v)
assert "{{" not in t and "--" not in t and "\u2014" not in t and "\u2013" not in t, re.findall(r"\{\{[^}]*\}\}", t)[:4]
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, NAME + ".tex"), "w", encoding="utf-8").write(t)
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"], cwd=OUT, capture_output=True, text=True)
log = open(os.path.join(OUT, NAME + ".log"), encoding="utf-8", errors="ignore").read()
print([l for l in log.splitlines() if "Missing character" in l or "undefined" in l.lower() or "Overfull" in l][:12])
for ext in (".aux", ".log", ".out"):
    q = os.path.join(OUT, NAME + ext)
    if os.path.exists(q): os.remove(q)
txt = subprocess.run(["pdftotext", os.path.join(OUT, NAME + ".pdf"), "-"], capture_output=True, text=True).stdout
pages = subprocess.run(["pdfinfo", os.path.join(OUT, NAME + ".pdf")], capture_output=True, text=True).stdout
for bad in ("DSIT", "DCMS", "civil serv"):
    assert bad not in txt
print("paper", r.returncode, len(txt.split()), "words;", [l for l in pages.splitlines() if l.startswith("Pages")], "dashes:", txt.count("\u2014") + txt.count("\u2013") + txt.count("--"))
