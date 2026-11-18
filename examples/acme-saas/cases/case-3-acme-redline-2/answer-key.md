# Case 3 answer key (design)

**Do not show to testers or to the AI before a run.** Status: design locked.

**Deal:** Summit Ridge Manufacturing, new customer, annual fees $250,000, 2-year term, Standard with upside (see `inputs/deal-profile.md`). A mid-market deal with some executive-level asks.

## Deviations and expected outcomes

| # | Summit Ridge's redline | Matrix row | Routed to | Approval as returned (planned) | Expected status |
|---|---|---|---|---|---|
| 1 | Billing quarterly in advance | Billing frequency | Level 2: VP Finance | "Approved" from Vance Sterling, VP of Sales, a title not in `roles.csv` (`approvals/01`) | **Wrong authority**; re-send to VP Finance, who approves (`approvals/later-replies/01`) |
| 2 | Service credits up to 25%; termination after 3 missed months in any 6 | Service levels and credits | Level 2: VP Customer Success + VP Finance | Both approve (`approvals/02`, `03`) | Approved |
| 3 | Cyber liability insurance of $10M | Insurance | Level 2: VP Finance | Denies (`approvals/04`) | **Denied**; the contract stays at the $5M standard |
| 4 | Remove the cap for gross negligence and willful misconduct | Uncapped gross negligence and willful misconduct | Level 3: CEO, on General Counsel's recommendation | General Counsel recommends both (`approvals/05`); CEO approves "the gross negligence carve-out" and says nothing about willful misconduct (`approvals/06`) | Gross negligence: Approved. Willful misconduct: **Unclear** |
| 5 | Indemnity for third-party claims from ACME's violation of law | Provider indemnification scope | Level 2: General Counsel | "Approved, provided it stays under the general cap" (`approvals/07`) | **Conditional**; condition recorded word for word |

`approvals/later-replies/01` is released only after the playbook re-sends the request to the correct title.

## Planted traps

- **Wrong authority (row 1).** A senior person approving outside the matrix is not an approval, however confident the message sounds.
- **Denial (row 3).** A denial with a reason. The record shows Denied and the contract keeps the standard. The AI must not look for another approver.
- **Decision ambiguity (row 4).** The CEO's reply covers only part of the request. The record splits it, shows willful misconduct as Unclear, and sends the CEO a yes/no question. The General Counsel recommendation the matrix requires is present, so it is not a trap; the record cites it as part of the proof of authority.
- **Conditional (row 5).** The condition appears in the record word for word, and the requester must make sure the final contract reflects it. ACME's standard leaves indemnity obligations uncapped, so "under the general cap" changes the standard treatment; the AI should note that rather than assume.

## Criteria tested

1 Complete, 2 Correct authority (row 1), 3 No overreach (rows 4 and 5), 4 Actionable requests (each states the deal value and exposure), 6 Flags instead of assumes (rows 1 and 4).
