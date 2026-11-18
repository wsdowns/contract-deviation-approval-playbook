# The contract delegation of authority framework

This is a framework for managing contract deviations under a delegation of authority (DoA). It describes who may approve each change to a contract, how a request reaches that person, how the answer is recorded, and where an AI partner helps without ever holding authority.

The Contract Deviation Approval Playbook in this repository is the working implementation. This page explains the framework behind it, so it can be adopted, audited or rebuilt with different tools.

## The problem it solves

A customer changes your contract. Each change needs approval from the person your DoA names for that term. In practice the seller has to work out which clause changed, find the right rule, work out who must approve it, write the request, chase the answer, and later prove that each change had authority behind it. The result depends on the individual seller. Approvals come back partial, conditional, from the wrong person, or not at all, and a clean-looking record that overstates what was approved is worse than none.

## What the framework produces

An approval record: one row for every change a customer made, showing who had authority to approve it, what that person actually said, in their exact words, and whether the final contract matches.

The record is proof of authority for the changes. It is not proof of the changes. It says who agreed to what, not whether the contract text is right.

## Principles

1. **Automate the plumbing, never the authority.** The AI finds, routes, drafts and records. People approve. The AI never approves a change, never decides who has authority, and never sends on its own.
2. **Authority comes from one source.** The DoA matrix is the only statement of who may approve what. If the matrix does not cover a change, the AI says so and routes it to the matrix owner. It does not guess.
3. **Approvers decide, and may say no.** An approval is permission, not an obligation. A denial is recorded as a denial.
4. **Negotiation protects the company.** Keep terms close to the standard. The seller, not the AI, decides whether to ask for a different position after a denial.
5. **Record what was said, not what was meant.** Conditions, limits and caveats are quoted. If a reply is ambiguous, the record flags it instead of rounding it up to an approval.
6. **Flag instead of assuming.** When authority is unclear, information conflicts or an approval is incomplete, the AI speaks up.
7. **The seller concedes only what was approved.**

## The parts

| Part | What it is | Where it lives |
|---|---|---|
| The DoA matrix | Who may approve each term, by level, and which positions are not approvable | `doa_matrix.csv` |
| Roles and people | The titles the matrix may name, and who holds each title today | `roles.csv`, `people.csv` |
| Process settings | Who requests, who owns the matrix, who keeps records, who checks before signature, and the approvals mailbox | `settings.csv` |
| The standard agreement | The positions every change is measured against | Your standard contract |
| The deal profile | Customer, fees, term, strategic or standard, upside, competition, data types, precedent. Normally comes from the CRM | `docs/deal-profile.md` |
| The prompts | Standing instructions and four stage prompts, neutral to contract type | `playbook/` |
| The AI environment | The model that runs the prompts, qualified and approved before real use | `docs/ai-environment.md` |
| The approval record | The output, with a fixed format and status vocabulary | `docs/approval-record.md` |
| The seller app | A local web app that walks a seller through the steps | `app/` |

## Who does what

| Role | Responsibility |
|---|---|
| Requester (for example the Account Executive) | Hands over the contract, confirms the requests, decides next moves, and concedes only approved items |
| Approver | Decides each request that names their title. Replies to the approvals mailbox |
| Matrix owner (for example the General Counsel) | Owns the matrix and rules on anything it does not cover |
| Record custodian (for example the Contracts Manager) | Files the original replies, the approval record and the signed contract together |
| Pre-signature check (for example the Deal Desk Manager) | Checks the final contract against the approvals before signature |
| The AI partner | Identifies, locates, drafts and records. Holds no authority |

## How a deviation moves

1. **Identify.** Compare the contract under review with the standard. List every changed term, and treat parts in the same matrix cell with the same approvers as one change.
2. **Locate.** Find each change's matrix row, level and approver. Flag anything the matrix does not cover.
3. **Draft.** Write one request per approver that stands alone, with the change quoted, the deal context and the exact question.
4. **Send.** The seller confirms one batch. Requests go to the approver, copying the seller and the approvals mailbox.
5. **Record.** Approvers reply to the approvals mailbox. The AI checks the sender against the people list and the title against the routing, then records each decision with the approver's words.
6. **Follow up.** A request nobody answers is reminded on a business-day schedule, then escalated to the seller and the matrix owner together, and to a standing fallback contact if the approver has one. For other open items, the AI drafts rulings requests and re-sends to the right title. After a denial, only the seller can ask for a different position.
7. **Final check.** The seller states what the final contract says. Every change is checked against its approval, and the outcome is recorded as conceded as approved, not conceded, or conceded differently.

## Decision statuses

Approved, Approved (pre-approved), Conditional, Partial, Unclear, Missing co-approval, Wrong authority, Authority unclear, Not in matrix, Not approvable, Denied. Their meaning and the ambiguity rules are in `docs/escalation-path.md` and `docs/approval-record.md`.

## Controls

- **Setup gate for the AI environment.** Before a real deal goes in, the environment needs written zero data retention or a private instance, no training on inputs, confidentiality that covers customer terms, access control and audit, known data location and deletion, a recorded sign-off, and a business account. See `docs/ai-environment.md`.
- **Qualification run.** Before real use, run the worked Case 1 on the chosen model and compare the record with its answer key. A model that misses changes, picks authority levels itself or reads silence as approval is not fit.
- **Answer keys stay hidden** from the AI and from testers.
- **Human confirmation** before anything is sent.
- **Stand-in data banner** in the app while the gate is not passed.

## How it grows

The framework starts manual and matures. People decide every deviation at first. An approvals ledger records every decision, so the matrix owner can audit approvers and terms. Later, the owner writes deterministic rules that approve routine changes under stated conditions, still on a named person's authority. See `docs/maturity-model.md`, `docs/audit-and-ledger.md` and `docs/deterministic-rules.md`. The ledger is built; the rules are designed, not built.

## Known limits

- The worked example uses three fictional cases and a small number of runs. It shows the method works, not how often.
- Approvers decide in a portal. Email carries only a link. Single sign-on beyond a proxy header is designed, not built. Demo mode has the AI play the approvers, and labels everything it produces as simulated.
- Matching a reply to its request at scale is hard. A unique request ID is designed but not yet built.
- The record proves linkage between request and reply, not that a reply is authentic.
- Later rounds and the signed-copy check work from uploaded Word, PDF or text files. A scanned signed copy cannot be checked, and a round continues from an earlier upload that you choose by hand.
- Only text contracts are handled. Tracked-changes Word files are read through a text form.

## Adapting the framework

Replace the matrix, roles, people and settings with your own, point the app at your standard agreement, choose a qualified model, and pass the setup gate. The steps are in `docs/setup-guide.md`. Nothing in the framework depends on SaaS: the matrix format fits any contract type.
