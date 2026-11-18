# Stage 2: Locate the delegation of authority rule

Annual fees from the deal profile: $20,000. Term 1 year.

| ID | Matrix row | Outcome | Cell relied on (exact words) | Approver titles | Joint? | Prerequisites | Reasoning |
|---|---|---|---|---|---|---|---|
| D1 | General liability cap | Route to Level 2 | Level 2: "Up to 2x fees: Associate General Counsel". Level 1: "Up to 1.5x fees: Contracts Manager". Not approvable: "Uncapped general liability; any cap above 3x fees or $5M" | Associate General Counsel | No | None | 2x fees is $40,000 (2 x $20,000). That exceeds Level 1's 1.5x ($30,000) and fits "Up to 2x fees". It is below the Not approvable limits (3x is $60,000, and $5M). |
| D2 (2a and 2b) | Service levels and credits | Route to Level 1 | Level 1: "99.9% availability, credits up to 15%: VP Customer Success". Standard: "99.5% availability; credits up to 10% of monthly fees; credits are the sole remedy". Not approvable: "Availability above 99.95%; credits paid in cash; uncapped credits" | VP Customer Success | No | None | The request is "99.9%" and "up to 15%", the exact Level 1 pairing. Sub-item 2c (sole remedy) is the standard, so nothing more is needed. Neither Not approvable item applies: 99.9% is not above 99.95%, and the credit is capped. |
| D3 | Payment terms | Route to Level 1 | Level 1: "Net 45: Deal Desk Manager". Not approvable: "Over Net 90; payment terms that run from Customer's receipt or approval of invoice" | Deal Desk Manager | No | None named. See flag 3 on the Order Form | "within 45 days of the invoice date" is Net 45 from invoice date. It does not run from receipt or approval. |
| D4 | Renewal price increase cap | Route to Level 2 | Level 2: "Cap at 3%: VP Finance". Level 1: "Cap at 5%: Deal Desk Manager". Not approvable: "Price lock beyond one renewal; price decreases at renewal" | VP Finance | No | None | A 3% cap is tighter than Level 1's "Cap at 5%", so Level 1 does not cover it. It matches Level 2 exactly. It is a ceiling, not a price lock or decrease. At $20,000 a 3% cap is $600 (a 7% increase is $1,400). |
| D5 (5a and 5b) | Publicity | Pre-approved | Level 1: "Pre-approved: remove Provider's publicity right: Contracts Manager" | Contracts Manager | No | None | 5a deletes the Provider's publicity right, which is the cell's wording. 5b adds a consent-based prohibition. See flag 5. No escalation is needed. |

**Arithmetic**

- D1: 1x = $20,000; requested 2x = $40,000; Level 1 ceiling 1.5x = $30,000; Not approvable threshold 3x = $60,000.
- D2: monthly fees are $20,000 / 12 = $1,666.67, assuming even monthly fees (not stated in the profile). 15% = $250.00 and 10% = $166.67 per month. In a 30-day month (43,200 minutes), 99.9% allows 43.2 minutes of downtime and 99.5% allows 216 minutes.
- D3: 45 days against 30 days is 15 more days to pay an invoice of up to $20,000.
- D4: 3% of $20,000 = $600, giving at most $20,600 at the first renewal. 7% = $1,400, giving $21,400. Difference $800. Compounding applies at later renewals.

**Questions for the matrix owner** (General Counsel)

None. No outcome is Not in matrix or Authority unclear.

**Flags**

1. Standard positions in two sources do not match. For D2 and D4 the matrix gives a standard (99.5% and 10%; 7% renewal increase) that is not in agreement v1.0. I routed on the matrix. If the matrix owner treats the agreement as the standard, D2 and D4 would be additions with no standard position. Noted for the matrix owner; no routing change follows from it.
2. Suspension (D3): Section 2.3 reads "outstanding, undisputed balance ... for more than 30 days" and the matrix standard reads "more than 30 days overdue". With Net 45 the two readings suspend at different dates. The redline does not edit Section 2.3. The matrix row "Suspension for non-payment" is not triggered because no change to suspension is requested. A human should confirm this reading.
3. D3 starts "Unless the Order Form states otherwise". The Order Form was not provided, so I cannot see the standard term it carries or whether it overrides the 45 days. Not guessed.
4. Redline section numbers do not match v1.0 (see Stage 1, seller question 3). Routing is by content, not number.
5. D5, sub-item 5b: the cell says "remove Provider's publicity right". The redline removes the right and also adds a promise not to use Customer's name or logo "without Customer's prior written consent". I read this as the removal the cell describes. If a human reads the added promise as more than removal, 5b has no clearly covering cell and would be Authority unclear. I did not escalate it.
6. Joint approvals: none required for any item. Prerequisites (for example a General Counsel recommendation): none attach to these cells.

**What I did not do or could not check (Rule 12)**

- Did not check for unmarked changes or the Order Form (Stage 1 questions 1 and 2).
- Did not name people. Names come in Stage 3.
- Did not verify that the monthly fee basis is even across 12 months.
