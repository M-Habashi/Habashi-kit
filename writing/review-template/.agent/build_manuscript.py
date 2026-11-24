"""Starter manuscript builder for the Habashi-kit/writing review page.

Edit TITLE, SUBTITLE, the manuscript sections, and REFS below, then run:
    python .agent/build_manuscript.py "short note about this revision"

A new version is appended to .agent/manuscript_versions.js whenever the article changes.
Optional: `pip install latex2mathml` for MathML equations (falls back to plain text if absent).
"""
import datetime
import html
import json
import os
import re
import sys
from urllib.parse import quote_plus

try:
    from latex2mathml.converter import convert as _convert_mml
except ImportError:
    _convert_mml = None

TITLE = "Your Manuscript Title"
SUBTITLE = "Manuscript Draft"

ARGMIN_BAD = '<mo /><mrow><mi>a</mi><mi>r</mi><mi>g</mi><mspace width="0.167em" /><mi>m</mi><mi>i</mi><mi>n</mi></mrow>'


def mml(tex, block=False):
    if _convert_mml is None:
        tag = "div" if block else "span"
        return f'<{tag} class="math-fallback">{html.escape(tex)}</{tag}>'
    m = _convert_mml(tex, display="block" if block else "inline")
    return m.replace(ARGMIN_BAD, "<mo>arg&#x2009;min</mo>")


EQ = {}    # key -> equation number
WORD = {}  # "eqN" -> UnicodeMath / plain text for Word copy


def eq(key, tex, word=""):
    n = len(EQ) + 1
    EQ[key] = n
    WORD[f"eq{n}"] = word or tex
    return (
        f'<div class="equation" id="eq{n}"><div class="expression">{mml(tex, True)}</div>'
        f'<span class="eqno">({n})</span></div>'
    )


def ref(k):
    return f'Equation <a href="#eq{EQ[k]}">({EQ[k]})</a>'


def inline(text):
    return re.sub(r"\$(.+?)\$", lambda m: mml(m.group(1)), text)


def trow(cells, tag="td"):
    return "<tr>" + "".join(f"<{tag}>{inline(c)}</{tag}>" for c in cells) + "</tr>"


parts = []
P = lambda t: parts.append(f"<p>{inline(t)}</p>")
H1 = lambda num, t, id_: parts.append(f'<h1 id="{id_}"><span class="secno">{num}</span>{t}</h1>')
H2 = lambda num, t, id_: parts.append(f'<h2 id="{id_}"><span class="secno">{num}</span>{t}</h2>')
E = lambda *a: parts.append(eq(*a))
RAW = parts.append

# ---------------------------------------------------------------- content (replace with your paper)

RAW('<h1 id="abstract">Abstract</h1>')
P(
    "Replace this placeholder abstract with a concise 9–12 sentence summary of your study: "
    "broader context, specific problem, research gap, aims, method, validation type, key quantitative "
    "results, and practical significance."
)

H1("1", "Introduction", "sec1")
P(
    "Open with the broader motivation and limitation of existing approaches, citing the oldest "
    "original sources {citep:sample2020}. Narrow to the specific technical problem, group prior "
    "literature by role, state the gap explicitly, and close with your main contributions and roadmap."
)

H1("2", "Methodology", "sec2")
P(
    "Present the formulation, experimental or computational setup, and evaluation criteria. "
    "Inline math like $y(t)$ and numbered equations such as {eq:sample_eq} render automatically:"
)
E("sample_eq", r"y(t) = \alpha\,x(t) + \beta,", "y(t) = α x(t) + β,")
P(
    "where $x(t)$ is the input, $y(t)$ is the response, and $\\alpha$ and $\\beta$ are model "
    "parameters summarized in Table 1."
)
RAW(
    '<figure class="table" id="tab1"><figcaption><b>Table 1.</b> Example parameter table.</figcaption>'
    "<table><thead>"
    + trow(["Symbol", "Value", "Description"], "th")
    + "</thead><tbody>"
    + "".join(
        trow(r)
        for r in [
            ("$\\alpha$", "1.0", "Scale parameter"),
            ("$\\beta$", "0.0", "Offset parameter"),
        ]
    )
    + "</tbody></table></figure>"
)

H1("3", "Results and discussion", "sec3")
P(
    "Open each results subsection with what was applied and expected before reporting outcomes. "
    "Describe every figure in text before inserting its `<figure>` block."
)

H1("4", "Conclusions", "sec4")
P(
    "Open directly with this study's verified contributions, summarize core outcomes and tradeoffs "
    "concisely, state the demonstrated significance, and close neutrally on scope and open future work."
)

# ---------------------------------------------------------------- references
# key -> (in-text name, year, formatted citation). Cite as {citet:key} "Name [n]" or {citep:key} "[n]".
REFS = {
    "sample2020": (
        "Author et al.",
        "2020",
        "Author, A., Coauthor, B., and Coauthor, C. (2020), “Replace with a verified original reference,” "
        "<i>Journal Name</i>, 10(1), 1–15. DOI: 10.0000/example.2020.0001",
    ),
}

# ---------------------------------------------------------------- build
body = "\n".join(parts)
ARTICLE = f"""
{body}
<section class="references" aria-labelledby="refs"><h2 id="refs">References</h2><ol>
{{REFS}}
</ol></section>
"""

CITED = []


def cite(m):
    keys = m.group(2).split(",")
    for k in keys:
        if k not in CITED:
            CITED.append(k)
    nums = "[" + ", ".join(f'<a class="cite" href="#ref-{k}">{CITED.index(k) + 1}</a>' for k in keys) + "]"
    return (" and ".join(REFS[k][0] for k in keys) + " " + nums) if m.group(1) == "t" else nums


ARTICLE = re.sub(r"\{eq:([A-Za-z0-9_]+)\}", lambda m: ref(m.group(1)), ARTICLE)
ARTICLE = re.sub(r"\{n:(\w+)\}", lambda m: str(EQ[m.group(1)]), ARTICLE)
ARTICLE = re.sub(r"\{cite([tp]):([a-z0-9_,]+)\}", cite, ARTICLE)


def scholar(t):
    m = re.search(r"“(.+?)(,?)”|<i>(.+?)</i>", t)
    if not m:
        return t
    title = m.group(1) or m.group(3)
    a = (
        f'<a href="https://scholar.google.com/scholar?q={quote_plus(re.sub("<[^>]+>", "", title))}" '
        f'target="_blank" rel="noopener">{title}</a>'
    )
    return t.replace(m.group(0), f"“{a}{m.group(2)}”" if m.group(1) else f"<i>{a}</i>", 1)


ARTICLE = ARTICLE.replace("{REFS}", "\n".join(f'<li id="ref-{k}">{scholar(REFS[k][2])}</li>' for k in CITED))

if "--preview" in sys.argv:
    open(sys.argv[sys.argv.index("--preview") + 1], "w", encoding="utf-8").write(ARTICLE)
    sys.exit()

HERE = os.path.dirname(os.path.abspath(__file__))
VERS = os.path.join(HERE, "manuscript_versions.js")
HEAD = "window.MANUSCRIPT_VERSIONS = "
if os.path.exists(VERS):
    versions = json.loads(open(VERS, encoding="utf-8").readline()[len(HEAD):].rstrip().rstrip(";"))
else:
    versions = [
        {
            "v": 0,
            "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "note": "Initial template draft",
            "html": ARTICLE,
        }
    ]
    print("initialized version 0")

args = [a for a in sys.argv[1:] if not a.startswith("--")]
if versions[-1].get("author") == "user" and versions[-1]["html"] != ARTICLE and "--merged" not in sys.argv:
    sys.exit(
        f"v{versions[-1]['v']} holds edits made in the review page. Port them into this script, "
        "then rerun with --merged."
    )
if versions[-1]["html"] != ARTICLE:
    versions.append(
        {
            "v": versions[-1]["v"] + 1,
            "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "note": args[0] if args else "",
            "html": ARTICLE,
        }
    )
    print("saved version", versions[-1]["v"])

DRAFT = os.path.join(HERE, "manuscript_draft.json")
base = json.load(open(DRAFT, encoding="utf-8"))["base"] if os.path.exists(DRAFT) else None
versions = [v for v in versions[:-10] if v["v"] == base] + versions[-10:]

meta = {"title": TITLE, "subtitle": SUBTITLE}
with open(VERS, "w", encoding="utf-8") as f:
    f.write(HEAD + json.dumps(versions, ensure_ascii=False) + ";\n")
    f.write("window.MANUSCRIPT_WORD = " + json.dumps(WORD, ensure_ascii=False) + ";\n")
    f.write("window.MANUSCRIPT_META = " + json.dumps(meta, ensure_ascii=False) + ";\n")

print(len(EQ), "equations,", len(versions), "versions")
