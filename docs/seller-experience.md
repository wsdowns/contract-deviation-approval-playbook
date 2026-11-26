# The seller's experience

The playbook is designed so the seller does as little as possible. The seller hands over a contract. The app does the rest, and speaks up only when a human decision is needed.

The seller is the **Requester** named in `settings.csv`, for example the account executive. Who may sign in as a seller is listed in `sellers.csv`.

## What the seller does

1. **Opens the Contracts page and uploads the contract.** From Home the seller chooses Start Here: Demo (Staged Examples) or Seller's Associate: Your Contracts. The upload is the organization's standard agreement with the customer's changes (a Word file with tracked changes works best), plus a few facts about the deal. A contract on the customer's own paper is not supported yet. See [deal-profile.md](deal-profile.md).
2. **Reads the Summary.** Every change, the matrix row, who may approve it, and the drafted requests.
3. **Sends nothing by hand.** By default requests go out as soon as every recipient has been matched to a known approver, with the seller copied. An organization can set the app to wait for one confirmation instead.
4. **Watches Requests/Status.** Where each change stands, with each approver's exact words, reminders, delegations and any question an approver asked. The page updates by itself.
5. **Appeals a denial, once, if something about the deal is special.** The same approver decides again. After that, the decision stands. The seller never goes over an approver's head.
6. **Runs the Final Check, then archives the deal.** The seller uploads the contract at its latest revision, with approved changes accepted and denials removed. It passes only if every change in it was approved in those words, and shows where it fails. Archiving can be done at any time: open requests are withdrawn, the deal leaves the seller's list, and the ledger keeps the history.

## What the app automates

- Finding each change and placing it on a matrix row, in code.
- One AI reading per contract to name the covering level, checked by code.
- Writing one request per approver from a fixed template, and one referral to the Deal Desk for each change the matrix does not settle.
- Sending notifications with a link to the portal, copying the seller and the approvals mailbox.
- Recording each decision with its exact words, and building the approval record.
- Reminding and escalating when an approver is silent.
- Drafting a short line the seller may adapt for each denial. It offers no concession and does not share the approver's words.
- Adding decisions and records to the approvals ledger.

## What it never automates

- **Marking anything approved.** A change is Approved or Conditional only when the right title has decided so in the portal, or when the matrix itself pre-approves it. In demo mode the AI plays the approvers and every record says so.
- **Letting someone else decide.** Only the assigned approver, their delegate or their listed fallback contact can open a request.
- **Settling an unclear matrix.** The change is referred, never guessed.
- **Appealing to anyone but the person who decided.**

The principle: **automate the plumbing, never the authority.** An approval is permission to concede, not an instruction to, and the seller may hold it unused. See [escalation-path.md](escalation-path.md#approval-is-permission-not-an-obligation).

## Not built yet

- The seller cannot answer an approver's question inside the app; they reply outside it, and the request stays open.
- The app does not send the finished record to the record custodian or a notice to the pre-signature check role. Those steps are done by people.

## Trying it without sending anything

Demo mode writes each message to the run folder instead of emailing it, and the AI plays the approvers. The automated tests use a stand-in model and need no AI at all. Live mode sends real email. See [setup-guide.md](setup-guide.md).

## Who is told

| Event | Told |
|---|---|
| Request sent | The approver, with the seller and the approvals mailbox copied |
| Decision recorded | The seller, with the approver and the mailbox copied |
| Delegated | The delegate, with the approver, seller and mailbox copied |
| Question asked | The seller, with the approver and mailbox copied |
| Reminder | The approver and any delegate, with the seller and mailbox copied |
| Escalation | The seller and the matrix owner, and any fallback contact |
| Seller archives the deal | Approvers with open requests |
