"""Find, with no AI, which approval matrix row each change in a contract falls under.

ACME's standard agreement is built from named places: the Key Terms fields on the cover page ("General Cap
Amount") and the headed paragraphs of the Standard Terms ("Payment", "Liability Cap"), grouped under group
headings ("Payment & Taxes"). The Word file carries no section numbers, so the headings are the keys. Each
matrix row lists, in its `Contract location` column, the places where its term is defined:

    Key Terms > General Cap Amount        a cover page field
    Payment & Taxes > Payment             a headed paragraph, as Group > Heading
    New: Service Levels                   a heading the customer is expected to ADD (the standard has no such place)

Where two matrix rows share a place (the Payment paragraph holds both payment days and billing frequency),
each lists words in its `Keywords` column and the changed text decides. If that cannot decide, the change is
"ambiguous" and the AI may choose only among the rows that claim the place. A change in a place no row
claims is "unlocated": it goes to the matrix owner as not in the matrix.
"""
import csv
import re
from pathlib import Path

NOT_A_HEADING = re.compile(r"\b(must|will|shall|may|is|are)\b", re.I)
LEAD = re.compile(r"^([A-Z][^.:;]{0,70}?)\.(?:\s|$)")
QUOTED = re.compile(r"^[“\"']([^”\"']+)[”\"']")
PLACEHOLDER = re.compile(r"\[[^\]]{2,60}\]")


def norm(s):
    """Comparable form of a heading or path: lower case, hyphens as spaces ("Most-Favored" is "Most Favored")."""
    return re.sub(r"\s*>\s*", " > ", re.sub(r"[\s\-\u2010\u2011\u2013]+", " ", str(s))).strip().lower()


def _short(p):
    return 0 < len(p.split()) <= 5 and not p.rstrip().endswith((".", ":", ";", ","))


def _heading(p):
    m = LEAD.match(p)
    if not m:
        return ""
    h = m.group(1).strip()
    return h if len(h.split()) <= 7 and not NOT_A_HEADING.search(h) else ""


def outline(paras):
    """For each paragraph: {"path": "Group > Heading" or "", "heading": "Heading" or ""}."""
    out, region, group, head = [], None, "", ""
    for i, p in enumerate(paras):
        nxt = paras[i + 1] if i + 1 < len(paras) else ""
        info = {"path": "", "heading": ""}
        if p == "Key Terms":
            region, group, head = "key", "Key Terms", ""
        elif p.startswith("PROVIDER:") or p.startswith("Provider and Customer have not changed"):
            region, group, head = None, "", ""
        elif p == "Standard Terms":
            region, group, head = "terms", "", ""
        elif region == "key":
            if _short(p) and (len(nxt.split()) > 5 or nxt.rstrip().endswith(".")):
                head = p
            if head:
                info = {"path": f"{group} > {head}", "heading": head}
        elif region == "terms":
            lead = _heading(p)
            if _short(p) and not lead:
                group, head = p.strip(), ""
                info = {"path": group, "heading": ""}
            else:
                if group == "Definitions":
                    q = QUOTED.match(p)
                    head = q.group(1) if q else head
                elif lead:
                    head = lead
                info = {"path": f"{group} > {head}" if head else group, "heading": lead}
        out.append(info)
    return out


def read_rows(matrix):
    """The matrix rows with their locations and keywords parsed."""
    rows = []
    with open(Path(matrix) / "doa_matrix.csv", newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            refs, new = set(), set()
            for part in re.split(r"\s*;\s*", r.get("Contract location", "") or ""):
                if not part.strip():
                    continue
                if part.lower().startswith("new:"):
                    new.add(norm(part[4:]))
                else:
                    refs.add(norm(part))
            kws = [k.strip().lower() for k in re.split(r"\s*;\s*", r.get("Keywords", "") or "") if k.strip()]
            rows.append({"term": r["Term"], "row": r, "refs": refs, "new": new, "keywords": kws})
    return rows


def placeholder_fill(d):
    """A change that only fills in a bracketed blank of the standard, such as the customer's legal name."""
    if d["kind"] != "Changed" or not PLACEHOLDER.search(d["baseline"]):
        return False
    pat = "".join(".+?" if PLACEHOLDER.fullmatch(t) else re.escape(t) for t in re.split(r"(\[[^\]]{2,60}\])", d["baseline"]) if t)
    return bool(re.fullmatch(pat, d["other"], re.S))


def locate(diffs, standard_paras, other_paras, matrix):
    """Number each difference D1, D2, ... and say where it falls. Returns the list of deviations."""
    so, oo = outline(standard_paras), outline(other_paras)
    known = {norm(o["heading"]) for o in so if o["heading"]}
    rows = read_rows(matrix)
    out = []
    for n, d in enumerate(diffs, 1):
        refs, new = [], []
        for i in d["base_paras"]:
            if i < len(so) and so[i]["path"]:
                refs.append(so[i]["path"])
        for j in d["other_paras"]:
            if j < len(oo):
                if oo[j]["path"]:
                    refs.append(oo[j]["path"])
                if oo[j]["heading"] and norm(oo[j]["heading"]) not in known:
                    new.append(oo[j]["heading"])
        refs = list(dict.fromkeys(refs))
        keys = {norm(r) for r in refs}
        newkeys = {norm(h) for h in new}
        where = ("New section: " + new[0]) if new and d["kind"] == "Added" else (refs[0] if refs else "(outside any headed place)")
        dev = {"id": f"D{n}", "kind": d["kind"], "baseline": d["baseline"], "other": d["other"], "where": where, "rows": [], "how": ""}
        if placeholder_fill(d):
            dev.update(status="placeholder", how="fills a blank of the standard")
            out.append(dev)
            continue
        cands = [r for r in rows if (r["refs"] & keys) or (r["new"] & newkeys)]
        if len(cands) > 1:
            text = (d["other"] or d["baseline"]).lower()  # the new wording decides; for a removal, the removed words
            hit = [r for r in cands if any(k in text for k in r["keywords"])]
            if len(hit) == 1:
                cands, dev["how"] = hit, "contract location and keywords"
            elif hit:
                cands = hit
        elif cands:
            dev["how"] = "contract location"
        dev["rows"] = [r["term"] for r in cands]
        dev["status"] = "unlocated" if not cands else ("located" if len(cands) == 1 else "ambiguous")
        out.append(dev)
    return out


def matrix_problems(matrix, standard_paras):
    """What is wrong with the matrix's location columns, in plain words. Empty when it is sound."""
    rows = read_rows(matrix)
    with open(Path(matrix) / "doa_matrix.csv", newline="", encoding="utf-8") as f:
        cols = csv.DictReader(f).fieldnames or []
    if "Contract location" not in cols:
        return ["doa_matrix.csv has no 'Contract location' column, so changes cannot be placed in the matrix."]
    paths = {norm(o["path"]) for o in outline(standard_paras) if o["path"]}
    out, owner = [], {}
    for r in rows:
        for ref in sorted(r["refs"]):
            if ref not in paths:
                out.append(f"'{r['term']}': '{ref}' is not a place in the standard agreement. Check the heading, spelled as Group > Heading.")
            owner.setdefault(ref, []).append(r)
        for ref in sorted(r["new"]):
            if ref in {norm(o["heading"]) for o in outline(standard_paras) if o["heading"]}:
                out.append(f"'{r['term']}': 'New: {ref}' already exists in the standard. Use its Group > Heading instead.")
    for ref, rs in owner.items():
        if len(rs) > 1:
            if any(not x["keywords"] for x in rs):
                out.append(f"'{ref}' is claimed by {', '.join(x['term'] for x in rs)}. Each of them needs Keywords, so a change there can be told apart.")
            else:
                seen = {}
                for x in rs:
                    for k in x["keywords"]:
                        seen.setdefault(k, []).append(x["term"])
                for k, ts in seen.items():
                    if len(ts) > 1:
                        out.append(f"Keyword '{k}' is used by both {' and '.join(ts)} for '{ref}'. Keywords must tell the rows apart.")
    return out


def unclaimed(matrix, standard_paras):
    """Places in the standard that no matrix row claims. A change there goes to the matrix owner as not in the matrix.
    Group headings and defined terms are left out; the owner can still claim them."""
    claimed = set()
    for r in read_rows(matrix):
        claimed |= r["refs"]
    seen = []
    for o in outline(standard_paras):
        p = o["path"]
        if p and " > " in p and not p.startswith("Definitions") and norm(p) not in claimed and p not in seen:
            seen.append(p)
    return seen
