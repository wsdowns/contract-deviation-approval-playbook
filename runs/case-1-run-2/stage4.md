# Stage 4: Document the actual decisions (Brightwater Logistics, run 2)

## Record header

- Customer: Brightwater Logistics, Inc. Deal value: $20,000 (annual fees $20,000, term 1 year). Record date: replies of February 10 and 11, 2026 processed.
- Matrix version checked: `examples/acme-saas/doa-matrix/doa_matrix.csv`, sha256 prefix 91963d57eb28fc40.
- Prepared by: AI partner. Requests confirmed and sent by: Alex Easton, Account Executive, on February 9, 2026 (assumed for this run).
- Record custodian: Contracts Manager (Casey Morrow). Pre-signature check: Deal Desk Manager (Darla Denkins).
- The final contract has not been reported. Final outcome is shown only where it follows from a denial.

## Replies, one at a time

1. **01-darla-net-45.md.** Sender darla.denkins@acme.example is Darla Denkins, Deal Desk Manager. Matches R3 by subject ("Brightwater Logistics: payment terms Net 45"). Title is the one Stage 2 names for D3 (Level 1). Reply: "Approved. Net 45 from the invoice date is fine for a small account like Brightwater." It approves the whole request. Status **Approved**.
2. **02-vivian-renewal-cap.md.** Sender vivian.fairfax@acme.example is Vivian Fairfax, VP Finance. Matches R4. Title is the one named for D4 (Level 2). Reply: "Denied. A 3% cap would set a precedent we do not want on a $20,000 account. The standard renewal increase stays." Status **Denied**. Final outcome **Not conceded** from now.
3. **03-andrea-liability-cap-2x.md.** Sender andrea.collins@acme.example is Andrea G. Collins, Associate General Counsel. Matches R1. Title is the one named for D1 (Level 2). Reply: "Approved. A cap of 2x annual fees is $40,000, which is small exposure for this deal." The reply approves 2x and the $40,000 matches 2 x $20,000. Status **Approved**.
4. **04-cassie-service-levels.md.** Sender cassie.sutton@acme.example is Cassie Sutton, VP Customer Success. Matches R2. Title is the one named for D2 (Level 1). Reply: "Approved. 99.9% availability with credits up to 15% is fine." It opens with "Approved" and restates both figures, so 2a and 2b are covered. It does not mention "sole remedy" (2c), which is the standard position and not a change. Status **Approved**.

## Approval record

| ID | Change | Matrix row and level | Approver (name, title) | Decision (exact words) | Date and time | Evidence | Status | Conditions (exact words) | Final outcome | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| D1 | Key Terms, General Cap Amount: "2x the Fees paid or payable by Customer to Provider in the 12 month period immediately before the claim." | General liability cap, Level 2: "Up to 2x fees: Associate General Counsel" | Andrea G. Collins, Associate General Counsel | "Approved. A cap of 2x annual fees is $40,000, which is small exposure for this deal." | Tue, 10 Feb 2026 14:26 -0500 | approvals/03-andrea-liability-cap-2x.md (sha256 977c11a6909533b3) | Approved | None | Pending contract report | Reply says "2x annual fees"; the clause measures "Fees paid or payable ... in the 12 month period immediately before the claim". Equal at $20,000 and a 1-year term. Check at pre-signature. The cap is mutual (also raises Customer's cap). |
| D2 | New Section 3.2: 99.9% availability; credits "up to 15% of the Fees for that month"; "sole remedy" | Service levels and credits, Level 1: "99.9% availability, credits up to 15%: VP Customer Success" | Cassie Sutton, VP Customer Success | "Approved. 99.9% availability with credits up to 15% is fine." | Wed, 11 Feb 2026 10:08 -0500 | approvals/04-cassie-service-levels.md (sha256 a639cc0f5db89a27) | Approved | None | Pending contract report | Reply does not repeat "sole remedy"; that matches the standard, so no gap is recorded. Credit form (not cash) is not stated in the clause. Check at pre-signature. |
| D3 | Section 4.2 Payment: "Unless the Order Form states otherwise, invoices are payable within 45 days of the invoice date." | Payment terms, Level 1: "Net 45: Deal Desk Manager" | Darla Denkins, Deal Desk Manager | "Approved. Net 45 from the invoice date is fine for a small account like Brightwater." | Tue, 10 Feb 2026 09:14 -0500 | approvals/01-darla-net-45.md (sha256 7b18fec3328f3517) | Approved | None | Pending contract report | The clause lets the Order Form override. Pre-signature check should read the Order Form. The same person approved D3 and performs the pre-signature check. |
| D4 | New Section 4.4: "On each automatic renewal, Provider may increase the Fees by no more than 3% over the Fees for the prior Subscription Period." | Renewal price increase cap, Level 2: "Cap at 3%: VP Finance" | Vivian Fairfax, VP Finance | "Denied. A 3% cap would set a precedent we do not want on a $20,000 account. The standard renewal increase stays." | Tue, 10 Feb 2026 11:02 -0500 | approvals/02-vivian-renewal-cap.md (sha256 788f27b8290eae80) | Denied | None | Not conceded | Contract stays at the standard. If the denied clause appears in the final contract it is Conceded differently, with no approval. |
| D5a | Section 12.8: Provider's publicity right deleted | Publicity, Level 1: "Pre-approved: remove Provider's publicity right: Contracts Manager" | none (Contracts Manager, Casey Morrow, pre-approved role) | none | n/a | none | Approved (pre-approved), Contracts Manager | None | Pending contract report | No reply expected. Fit doubt: see D5b. |
| D5b | Section 12.8: "Provider will not identify Customer or use Customer's name or logo in any marketing or customer list without Customer's prior written consent." | Publicity, Level 1 cell does not clearly cover it | no reply yet (matrix owner Grace Colton, General Counsel, asked in Q1) | none | n/a | none | Authority unclear | None | Pending contract report | Waits for the matrix owner's ruling on who may approve. A ruling is not an approval of the change; the approvals it names are still needed. |

Not all changes are approved. Status count: Approved 3 (D1, D2, D3), Denied 1 (D4), Approved (pre-approved) 1 (D5a), Authority unclear 1 (D5b).

## Open items

- **D5b, Authority unclear.** No reply yet from Grace Colton to Q1. Next step: wait for her ruling, then request the approvals it names. The playbook sets no reminder period, so no reminder is drafted. The seller should say when to chase.
- **D4, Denied.** Settled; no open approval. The seller negotiates from the standard. Any counterproposal starts at Stage 1.
- **Final contract not reported.** Final outcome and the pre-signature check wait for it (Darla Denkins runs the check).
- Clause-number confirmation from the seller (Stage 1, question 1) was not answered in the files I was given.

## Flags (separate from open items)

- D5a: pre-approved row, with a fit doubt about the paired covenant in D5b. Not an open item for D5a.
- N1 (matrix versus agreement standards) was a notice; no reply is in the files.

## Follow-up drafts (for the seller to confirm)

- **D1, D2, D3:** none needed.
- **D4 (Denied):** no message to Vivian Fairfax. Message to the seller: "Vivian Fairfax, VP Finance, denied the 3% renewal cap. The standard renewal increase stays. I have not suggested or drafted a counterproposal."
- **D5b:** none new. Q1 is already with the matrix owner.

## Pre-signature check

Not run. The seller has not reported the final contract.

## What I did not do or could not check

- I did not contact anyone.
- I could not verify that the emails are genuine; sender matching uses `people.csv` only.
- I could not check the Order Form or the final contract.
