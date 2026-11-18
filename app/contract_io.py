"""Read an uploaded contract and compare it with a baseline, with no AI involved.

A Word file with tracked changes gives three texts: the accepted text (insertions kept, deletions
dropped), the rejected text (what the file said before the customer's tracked edits) and a marked-up
text of only the changed paragraphs. Comparing the rejected text with the baseline finds edits the
customer made without tracking them. Standard library only, apart from pdftotext for PDFs.
"""
import difflib
import re
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
MAX_BYTES = 15 * 1024 * 1024


class ContractError(Exception):
    pass


def _walk(el, state, parts):
    for ch in el:
        tag = ch.tag
        if tag in (W + "pPr", W + "rPr"):
            continue
        if tag in (W + "ins", W + "moveTo"):
            _walk(ch, "ins", parts)
        elif tag in (W + "del", W + "moveFrom"):
            _walk(ch, "del", parts)
        elif tag == W + "r":
            for t in ch:
                if t.tag in (W + "t", W + "delText"):
                    parts.append((state, t.text or ""))
                elif t.tag in (W + "tab", W + "br"):
                    parts.append((state, " "))
        else:
            _walk(ch, state, parts)


def _paragraph(p):
    parts = []
    _walk(p, "normal", parts)
    accepted = "".join(t for s, t in parts if s != "del")
    rejected = "".join(t for s, t in parts if s != "ins")
    marked, last = [], None
    for s, t in parts:
        if not t:
            continue
        if marked and last == s:
            marked[-1] = (s, marked[-1][1] + t)
        else:
            marked.append((s, t))
        last = s
    text = "".join(f"~~{t}~~" if s == "del" else f"**{t}**" if s == "ins" else t for s, t in marked)
    return {"accepted": accepted, "rejected": rejected, "marked": text, "tracked": any(s != "normal" for s, _ in parts)}


def read_docx(data):
    try:
        with zipfile.ZipFile(__import__("io").BytesIO(data)) as z:
            root = ET.fromstring(z.read("word/document.xml"))
    except (zipfile.BadZipFile, KeyError, ET.ParseError):
        raise ContractError("That file is not a readable Word document. Save it as .docx and try again.")
    paras = [_paragraph(p) for p in root.iter(W + "p")]
    return [p for p in paras if p["accepted"].strip() or p["rejected"].strip()]


def extract(filename, data):
    """Return {kind, accepted, rejected, tracked_text, tracked_count, warnings}."""
    if len(data) > MAX_BYTES:
        raise ContractError("That file is larger than 15 MB.")
    ext = Path(filename).suffix.lower()
    warnings = []
    if ext == ".docx":
        paras = read_docx(data)
        tracked = [p for p in paras if p["tracked"]]
        kind = "docx-tracked" if tracked else "docx-clean"
        if not tracked:
            warnings.append("This Word file has no tracked changes. It will be compared with the standard to find every difference.")
        return {"kind": kind, "accepted": "\n".join(p["accepted"] for p in paras),
                "rejected": "\n".join(p["rejected"] for p in paras),
                "tracked_text": "\n\n".join(p["marked"] for p in tracked), "tracked_count": len(tracked), "warnings": warnings}
    if ext == ".pdf":
        if not shutil.which("pdftotext"):
            raise ContractError("PDF reading needs the pdftotext tool. Install poppler, or upload a Word or text file.")
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "in.pdf"
            f.write_bytes(data)
            out = subprocess.run(["pdftotext", "-layout", str(f), "-"], capture_output=True, text=True)
        if out.returncode != 0 or not out.stdout.strip():
            raise ContractError("No text could be read from that PDF. A scanned image cannot be checked; upload the Word or text version.")
        warnings.append("PDF: tracked changes and strike-through marks are lost. Ask for the Word file if you can. "
                        "Every difference from the standard is listed below instead. A PDF has no headings the program can read, "
                        "so the changes cannot be placed on the matrix automatically: upload the Word file for that.")
        return {"kind": "pdf", "accepted": out.stdout, "rejected": out.stdout, "tracked_text": "", "tracked_count": 0, "warnings": warnings}
    if ext in (".txt", ".md", ""):
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            raise ContractError("That text file is not UTF-8. Save it as UTF-8 or upload a Word file.")
        return {"kind": "text", "accepted": text, "rejected": text, "tracked_text": "", "tracked_count": 0,
                "warnings": ["Plain text carries no tracked changes and no headings the program can read, so the changes cannot be placed on the matrix automatically. Upload the Word file for that."]}
    raise ContractError(f"Upload a Word (.docx), PDF or text file, not {ext}.")


_QUOTES = str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"', "–": "-", "—": "-", " ": " "})


def paragraphs(text):
    """The non-empty paragraphs of a text, whitespace and punctuation style normalised."""
    out = []
    for para in text.split("\n"):
        para = re.sub(r"\s+", " ", para.translate(_QUOTES)).strip()
        if para:
            out.append(para)
    return out


def units_p(text):
    """Sentence-sized pieces with the number of the paragraph each came from, so layout does not count as a change."""
    out = []
    for n, para in enumerate(paragraphs(text)):
        out += [(s.strip(), n) for s in re.split(r"(?<=[.;:])\s+(?=[A-Z(\"'\d])", para) if s.strip()]
    return out


def units(text):
    return [u for u, _ in units_p(text)]


def differences(baseline, other, limit=200):
    """Every place `other` differs from `baseline`: list of {kind, baseline, other, base_paras, other_paras}.

    base_paras and other_paras are the paragraph numbers (see paragraphs()) that the changed pieces sit in."""
    ua, ub = units_p(baseline), units_p(other)
    a, ap, b, bp = [u for u, _ in ua], [n for _, n in ua], [u for u, _ in ub], [n for _, n in ub]
    out = []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if op == "equal":
            continue
        out.append({"kind": {"replace": "Changed", "delete": "Removed", "insert": "Added"}[op],
                    "baseline": " ".join(a[i1:i2]), "other": " ".join(b[j1:j2]),
                    "base_paras": sorted(set(ap[i1:i2])), "other_paras": sorted(set(bp[j1:j2]))})
    return out[:limit]


def render(diffs):
    if not diffs:
        return "None."
    lines = []
    for n, d in enumerate(diffs, 1):
        lines.append(f"{n}. {d['kind']}\n   Standard: {d['baseline'] or '(nothing)'}\n   Contract: {d['other'] or '(nothing)'}")
    return "\n".join(lines)


def analyse(filename, data, baseline_text, previous_text=None):
    """Everything the playbook needs about an uploaded contract.

    previous_text is the accepted text of the round before this one, if any. Then `since_previous` lists
    what is new this round, and the untracked check uses whichever base the customer evidently redlined:
    the standard or the previous round.
    """
    r = extract(filename, data)
    total = differences(baseline_text, r["accepted"])
    untracked, base = [], "standard"
    if r["kind"] == "docx-tracked":
        untracked = differences(baseline_text, r["rejected"])
        if previous_text is not None:
            from_prev = differences(previous_text, r["rejected"])
            if len(from_prev) < len(untracked):
                untracked, base = from_prev, "previous round"
    since = differences(previous_text, r["accepted"]) if previous_text is not None else None
    ua, ub = units(baseline_text), units(r["accepted"])
    kept = sum(b.size for b in difflib.SequenceMatcher(None, ua, ub, autojunk=False).get_matching_blocks())
    r.update(total=total, untracked=untracked, untracked_base=base, since_previous=since, similarity=kept / len(ua) if ua else 1.0)
    return r
