# Escalation path, statuses and ambiguity

How a contract deviation moves from request to proven approval, what status each deviation can have, and what happens when something is unclear. These rules apply to any contract type. Roles are named by the titles in `settings.csv`, so each organization fills in its own.

## The path

1. **Requester** (for example, the account executive) hands the contract to the playbook: a redline, or the counterparty's paper as received.
2. **Identify (Stage 1).** The AI lists every deviation from the standard positions in `doa_matrix.csv`, with clause references and the requested wording.
3. **Locate (Stage 2).** The AI finds the matrix row for each deviation and routes it to the **lowest level whose authority covers the request**. A higher level may also approve, but the request does not skip levels.
4. **Draft (Stage 3).** The AI drafts one escalation request per approver: the change, the standard position, the deal facts and exposure, a modest recommendation (hold the standard unless the profile gives a reason), and the decision needed. The AI never proposes a concession. After the requester confirms the batch once, the playbook sends each request on the requester's behalf and copies the **approvals mailbox**.
5. **Approvers reply** to the approvals mailbox. The playbook matches each reply to the request it answers and each sender to a title. See [seller-experience.md](seller-experience.md).
6. **Document (Stage 4).** The AI records each decision with a status (below), quoting the approver word for word.
7. The **record custodian** stores the approval record, the evidence and the contract together.
8. The **pre-signature check** compares the final contract with the approvals before anyone signs.

Every deviation must reach **Approved** or **Conditional**, or be removed from the contract, before signature.

## Statuses

| Status | Meaning | Next step |
|---|---|---|
| Approved | The approver named by the matrix approved the full request | None |
| Conditional | Approved, with conditions or limits | Record the conditions word for word. The requester makes sure the contract reflects them |
| Partial | The approval covers only part of the request | Record the approved part as Approved. Send the rest back to the same approver |
| Unclear | The reply does not clearly approve or deny the request | Send it back to the same approver with a specific yes/no question. Silence is not approval |
| Missing co-approval | A joint approval (`+`) is incomplete | Chase each approver who has not replied. Nothing is approved until all have |
| Wrong authority | The reply came from someone who does not hold the title the matrix names | Not valid. Re-send the request to the correct title |
| Authority unclear | The matrix does not clearly say who may approve this request | The matrix owner rules on who has authority. Then escalate to that approver |
| Not in matrix | No matrix row covers the deviation | The matrix owner decides. Do not apply the nearest row by analogy |
| Not approvable | The position is in the Not approvable column | No one may approve it. The requester negotiates it out, or the matrix owner amends the matrix |
| Approved (pre-approved) | The matrix lets a named role accept the change without escalation, and the request is within the cell's words | No message is sent. Name the role in the record. If the request does anything the cell does not name, it is Authority unclear instead |
| Denied | The approver said no | The contract stays at the standard position. The seller may appeal once to the same approver, with new context. After that the decision stands. A different position goes in a new round of the contract |

## Approval is permission, not an obligation

The organization's interest is to keep terms as close to standard as possible. Negotiation protects the company, not the individual seller. So:

- **An approval lets the requester concede a term. It never requires it.** The requester decides how to negotiate and may hold an approval unused.
- **The approver decides, and may deny.** A denial is a normal outcome, not a failure. The requester does not decide whether a concession is worth making; the approver does.
- **Concede in small steps.** Each request carries a recommendation: hold the standard, or offer the smallest concession that could close the point, such as the Level 1 fallback before a Level 2 position.
- **The record shows the final contract outcome** for each change, next to its status: **Conceded as approved**, **Not conceded** (the request was denied or the approval went unused), or **Conceded differently** (the contract says something other than what was approved, so the approval does not cover it).
- **The pre-signature check works in both directions.** Every change from standard in the final contract must be covered by an approval, and an approval is never proof that a change was made.

## Appeals, and a different position after a denial

A seller may appeal a denial once. The appeal goes back to the same approver, quoting the denial in the approver's words and any new context the seller adds, and the approver decides again. There is no appeal to anyone above the approver, and no second appeal. A "not approvable" change has no approver, so it cannot be appealed.

A denial also does not stop the seller from asking for a different position, in a new round of the contract. The seller must ask; the app never suggests it. The new request is routed to the lowest level that covers it, even if that is lower than the approver who denied, and it quotes the denial so the new approver decides with the facts. The matrix does not say whether a lower-level approval after a higher-level denial is allowed. The record flags this, and the matrix owner may add a rule.

## Two kinds of ambiguity

Ambiguity is treated differently depending on whose question it is.

| | Rule ambiguity | Decision ambiguity |
|---|---|---|
| The question | Who has authority? | What did the approver actually approve? |
| Cause | The deviation is in the matrix but does not fit cleanly into one level, or two cells conflict | The approver's reply does not clearly cover the whole request |
| Status | Authority unclear | Unclear or Partial |
| Goes to | The **matrix owner**, because it is a question about the matrix | The **same approver**, because it is a question about their answer |
| The AI must not | Pick the closest level | Read silence, "looks fine", or a reply to a different question as approval |

### Examples from the ACME SaaS example

- **Rule ambiguity (Case 2).** The customer asks for a liability cap of the greater of 3x fees or $5M. Level 3 allows "up to 3x fees, or a fixed floor up to $5M", and Not approvable lists "any cap above 3x fees or $5M". A greater-of formula combines both, so the matrix does not settle whether Level 3 may approve it. The AI flags Authority unclear and asks General Counsel, as matrix owner, to rule.
- **Decision ambiguity (Case 1).** The customer asks to uncap gross negligence and willful misconduct. The CEO replies approving "the gross negligence carve-out" and says nothing about willful misconduct. The AI records gross negligence as Approved, records willful misconduct as Unclear, and asks the CEO a yes/no question about willful misconduct.

## What the record must never do

- Show a deviation as approved when its status is anything other than Approved or Conditional.
- Drop or paraphrase an approver's conditions.
- Resolve an ambiguity by inference, however reasonable.
