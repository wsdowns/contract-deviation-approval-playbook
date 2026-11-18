# Stage 4: Document the actual decisions (Brightwater Logistics redline)

## Header

- Customer: Brightwater Logistics, Inc.
- Deal value: $20,000 annual fees, 1 year term. Target signature February 27, 2026.
- Requests sent: February 9, 2026 (assumed: seller confirmed the batch and all four requests were sent that day).
- Replies recorded through: February 11, 2026, 10:08 -0500.
- Matrix version checked against: `examples/acme-saas/doa-matrix/doa_matrix.csv`, SHA-256 `91963d57eb28fc40d448a4b39f5fb294c069d058abf92c586b50761e6563f59f`.
- Prepared by: AI partner. Requests confirmed by: Alex Easton, Account Executive (requester), per the instruction that the seller confirmed.
- Record custodian: Contracts Manager (Casey Morrow). Pre-signature check: Deal Desk Manager (Darla Denkins).

## Approval record

| ID | Change | Matrix row and level | Approver (name, title) | Decision (exact words) | Date and time | Evidence | Status | Conditions (exact words) | Final outcome | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| D1 | Key Terms, General Cap Amount: "2x the Fees paid or payable by Customer to Provider in the 12 month period immediately before the claim." (takes effect through Section 8.1) | General liability cap, Level 2: "Up to 2x fees: Associate General Counsel" | Andrea G. Collins, Associate General Counsel (andrea.collins@acme.example, matches people.csv) | "Approved. A cap of 2x annual fees is $40,000, which is small exposure for this deal." | Tue, 10 Feb 2026 14:26 -0500 | `approvals/03-andrea-liability-cap-2x.md` | Approved | None | | Title is the one Level 2 names. No prerequisite. Reply says "2x annual fees"; the clause says 2x "Fees paid or payable ... in the 12 month period immediately before the claim". Reply does not mention that Section 8.1 applies the higher cap to "each party". Recorded as Approved; a human may confirm whether the wording difference matters. |
| D2 (2a, 2b) | New Section 3.2: "Provider will make the Product available at least 99.9% of the time in each calendar month. If availability in a month is below 99.9%, Provider will credit Customer up to 15% of the Fees for that month, as Customer's sole remedy for the shortfall." | Service levels and credits, Level 1: "99.9% availability, credits up to 15%: VP Customer Success" | Cassie Sutton, VP Customer Success (cassie.sutton@acme.example, matches people.csv) | "Approved. 99.9% availability with credits up to 15% is fine." | Wed, 11 Feb 2026 10:08 -0500 | `approvals/04-cassie-service-levels.md` | Approved | None | | Title is the one Level 1 names. No prerequisite. Reply covers both 2a (99.9%) and 2b (up to 15%). 2c (sole remedy) matches the standard and needed no approval. Section number 3.2 collides with an existing section (Stage 1). |
| D3 | Section 4.2 Payment: "Unless the Order Form states otherwise, invoices are payable within 45 days of the invoice date." | Payment terms, Level 1: "Net 45: Deal Desk Manager" | Darla Denkins, Deal Desk Manager (darla.denkins@acme.example, matches people.csv) | "Approved. Net 45 from the invoice date is fine for a small account like Brightwater." | Tue, 10 Feb 2026 09:14 -0500 | `approvals/01-darla-net-45.md` | Approved | None | | Title is the one Level 1 names. No prerequisite. Order Form still not provided (Stage 2, flag 3), so the opening words "Unless the Order Form states otherwise" cannot be checked against it. Section 2.3 suspension wording ("more than 30 days") is unedited and was not part of the request or the reply (Stage 2, flag 2). The approver is also the pre-signature check role. |
| D4 | New Section 4.4: "On each automatic renewal, Provider may increase the Fees by no more than 3% over the Fees for the prior Subscription Period." | Renewal price increase cap, Level 2: "Cap at 3%: VP Finance" | Vivian Fairfax, VP Finance (vivian.fairfax@acme.example, matches people.csv) | "Denied. A 3% cap would set a precedent we do not want on a $20,000 account. The standard renewal increase stays." | Tue, 10 Feb 2026 11:02 -0500 | `approvals/02-vivian-renewal-cap.md` | Denied | None | | Title is the one Level 2 names. The denial is clear and covers the whole request. The standard stays: "Fees may increase up to 7% at each renewal". The reply does not address any other cap. Section number 4.4 collides with an existing section (Stage 1). |
| D5 (5a, 5b) | Section 12.8 Logo Rights: Provider's publicity right deleted; inserted "Provider will not identify Customer or use Customer's name or logo in any marketing or customer list without Customer's prior written consent." | Publicity, Level 1: "Pre-approved: remove Provider's publicity right: Contracts Manager" | No reply expected. Role: Contracts Manager (Casey Morrow) | None | Not applicable | None | Approved (pre-approved), Contracts Manager | None | | Carried from Stage 2. Stage 2, flag 5 is still open: if a human reads the added consent promise (5b) as more than "remove Provider's publicity right", 5b has no clearly covering cell and would be Authority unclear. Not resolved here. |

No row shows a Final outcome yet. The seller has not reported the final contract.

## Open items

| ID | Status | Next step |
|---|---|---|
| D4 | Denied | No follow-up to Vivian Fairfax. The standard stays, and the record does not treat this change as concedable. The seller negotiates the term out of the contract. If the seller wants a counterproposal, it returns to Stage 1 and is routed to the level that covers it. Final outcome stays blank until the seller reports the final contract. |
| D5 | Approved (pre-approved), flag open | Seller or Contracts Manager to confirm whether 5b (the added consent promise) is covered by the pre-approved cell (Stage 2, flag 5). If not, 5b goes to the matrix owner as Authority unclear. |
| D1, D2, D3 | Approved | Not open. Pending checks: Order Form for D3, and confirmation of the "annual fees" wording for D1 (see Notes). |
| All | Final contract not reported | Seller reports what the final contract says for D1 to D5. Then fill in Final outcome and run the pre-signature check. |

Carried over from earlier stages and still unresolved: Order Form not provided, redline completeness not confirmed, redline section numbers do not match agreement v1.0, and the matrix standards for D2 and D4 (99.5%, 7%) are not in agreement v1.0.

## Follow-up drafts (for the seller to confirm)

No message to any approver is needed. No reply is Partial, Unclear, Wrong authority or Missing co-approval, and there is no joint approval. Nothing below is sent.

**Note to the seller (D4, Denied)**

Vivian Fairfax, VP Finance, replied on February 10, 2026 at 11:02 -0500: "Denied. A 3% cap would set a precedent we do not want on a $20,000 account. The standard renewal increase stays." The standard stays: "Fees may increase up to 7% at each renewal". Please remove Section 4.4 from the contract, or negotiate it back to the standard. No approval exists for any renewal cap. If you want to offer a different cap, tell me and I will return to Stage 1 and route it to the level that covers it. I have not drafted any request to Vivian Fairfax.

**Note to the seller (what the approvals do and do not allow)**

D1 (2x cap), D2 (99.9% and up to 15%) and D3 (Net 45) have approvals. An approval lets you concede a term. It does not require it. D4 is denied, so not every deviation is approved. Please report the final contract text for D1 to D5 so I can fill in Final outcome and run the pre-signature check.

## Pre-signature check

Not run. It runs once the seller reports the final contract.

## What I did not do or could not check (Rule 12)

- Did not contact anyone or send anything.
- Did not verify that the reply emails are genuine. Sender matching used the address in each reply against `people.csv` only.
- Did not see the Order Form, the full Brightwater document, or the final contract.
- Did not decide whether D5 sub-item 5b is covered by the pre-approved cell.
- Needs a human decision: whether the Deal Desk Manager should perform the pre-signature check on D3, which she approved.
