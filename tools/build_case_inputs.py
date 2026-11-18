"""Build the stand-in contract inputs for Cases 2 and 3 from ACME's standard agreement text.

Case 2: Lakeshore Health's own paper (a clean agreement, no redline).
Case 3: Summit Ridge Manufacturing's redline (text form, same style as Case 1).

This script makes the stand-in drafts reproducible.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EX = ROOT / "examples" / "acme-saas"
BASE = (EX / "contracts" / "ACME_SaaS_Agreement_v1.0.txt").read_text(encoding="utf-8")


def sub(text, old, new, count=1):
    """Replace `old`, ignoring how the original wraps its lines."""
    pat = r"\s+".join(re.escape(w) for w in old.split())
    out, n = re.subn(pat, lambda m: new, text, count=count)
    assert n >= 1, f"not found: {old[:60]}"
    return out


def case2():
    t = BASE
    t = sub(t, "[Customer legal name]", "Lakeshore Health, Inc.", count=0)
    t = sub(t, "The laws of the State of Delaware.", "The laws of the State of Illinois.")
    t = sub(t, "The state and federal courts located in New Castle County, Delaware.",
            "The state and federal courts located in Cook County, Illinois.")
    t = sub(t, "1x the Fees paid or payable by Customer to Provider in the 12 month period immediately before the claim.",
            "The greater of (a) 3x the Fees paid or payable by Customer to Provider in the 12 month period "
            "immediately before the claim and (b) $5,000,000.")
    t = sub(t, "subject to Section 10 (Confidentiality).",
            "subject to Section 10 (Confidentiality). Provider will also hold HITRUST CSF certification throughout "
            "the Subscription Period and will give Customer its current certification letter on request.")
    t = sub(t, "except as stated in the Key Terms above.",
            "except as stated in the Key Terms above and in Sections 4.5, 5.7 and 6.5.")
    t = sub(t, "5.         Term & Termination",
            "   4.5     Most-Favored Customer Pricing. Provider represents that the Fees are no higher than the fees Provider "
            "charges any other customer for substantially similar subscriptions of comparable size and term. If Provider offers "
            "lower fees to any such customer during the Subscription Period, Provider will promptly reduce Customer's Fees to "
            "match, from the date of that offer.\n5.         Term & Termination")
    t = sub(t, "6.         Representations & Warranties",
            "   5.7     Termination for Convenience. Customer may terminate the Framework Terms or any Order Form at any time, "
            "for any reason, on 60 days' notice to Provider. Provider will refund the prepaid Fees for the period after the "
            "termination date within 30 days after termination.\n6.         Representations & Warranties")
    t = sub(t, "8.         Limitation of Liability",
            "   6.5     Data Location. Provider will store Customer Content only on servers located in the United States.\n"
            "8.         Limitation of Liability")
    return "Lakeshore Health, Inc. SaaS Agreement (customer paper), as received\n\n" + t


CASE3 = """# Summit Ridge Manufacturing redline of the ACME SaaS Agreement

**Stand-in draft.** Text form of the redline. Clause numbers match ACME's agreement v1.0. Text-form redline:

Sent by Summit Ridge Manufacturing, Inc. to Alex Easton (ACME), March 2026.

---

**Preamble** (Summit Ridge's counsel updated the party names)

This Software as a Service Agreement ("SaaS Agreement") is between ACME, Inc. ("Provider") and ~~[Customer legal name]~~ **Summit Ridge Manufacturing, Inc.** ("Customer").

**Key Terms, Covered Claims** (Provider Covered Claims)

Provider Covered Claims: Any action, proceeding, or claim that the Cloud Service, when used by Customer according to the terms of the Agreement, violates, misappropriates, or otherwise infringes upon anyone else's intellectual property or other proprietary rights**, or that is made by a third party and results from Provider's violation of Applicable Laws**.

**Key Terms, Uncapped Claims**

Notwithstanding anything to the contrary, the following claims are not subject to the General Cap Amount: (a) death, bodily harm, or personal injury; ~~and~~ (b) an Indemnifying Party's indemnification obligation**; and (c) a party's gross negligence or willful misconduct**.

**Key Terms, Insurance Minimums**

During the Subscription Period and for six months after, Provider will carry: (a) commercial general liability insurance with limits of at least $1,000,000 for each occurrence and $2,000,000 in the aggregate; (b) workers' compensation insurance as required by Applicable Laws; and (c) cyber liability insurance with limits of at least ~~$5,000,000~~ **$10,000,000** for each occurrence and in the aggregate.

**Section 1.6 (new), Service Levels** (inserted after Section 1.5)

**Provider will make the Product available at least 99.5% of the time in each calendar month. If availability in a month is below 99.5%, Provider will credit Customer up to 25% of the Fees for that month. If availability is below 99.5% in any 3 months of a rolling 6-month period, Customer may terminate the affected Order Form on notice to Provider. Except for that termination right, credits are Customer's sole remedy for the shortfall.**

**Section 4.3 Payment**

Customer will pay Provider Fees and taxes in U.S. Dollars, unless the Order Form specifies a different currency, according to the payment terms in the Order Form. **Provider will invoice Fees quarterly in advance.**
"""


if __name__ == "__main__":
    (EX / "cases" / "case-2-lakeshore-paper" / "inputs" / "Lakeshore_Health_SaaS_Agreement.txt").write_text(case2(), encoding="utf-8")
    (EX / "cases" / "case-3-acme-redline-2" / "inputs" / "redline.md").write_text(CASE3, encoding="utf-8")
    print("written")
