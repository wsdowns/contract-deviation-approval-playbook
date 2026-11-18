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

| Column | Meaning |
|---|---|
| ID | The deviation's ID from Stage 1, including sub-items such as 4a |
| Change | The requested change, with the clause reference |
| Matrix row and level | The row and the level that covers the change |
| Approver | Name and title of each person who replied, or "no reply yet" |
| Decision | The reply in exact words |
| Date and time | When the reply was sent |
| Evidence | A reference to the message (file name or message ID). A hash of the message file can be added by tooling so later edits are detectable |
| Status | One of the statuses below |
| Conditions | Any condition or limit, in exact words |
| Final outcome | Conceded as approved, Not conceded, or Conceded differently. Filled in once the final contract is reported |
| Notes | Flags, prerequisites shown or missing, and anything a human must settle |

## Statuses

Approved, Conditional, Partial, Unclear, Missing co-approval, Wrong authority, Authority unclear, Not in matrix, Not approvable, Denied. The meaning of each, and what happens next, is in [escalation-path.md](escalation-path.md). A change that the matrix pre-approves is recorded as **Approved (pre-approved)**, naming the role.

## Header

Each record begins with:

- the customer, deal value and date;
- the matrix version it was checked against (a commit or file hash);
- who prepared it and who confirmed the requests;
- the record custodian and the pre-signature check role.

Pinning the matrix version means that if the matrix changes later, the record still shows which rules applied.

## Where it is kept

The record custodian stores the record with the evidence (the original messages) and the signed contract, as one file. In this repository, a case's record would sit in `runs/` with the run that produced it.

## What the record is not

- It does not show that a change was made in the contract. Final outcome shows that, separately.
- It does not show that an email is genuine. Sender authentication belongs to the email system. In a real organization, approvals should arrive through a controlled channel.
- It is not an argument for approval. It records decisions that were made.
