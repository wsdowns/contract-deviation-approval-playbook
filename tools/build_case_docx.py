"""Build the staged example redlines: ACME's standard agreement (Word) with tracked changes by a fictional customer.

Each case is a real Word file with insertions and deletions marked as tracked changes, so the app reads it exactly
as it reads a redline from a customer. Run this to rebuild Cases 2 and 3 (Case 1's file was made by hand):

    python tools/build_case_docx.py

Nothing here is a real customer. Every name and figure is invented.

In every operation, `key` is any unique stretch of the paragraph's ORIGINAL text. Edits are tracked, so a paragraph
can be edited more than once: the offsets are always taken from the original runs that are still in place.
"""
import copy
import io
import zipfile
from pathlib import Path

from lxml import etree

ROOT = Path(__file__).resolve().parents[1]
EX = ROOT / "examples" / "acme-saas"
STANDARD = EX / "contracts" / "ACME_SaaS_Agreement_v1.0.docx"
NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W = "{%s}" % NS
XML_SPACE = "{http://www.w3.org/XML/1998/namespace}space"


class Redline:
    def __init__(self, data, author, date):
        self.data = data
        self.root = etree.fromstring(zipfile.ZipFile(io.BytesIO(data)).read("word/document.xml"))
        self.author, self.date, self._id = author, date, 9000

    # ---------------------------------------------------------------- reading
    def _runs(self, p):
        """The paragraph's own runs that are still plain text: not yet inside a tracked insertion or deletion."""
        return [r for r in p.findall(W + "r") if r.find(W + "t") is not None]

    @staticmethod
    def _run_text(r):
        return "".join(t.text or "" for t in r.findall(W + "t"))

    def text(self, p):
        return "".join(self._run_text(r) for r in self._runs(p))

    def find(self, key):
        for p in self.root.iter(W + "p"):
            if key in self.text(p):
                return p
        raise LookupError(f"paragraph not found: {key}")

    # ---------------------------------------------------------------- building blocks
    def _mark(self, tag):
        self._id += 1
        el = etree.Element(W + tag)
        el.set(W + "id", str(self._id))
        el.set(W + "author", self.author)
        el.set(W + "date", self.date)
        return el

    @staticmethod
    def _set_text(r, text, tag="t"):
        for t in r.findall(W + "t"):
            r.remove(t)
        t = etree.SubElement(r, W + tag)
        t.text = text
        t.set(XML_SPACE, "preserve")

    def _new_run(self, like, text):
        r = etree.Element(W + "r")
        rpr = like.find(W + "rPr") if like is not None else None
        if rpr is not None:
            r.append(copy.deepcopy(rpr))
        self._set_text(r, text)
        return r

    def _split(self, p, offset):
        """Put a run boundary at this character offset. Returns the run that starts there, or None at the end of the paragraph."""
        pos = 0
        for r in self._runs(p):
            t = self._run_text(r)
            if pos == offset:
                return r
            if pos < offset < pos + len(t):
                right = copy.deepcopy(r)
                self._set_text(r, t[: offset - pos])
                self._set_text(right, t[offset - pos:])
                r.addnext(right)
                return right
            pos += len(t)
        return None

    # ---------------------------------------------------------------- operations
    def replace(self, key, old, new):
        """Track the deletion of `old` and, after it, the insertion of `new`."""
        p = self.find(key)
        a = self.text(p).index(old)
        self._split(p, a)
        self._split(p, a + len(old))
        pos, inside = 0, []
        for r in self._runs(p):
            n = len(self._run_text(r))
            if a <= pos < a + len(old) and n:
                inside.append(r)
            pos += n
        last = None
        for r in inside:
            d = self._mark("del")
            r.addprevious(d)
            d.append(r)
            self._set_text(r, self._run_text(r) or "".join(t.text or "" for t in r.findall(W + "t")), "delText")
            last = d
        if new:
            ins = self._mark("ins")
            ins.append(self._new_run(inside[-1], new))
            last.addnext(ins)

    def insert_after(self, key, anchor, new):
        """Track the insertion of `new` right after the words `anchor`."""
        p = self.find(key)
        at = self.text(p).index(anchor) + len(anchor)
        following = self._split(p, at)
        runs = self._runs(p)
        like = runs[-1] if following is None else runs[max(0, runs.index(following) - 1)]
        ins = self._mark("ins")
        ins.append(self._new_run(like, new))
        if following is None:
            runs[-1].addnext(ins)
        else:
            following.addprevious(ins)

    def new_paragraph_after(self, key, heading, body):
        """A whole new paragraph as one tracked insertion, shaped like the headed paragraphs around it."""
        anchor = self.find(key)
        model = self.find("Customer will pay Provider Fees and taxes")  # a headed paragraph: underlined heading, then body text
        runs = self._runs(model)
        p = etree.Element(W + "p")
        ppr = copy.deepcopy(model.find(W + "pPr"))
        rpr = ppr.find(W + "rPr")
        if rpr is None:
            rpr = etree.SubElement(ppr, W + "rPr")
        rpr.insert(0, self._mark("ins"))
        p.append(ppr)
        ins = self._mark("ins")
        ins.append(self._new_run(runs[0], heading))
        ins.append(self._new_run(runs[1], ".  "))
        ins.append(self._new_run(runs[2], body))
        p.append(ins)
        anchor.addnext(p)

    def save(self, out):
        src = zipfile.ZipFile(io.BytesIO(self.data))
        xml = etree.tostring(self.root, xml_declaration=True, encoding="UTF-8", standalone=True)
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
            for item in src.infolist():
                z.writestr(item, xml if item.filename == "word/document.xml" else src.read(item.filename))


def case2():
    """Lakeshore Health: a large strategic deal, six asks."""
    r = Redline(STANDARD.read_bytes(), "Lakeshore Health, Inc. counsel", "2026-03-02T09:00:00Z")
    r.replace("This Software as a Service Agreement", "[Customer legal name]", "Lakeshore Health, Inc.")
    r.replace("The laws of the State of", "Delaware", "Illinois")
    r.replace("The state and federal courts located in", "New Castle County, Delaware", "Cook County, Illinois")
    r.replace("Fees paid or payable by Customer to Provider in the 12 month", "1x", "The greater of (a) 3x")
    r.replace("Fees paid or payable by Customer to Provider in the 12 month", "before the claim.", "before the claim and (b) $5,000,000.")
    r.insert_after("annually updated SOC 2", "subject to Section 10 (Confidentiality).",
                   " Provider will also hold HITRUST CSF certification throughout the Subscription Period and will give Customer its current certification letter on request.")
    r.new_paragraph_after("Payment Dispute.", "Most-Favored Customer Pricing",
                          "Provider represents that the Fees are no higher than the fees Provider charges any other customer for substantially similar subscriptions of comparable size and term. "
                          "If Provider offers lower fees to any such customer during the Subscription Period, Provider will promptly reduce Customer's Fees to match, from the date of that offer.")
    r.new_paragraph_after("Each Recipient may retain Discloser", "Termination for Convenience",
                          "Customer may terminate the Framework Terms or any Order Form at any time, for any reason, on 60 days' notice to Provider. "
                          "Provider will refund the prepaid Fees for the period after the termination date within 30 days after termination.")
    r.new_paragraph_after("Provider Warranty Remedy.", "Data Location", "Provider will store Customer Content only on servers located in the United States.")
    return r


def case3():
    """Summit Ridge Manufacturing: a mid-market deal with some executive-level asks."""
    r = Redline(STANDARD.read_bytes(), "Summit Ridge Manufacturing, Inc. counsel", "2026-03-16T09:00:00Z")
    r.replace("This Software as a Service Agreement", "[Customer legal name]", "Summit Ridge Manufacturing, Inc.")
    r.insert_after("Provider Covered Claims:", "other proprietary rights", ", or that is made by a third party and results from Provider's violation of Applicable Laws")
    r.replace("the following claims are not subject to the General Cap Amount", "and (b)", "(b)")
    r.insert_after("the following claims are not subject to the General Cap Amount", "indemnification obligation", "; and (c) a party's gross negligence or willful misconduct")
    r.replace("Provider will carry", "$5,000,000", "$10,000,000")
    r.new_paragraph_after("Customer Content.  Provider may copy", "Service Levels",
                          "Provider will make the Product available at least 99.5% of the time in each calendar month. If availability in a month is below 99.5%, Provider will credit Customer up to 25% of the Fees for that month. "
                          "If availability is below 99.5% in any 3 months of a rolling 6-month period, Customer may terminate the affected Order Form on notice to Provider. "
                          "Except for that termination right, credits are Customer's sole remedy for the shortfall.")
    r.insert_after("Customer will pay Provider Fees and taxes", "according to the payment terms in the Order Form.", " Provider will invoice Fees quarterly in advance.")
    return r


OUT = {
    "case-2-lakeshore-paper": ("Lakeshore_Redline_of_ACME_SaaS_Agreement.docx", case2),
    "case-3-acme-redline-2": ("SummitRidge_Redline_of_ACME_SaaS_Agreement.docx", case3),
}

if __name__ == "__main__":
    for folder, (name, build) in OUT.items():
        dest = EX / "cases" / folder / "inputs" / name
        build().save(dest)
        print("wrote", dest.relative_to(ROOT))
