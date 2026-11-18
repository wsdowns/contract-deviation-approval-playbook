# Stage 3: Draft the escalation requests

## Purpose

Draft one clear request for each approver, so each can decide from the page without a phone call. Show the seller the whole batch once for confirmation. Draft follow-ups when a reply or a flag needs one.

## Inputs

- The Stage 2 routing table.
- The deal profile.
- Concessions already approved in this deal (from the record, if any).
- `people.csv` and `settings.csv`, for recipients and the approvals mailbox.

## Steps

1. **Check the deal profile.** List any blank field that matters to a request (for example, annual fees for a liability cap). Ask the seller once. Anything still blank appears in the requests as "not provided".
2. **Decide what to send.** Draft a request for each deviation routed to a level. Do not draft approval requests for:
   - **Pre-approved** items: note them in the batch summary.
   - **Not approvable** items: tell the seller they must be negotiated out or taken to the matrix owner to amend the matrix.
   - **Not in matrix** and **Authority unclear** items: draft a question to the matrix owner instead (see Follow-ups below).
   Also do not draft a request for a deviation whose Round status is **Already decided**. List it in the batch summary as covered by the earlier decision, with the prior ID. Do draft one for **New**, **Changed since decided** and **Reinserted after denial**; for the last, part 2a of the request names the earlier denial.
3. **One request per deviation per approver.** Do not combine deviations in one message. For a joint approval, send each approver the same request and say who else must approve.
4. **Work out the exposure.** Compare the ask with the deal value, for example "a $5M cap on $1M of annual fees is 5 times fees". Show the arithmetic.
5. **Write the recommendation.** Recommend either to hold the standard or to offer the smallest concession that could close the point, usually the next lower level of the same matrix row. Where the request is already at the lowest level, there is no lower step: recommend holding the standard unless the profile gives a reason to concede, and say what that reason is. Label it as a recommendation.
6. **Show the batch summary.** The app sends the batch under the organization's send setting.

## Request format

Start each request with a heading `### Request N` (N counts from 1), so a person or a program can separate them.

**To:** the approver, by name and title from `people.csv`
**Cc:** the seller and the approvals mailbox
**Subject:** `<Customer>: <short description of the change>`
**Matrix row:** the exact `Term` from `doa_matrix.csv` that this request relies on (for a question to the matrix owner, write `none`)
**Level:** the level number you routed to, for example `2`

The program checks these two lines against the matrix before anything is sent: the person in **To** must hold a title named in that level's cell, and for a joint approval a request must go to every title named. A request that fails is held, and nothing in the batch goes out.

**Body, in this order**

1. **Decision needed.** One sentence: what you are asking the approver to approve or deny.
2. **The change.** The counterparty's exact words, with the clause reference.
3. **Our standard.** The standard position.
4. **Why the customer asks.** The seller's one line, labeled as the customer's stated reason.
5. **The deal.** Annual fees, term, strategic or standard, upside, competition and any other profile facts that bear on this request. Use "not provided" for blanks.
6. **Exposure.** The ask measured against the deal, with the arithmetic.
7. **Already approved in this deal.** Concessions granted so far.
8. **Who else decides.** Other required approvers and their status.
9. **Recommendation.** Hold the standard, or the smallest concession, labeled as a recommendation.
10. **How to reply.** "Reply to this message with Approved, Denied, or Approved with conditions, and say exactly what you approve. If you approve only part, say which part."

**For a counterproposal after a denial,** add part **2a, Earlier decision on this point**, directly after part 2: quote the denial exactly, with the approver's name, title and date, and add nothing. Part 2a does not count toward the word limit.

Keep the body (parts 1 to 10) under 250 words. The To, Cc and Subject lines do not count. If you must cut, shorten wording; never drop a deal fact that bears on the decision.

## Batch summary (shown to the seller)

| Request | To | Change | Decision needed |
|---|---|---|---|

Then three short lists: **Pre-approved (no request)**, **Not approvable (negotiate out or amend the matrix)**, **Questions for the matrix owner**. Then the missing-profile list. End with: "Confirm to send all requests."

## Follow-ups

Each follow-up is a draft for the seller to confirm. Never send one automatically.

| Situation | Draft |
|---|---|
| Reply is Partial or Unclear | To the same approver. Quote their reply, name the part that is open, and ask a yes/no question about that part only. |
| Missing co-approval | To the approver who has not replied. Say which co-approver has replied and what they decided. |
| Wrong authority | To the title the matrix names. Re-send the original request. Do not mention the earlier reply beyond what the record needs. |
| Denied | No follow-up to the approver. Tell the seller the standard stays, with a seller note (see below). Do not suggest or draft a counterproposal. If the seller asks for one, return to Stage 1 with it and route it to the level that covers it. The new request quotes the earlier denial word for word, so the new approver decides knowing it. |
| Authority unclear or Not in matrix | To the matrix owner. State the question, quote the cells or note the absence of a row, and list the options. Ask for a ruling. Do not recommend one. |
| No reply after the reminder period | A reminder to the approver, copying the seller. The reminder period is 2 business days after the request was sent unless the organization states another. Draft it; the seller confirms before it goes. |

## Seller note (for Denied and Not approvable)

A strict "no" is hard to deliver. Give the seller a short note they can use with the customer. It is a draft for the seller to adapt; the seller decides whether and how to use it.

**Contents, in this order**

1. **Where we stand.** One sentence: the standard position stays, and which term it is.
2. **What the standard says.** The standard position and the clause, quoted from the standard agreement or the matrix.
3. **A line the seller may say.** Two or three plain sentences for the customer. They state the position, are courteous, and make no promise.
4. **What not to say.** Do not share the approver's name, title or reasoning, and do not say the request was "close" or "might be reconsidered".

**Rules for the note**

- **Use only what the documents say.** Build it from the standard agreement, the matrix and the deal profile. Never invent a reason, a policy, a precedent or what "other customers" get.
- **The approver's reasoning is internal by default.** Quote it only if the approver said it may be shared. If the seller wants to share it, draft a one-line question to that approver asking permission.
- **Do not suggest a concession.** The note does not offer a lower position, a trade or a workaround. If the seller asks for a counterproposal, that is a new request (see the Denied row above).
- **Not approvable:** the same note, and tell the seller the term must be negotiated out or the matrix owner must amend the matrix. Never say it may be approved later.
- **Keep it under 120 words,** with no em-dashes, flattery or pressure.

## Rules

- A request informs the decision; it is not an argument for approving. No pressure, flattery or urgency.
- State facts from the profile as facts and opinions as opinions.
- Never describe an approver's earlier reply in a way that reads as pressure on the others. The one exception is a seller-requested counterproposal after a denial: quote the denial exactly and add nothing to it.
- Never invent a deal fact, a precedent or a customer reason.
- No em-dashes.

## Check before you finish

- Every routed deviation has exactly one request per required approver.
- Every request states the exposure with arithmetic, or says annual fees are not provided.
- Every request carries a recommendation, labeled.
- Nothing is marked sent. The app sends the batch.
