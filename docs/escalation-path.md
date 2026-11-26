# Escalation path, statuses and ambiguity

How a contract deviation moves from request to proven approval, what status each deviation can have, and what happens when something is unclear. These rules apply to any contract type. Roles are named by the titles in `settings.csv`, so each organization fills in its own.

## The path

1. **Requester** (for example, the account executive) uploads the contract.
2. **Identify.** Code lists every difference from the standard agreement.
3. **Locate.** Code finds the matrix row; one AI reading names the **lowest level whose authority covers the request**, and code checks it. A higher level may also approve, but the request does not skip levels.
4. **Request.** Code writes one request per approver: the change, the standard position, the deal facts and exposure, a modest recommendation and the decision needed. The app never proposes a concession.
5. **Approvers decide** in the portal. Notifications copy the seller and the **approvals mailbox**; email replies are not read.
6. **Record.** Code builds the approval record from the decisions, quoting each approver word for word.
7. The **record custodian** files the record, the evidence and the contract together.
8. The **final check** compares the final contract with the approvals before anyone signs, and the **pre-signature check** role reviews it.

Every deviation must reach **Approved** or **Conditional**, or be removed from the contract, before signature.

## Statuses

| Status | Meaning | Next step |
|---|---|---|
| Not sent | The request has not gone out | Fix the reason shown, or confirm the send |
| Awaiting reply | No decision yet | Reminders and escalation run on schedule. Silence is not approval |
| Approved | Every approver the matrix names approved | None |
| Conditional | Approved, with conditions or limits | Conditions are recorded word for word. The requester makes sure the contract reflects them |
| Missing co-approval | A joint approval (`+`) is incomplete | Nothing is approved until all have |
| Approved (pre-approved) | The matrix lets a named role accept the change without escalation | No request is sent |
| Not approvable | The position is in the Not approvable column | No one may approve it. Negotiate it out, or the matrix owner amends the matrix |
| Referred to Deal Desk | The matrix does not settle the change | The Deal Desk finds out what is needed and records the outcome and authority |
| Approved, Approved with conditions, Denied or No approval needed (Deal Desk) | The Deal Desk's recorded outcome | The authority it cites is its own statement, not verified in the system |
| Denied | An approver said no | The contract stays at the standard position. The seller may appeal once |
| Appeal pending | The appeal is with the same approver | Wait for the second decision |

### Extra statuses in the manual process

The portal takes only a clear choice, so a decision cannot be ambiguous. When the process is run by hand with the prompts in `playbook/`, decisions arrive as free text, and these statuses also apply.

| Status | Meaning | Next step |
|---|---|---|
| Partial | The approval covers only part of the request | Record the approved part. Send the rest back to the same approver |
| Unclear | The reply does not clearly approve or deny | Ask the same approver a specific yes or no question |
| Wrong authority | The reply came from someone who does not hold the named title | Not valid. Re-send to the correct title |
| Authority unclear | The matrix does not clearly say who may approve | The matrix owner rules on it |
| Not in matrix | No matrix row covers the change | The matrix owner decides. Do not apply the nearest row by analogy |

## Approval is permission, not an obligation

The organization's interest is to keep terms as close to standard as possible. Negotiation protects the company, not the individual seller. So:

- **An approval lets the requester concede a term. It never requires it.** The requester decides how to negotiate and may hold an approval unused.
- **The approver decides, and may deny.** A denial is a normal outcome, not a failure. The requester does not decide whether a concession is worth making; the approver does.
- **Concede in small steps.** Each request carries a recommendation: hold the standard, or offer the smallest concession that could close the point, such as the Level 1 fallback before a Level 2 position.
- **The record shows the final contract outcome** for each change, next to its status: **Conceded as approved**, **Not conceded** (the request was denied or the approval went unused), or **Conceded differently** (the contract says something other than what was approved, so the approval does not cover it).
- **The pre-signature check works in both directions.** Every change from standard in the final contract must be covered by an approval, and an approval is never proof that a change was made.

## Appeals, and a different position after a denial

A seller may appeal a denial once. The appeal goes back to the same approver, quoting the denial in the approver's words and any new context the seller adds, and the approver decides again. There is no appeal to anyone above the approver, and no second appeal. A "not approvable" change has no approver, so it cannot be appealed.

A denial also does not stop the seller from proposing a different position, in a new round of the contract. The app never suggests one. The new position is routed to the lowest level that covers it, even if that is lower than the approver who denied. The matrix does not say whether a lower-level approval after a higher-level denial is allowed; the matrix owner may add a rule.

## Two kinds of ambiguity

Ambiguity is treated differently depending on whose question it is. The app refers rule ambiguity to the title in the `Terms not in the matrix` setting (the Deal Desk for ACME), or to the matrix owner if the setting is absent. The manual playbook sends it to the matrix owner, and the examples below come from the manual version.

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
