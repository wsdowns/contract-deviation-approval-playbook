# The seller's experience

The playbook is designed so the seller does as little as possible. The seller hands over a contract and confirms one batch of requests. The playbook does the rest, and speaks up only when a human decision is needed.

The seller is the **Requester** named in `settings.csv`, for example the account executive.

## What the seller does

1. **Opens the Contracts page and hands over the contract, answering a short deal profile.** From Home the seller chooses Start Here: Demo (Staged Examples) or Seller's Associate: Your Contracts. The Contracts page lists the active contracts, each with its own steps (Summary, Requests/Status, Appeals, Final Check, Archive), and offers the upload form (or the staged examples) below the list. ACME's standard agreement with the customer's changes (a Word file is best), plus about eight questions about the deal. A contract on the customer's own paper is not supported yet. See [deal-profile.md](deal-profile.md).
2. **Reviews one summary.** For example: "5 changes found. 4 need approval from 6 people. 1 is pre-approved. Ready to send?" The seller can correct a misread change here.
3. **Nothing to confirm by default.** Requests go out automatically once every recipient has been matched to a known approver, with the seller copied. An organization can set the app to wait for one confirmation instead.
4. **Watches the status.** For example: "5 of 6 decided: 4 approved, 1 with conditions. Waiting on the CEO." The page updates by itself, and shows each approver's exact words.
5. **Appeals a denial, once, if something about the deal is special.** The seller picks the denied change and may add new context. The same approver decides again. After that, the decision stands. The seller never goes over an approver's head.
6. **Uploads the final contract for a pass or fail check, then archives the deal.** Archiving can be done at any time: open requests are withdrawn, the deal leaves the seller's list, and the audit ledger keeps the record. In a real setup a CRM close would trigger the same archive. The contract at its latest revision, with approved changes accepted and denials removed or explained. If it contains a change that was not approved, the result shows where. Then the finished record goes to the people who file and check it.

## What the playbook automates

- Finding each change and the matrix row that governs it (Stages 1 and 2).
- Drafting one request per approver (Stage 3).
- Sending the requests from the approvals mailbox on the seller's behalf, copying the seller, after the seller's one confirmation.
- Watching the approvals mailbox and matching each reply to the request it answers.
- Matching each sender to a title through `people.csv`, as of the reply date.
- Recording each decision with its exact words and a status (Stage 4).
- Reminding approvers who have not replied.
- Drafting a short seller note for each denial, so the seller has courteous words for the customer. The note never offers a concession and never shares the approver's reasoning unless the approver allows it.
- Sending the finished record to the record custodian, and a "ready to check" notice to the pre-signature check role.

## What it never automates

- **Marking anything approved.** A change is Approved or Conditional only when the right title has said so. A friendly reply is not an approval.
- **Acting on a reply from someone who does not hold the named title.** It is recorded as Wrong authority and re-sent to the right title.
- **Choosing a level when the matrix is unclear.** It flags Authority unclear and asks the matrix owner.
- **Appealing to anyone but the approver who decided.** Whether an approver consults their own manager is their business, outside the system.

The principle: **automate the plumbing, never the authority.** The seller also does not decide whether to concede: approvers decide, and may deny. An approval is permission to concede, not an instruction to, and the seller may hold it unused. See [escalation-path.md](escalation-path.md#approval-is-permission-not-an-obligation).

## How this is tested

Sending and receiving use a simulated mailbox, so every run is reproducible and no real email is involved.

- **Outbox:** whatever the playbook sends is written to an outbox folder.
- **Inbox:** the approvals in `approvals/` are the replies. A reply is released into the inbox only when the matching request appears in the outbox.
- **Later replies:** files in `approvals/later-replies/` are released only after the playbook sends the follow-up they answer.

The hand-off tester plays the seller. They get the contract, confirm the batch, and watch the status. They never see the answer key. A real email adapter can replace the simulated mailbox without changing the playbook.

## Who needs to be told

| Event | Told |
|---|---|
| Batch confirmed and sent | Approvers (the requests), the seller (a copy) |
| Reply received | Seller (status update) |
| Reply flagged | Seller (follow-up draft to confirm) |
| No reply after the reminder period | Seller, and the approver (reminder) |
| All changes Approved or Conditional | Record custodian (the record), pre-signature check role (ready to check) |
