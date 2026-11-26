# The approval record

The approval record is **proof of authority for the changes, not proof of the changes.** The signed contract proves what was agreed. The record proves who was entitled to agree to each change from standard, and what they actually said.

For each deviation, the record is a chain of links. If a link is missing or does not match, that deviation is not proven. The record says so; it never fills the gap.

## The links

| Link | Question | Evidence |
|---|---|---|
| The change | What exactly was changed? | Clause reference and the requested wording, quoted |
| The rule | Who had authority? | Matrix row and level, quoted from the matrix version in force |
| The approver | Was the person entitled to approve? | Sender matched to a title through `people.csv` |
| The decision | What did they actually say? | The reply quoted word for word, with date and time, and any conditions |
| The match | Does the decision cover the request? | A status, with the reason |

## Columns

The app builds the record with these columns.

| Column | Meaning |
|---|---|
| ID | The change's ID |
| Change | A short name for the change |
| Matrix row and level | The row and the level that covers the change |
| Approver (name, title) | Each person who decided or is awaited, noting any delegation; or the Deal Desk and the authority it cited |
| Decision (exact words) | What each person wrote, including an appeal's outcome |
| Status | One of the statuses in [escalation-path.md](escalation-path.md) |
| Conditions (exact words) | Any condition or limit |
| Final outcome | Filled in by the final check: whether the change is in the final contract, and if so whether it is covered |
| Notes | Simulated approvals, appeals, decision time and flags |

Under the table the record lists draft seller notes for denials and any request still open.

## Header and version

A demo record begins with a SIMULATED APPROVERS warning. The ledger stores the matrix version (a hash of the matrix files) and the deal facts with each record, so a later matrix change does not rewrite which rules applied. Printing the customer, deal value, matrix version and the AI environment at the top of the record itself is not built yet; when filing a record by hand, add them.

## Where it is kept

The app saves the record in the deal's run folder and adds it to the ledger. The record custodian files it with the evidence and the signed contract.

## What the record is not

- It does not show that a change was made in the contract. Final outcome shows that, separately.
- It does not prove who was at the keyboard. That rests on the sign-in method, so use single sign-on or well-managed logins.
- It is not an argument for approval. It records decisions that were made.
