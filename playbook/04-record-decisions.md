# Stage 4: Document the actual decisions

## Purpose

Record, for each deviation, who actually decided what, in their exact words, and whether that person had the authority. The record is **proof of authority for the changes, not proof of the changes.**

## Inputs

- The Stage 2 routing table and the requests sent.
- Each reply, one at a time, with sender address, date and time.
- `people.csv`, `roles.csv`, `doa_matrix.csv`.
- Later, the seller's report of what the final contract says.

## Steps for each reply

1. **Match the reply to a request.** Use the subject, thread and content. If it matches more than one request, or none, flag it and do not record it against a deviation.
2. **Identify the sender.** Look up the sender's address in `people.csv` to get the person and title. If the address is not there, the sender is unknown: status **Wrong authority**, and say the sender could not be identified.
   A message with a `Via: approval portal` line was sent by someone signed in to the portal, so the sender is verified: do not raise the sender as unverified. A line `Acting by delegation from: <name, title>` means the approver delegated this request to the sender in the portal. Record the decision as that title's, show both names, and add "acting by delegation" to Notes. The approver's own delegation needs no entry in the matrix.
   If any message has a `Simulated: yes` line, the reply was written by an AI-played approver in demo mode. Put "SIMULATED APPROVERS: demo only, not proof of authority." as the first line of the record, and again in the pre-signature check.
3. **Check authority.** The sender's title must be one the routing names for that deviation, or a title at a higher level of the same row (a higher level may approve what a lower level may). If not, the status is **Wrong authority**, however clear the reply is. Also check each prerequisite from Stage 2; if a prerequisite is not shown in the evidence, flag it.
4. **Read the reply and classify it**, using only what it says:

   | Status | When |
   |---|---|
   | Approved | It clearly approves the whole request as stated |
   | Conditional | It approves, with a condition, limit or qualification. Quote it exactly |
   | Partial | It approves part of the request, in words or by leaving out a separable part |
   | Unclear | It does not clearly approve or deny ("looks fine", "let's discuss", an answer to a different question) |
   | Denied | It refuses |

   Silence on part of a request is **Unclear** for that part, never Approved and never Denied.
5. **Split when needed.** If a reply covers only part of the request, record the covered part with its status and the rest as Unclear (or Denied, if the reply refuses it).
6. **Joint approvals.** Every required title must approve. Until all have, the status is **Missing co-approval**. If any approver denies, the deviation is **Denied**, and you record each person's decision separately.
   **Relayed replies.** If the reply reaches you as pasted text rather than a file, use the sender in the pasted header, put "relayed by <name>, <date>, original not seen" in Evidence, and flag that the sender could not be verified from the original message.
7. **Record it.** Add the row: approver (name and title), the decision in exact words, date and time, evidence reference, status, and any conditions quoted. Never paraphrase a condition.
8. **Draft the follow-up** the status table in Stage 3 calls for, for the seller to confirm.

**Later rounds.** If the input has a `<prior_approval_record>`, copy forward the row for every deviation whose Round status is **Already decided**: same approver, exact words, date, status and conditions, with Evidence "carried forward from <round name>". Process the new replies as usual for the other deviations. A carried-forward approval is only as good as the earlier record: never upgrade it.

## Statuses carried from Stage 2

Some deviations have a status before any reply arrives. Record them from the start.

| Stage 2 outcome | Status in the record | What changes it |
|---|---|---|
| Not approvable | **Not approvable** | Only a change to the matrix. The seller negotiates the term out |
| Not in matrix | **Not in matrix** | The matrix owner's decision. Record it as that person's decision, in exact words, and note any request to add a matrix row |
| Authority unclear | **Authority unclear** | The matrix owner's ruling on who may approve. Record the ruling in exact words, then record the approvals it calls for as for any other deviation |
| Pre-approved | **Approved (pre-approved)**, naming the role | Nothing; no reply is expected |

A ruling on who has authority is not an approval of the change. The change still needs the approvals the ruling names.

## Seller note for a Denied row

The note is for the **seller to use with the customer**, not a summary for the record. Draft one for each Denied row, with these four parts:

1. **Where we stand.** One sentence: the standard position stays, and which term.
2. **What the standard says.** The standard position and clause, quoted from the standard agreement or the matrix.
3. **A line the seller may say.** Two or three courteous sentences for the customer. They state the position and make no promise.
4. **What not to say.** Do not share the approver's name, title or reasoning, and do not say the request was "close" or "might be reconsidered".

Rules: use only what the documents say; never invent a reason, policy or precedent; do not suggest a concession or a counterproposal; keep it under 120 words. The approver's reasoning stays internal unless the approver said it may be shared. The same note format is defined in `03-draft-requests.md`.

## The final contract

When the seller reports what the final contract says, fill in **Final outcome** for each deviation:

| Final outcome | Meaning |
|---|---|
| Conceded as approved | The contract contains the change, within what was approved |
| Not conceded | The contract keeps the standard: the request was denied, withdrawn, or the approval went unused |
| Conceded differently | The contract says something other than what was approved, so the approval does not cover it |

Then run the pre-signature check:

- Every change from standard in the final contract has an approval that covers it. List any that does not.
- No approval is treated as proof that a change was made.
- Any condition an approver attached appears in the contract, or is flagged.

## Output

**Approval record**

| ID | Change | Matrix row and level | Approver (name, title) | Decision (exact words) | Date and time | Evidence | Status | Conditions (exact words) | Final outcome | Notes |
|---|---|---|---|---|---|---|---|---|---|---|

The record format is defined in `docs/approval-record.md`.

**Open items** (everything not yet Approved, Conditional or Pre-approved, with the next step for each)

**Follow-up drafts** (for the seller to confirm). For each Denied row, include the seller note defined above.

**Pre-signature check** (once the final contract is reported)

## Rules

- **Never write "all approved" unless every row is Approved, Conditional or Pre-approved.**
- A Denied row has Final outcome **Not conceded** from the moment of the denial, even before the seller reports the contract. The record must not suggest it may still be conceded. If the seller later reports the denied term in the contract, mark it Conceded differently and flag it as having no approval.
- A row with no reply, or a pre-approved row, shows "n/a" in the date column and "none" as approver reply.
- A flag on a pre-approved row (for example a doubt about fit) belongs in Notes and in a separate **Flags** list, not in Open items.
- Never overstate an approval. If a reply approved part of a request, the record says exactly which part.
- Never resolve an ambiguity by inference, however reasonable the inference seems.
- Quote conditions and decisions exactly. Do not tidy their grammar.
- If a condition changes how the organization's standard terms work, note that in `Notes`; do not decide whether it matters.
- Do not contact anyone. Draft follow-ups only.

## Check before you finish

- Every deviation has a status.
- Every Approved, Conditional or Denied row quotes the decision and shows the approver's title.
- Every Wrong authority row says why (title not named, or sender not identified).
- Every Conditional row quotes its condition word for word.
- Open items list a next step for every row that is not settled.
