# The contract delegation of authority framework

This is a framework for managing contract deviations under a delegation of authority (DoA). It describes who may approve each change to a contract, how a request reaches that person, how the answer is recorded, and where an AI partner helps without ever holding authority.

The Contract Deviation Approval Playbook in this repository is the working implementation. This page explains the framework behind it, so it can be adopted, audited or rebuilt with different tools.

## The problem it solves

A customer changes your contract. Each change needs approval from the person your DoA names for that term. In practice the seller has to work out which clause changed, find the right rule, work out who must approve it, write the request, chase the answer, and later prove that each change had authority behind it. The result depends on the individual seller. Approvals come back partial, conditional, from the wrong person, or not at all, and a clean-looking record that overstates what was approved is worse than none.

## What the framework produces

An approval record: one row for every change a customer made, showing who had authority to approve it, what that person actually said, in their exact words, and whether the final contract matches.

The record is proof of authority for the changes. It is not proof of the changes. It says who agreed to what, not whether the contract text is right.

## Principles

1. **Automate the plumbing, never the authority.** Code finds, routes, sends and records. The AI reads wording and names the level that covers it, and code checks that reading. People approve. The AI never approves a real change and never names an approver.
2. **Authority comes from one source.** The DoA matrix is the only statement of who may approve what. If the matrix does not settle a change, the app says so and refers it to the title the organization names for that (the matrix owner if none is named). It does not guess.
3. **Approvers decide, and may say no.** An approval is permission, not an obligation. A denial is recorded as a denial.
4. **Negotiation protects the company.** Keep terms close to the standard. The seller, not the AI, decides whether to appeal a denial or propose a different position in a new round.
5. **Record what was said, not what was meant.** Conditions, limits and caveats are quoted. Anything short of a clear decision is not an approval.
6. **Flag instead of assuming.** When authority is unclear or an approval is incomplete, the app says so.
7. **The seller concedes only what was approved.**

## The parts

| Part | What it is | Where it lives |
|---|---|---|
| The DoA matrix | Who may approve each term, by level, and which positions are not approvable | `doa_matrix.csv` |
| Roles and people | The titles the matrix may name, and who holds each title today | `roles.csv`, `people.csv` |
| Process settings | Who requests, who owns the matrix, who keeps records, who checks before signature, and the approvals mailbox | `settings.csv` |
| The standard agreement | The positions every change is measured against | Your standard contract |
| The deal profile | Customer, fees, term, strategic or standard, upside, competition, data types, precedent. Normally comes from the CRM | `docs/deal-profile.md` |
| The prompts | The app's own prompts, and a manual version of the process for any AI chat | `app/prompts/`, `playbook/` |
| The AI environment | The model that runs the prompts, qualified and approved before real use | `docs/ai-environment.md` |
| The approval record | The output, with a fixed format and status vocabulary | `docs/approval-record.md` |
| The app | The seller's screens, the approver portal and the audit page | `app/` |
| The approvals ledger | Append-only history of decisions and records | `docs/audit-and-ledger.md` |

## Who does what

| Role | Responsibility |
|---|---|
| Requester (for example the Account Executive) | Hands over the contract, watches status, may appeal a denial, and concedes only approved items |
| Approver | Decides each request that names their title, in the portal |
| Deal Desk, or whoever handles terms not in the matrix | Finds out what is needed for a change the matrix does not settle, and records the outcome and the authority relied on |
| Matrix owner (for example the General Counsel) | Owns the matrix and rules on anything it does not cover |
| Record custodian (for example the Contracts Manager) | Files the original replies, the approval record and the signed contract together |
| Pre-signature check (for example the Deal Desk Manager) | Checks the final contract against the approvals before signature |
| The AI partner | Names the covering level and explains the change. Holds no authority |

## How a deviation moves

1. **Identify.** Code compares the uploaded contract with the standard and lists every difference.
2. **Locate.** Code places each change on a matrix row. One AI reading per contract names the level; code checks it and takes the approvers from the matrix cell.
3. **Request.** Code writes one request per approver from a fixed template, with the change quoted, the deal context and the exact question.
4. **Send.** By default requests go out once every recipient matches a known approver, copying the seller and the approvals mailbox. An organization can require one confirmation.
5. **Decide.** The approver signs in to the portal and approves, approves with conditions, denies, delegates or asks a question.
6. **Follow up.** A silent request is reminded on a business-day schedule, then escalated to the seller and the matrix owner together, and to a standing fallback contact if the approver has one. The seller may appeal a denial once.
7. **Record and check.** Code builds the approval record. The seller uploads the final contract, and code passes it only if every change in it was approved in those words.

## Decision statuses

Approved, Approved (pre-approved), Conditional, Missing co-approval, Awaiting reply, Appeal pending, Referred to Deal Desk, Not approvable and Denied. The manual playbook adds statuses for ambiguous email replies. Their meaning and the ambiguity rules are in `docs/escalation-path.md` and `docs/approval-record.md`.

## Controls

- **Setup gate for the AI environment.** Before a real deal goes in, the environment needs written zero data retention or a private instance, no training on inputs, confidentiality that covers customer terms, access control and audit, known data location and deletion, a recorded sign-off, and a business account. See `docs/ai-environment.md`.
- **Qualification run.** Before real use, run the worked Case 1 on the chosen model and compare the record with its answer key. A model that misses changes or names the wrong covering level is not fit.
- **Answer keys stay hidden** from the AI and from testers.
- **Recipients checked in code** before anything is sent, with an optional confirmation click.
- **Stand-in data banner** in the app while the gate is not passed.

## How it grows

The framework starts manual and matures. People decide every deviation at first. An approvals ledger records every decision, so the matrix owner can audit approvers and terms. Later, the owner writes deterministic rules that approve routine changes under stated conditions, still on a named person's authority. See `docs/maturity-model.md`, `docs/audit-and-ledger.md` and `docs/deterministic-rules.md`. The ledger is built; the rules are designed, not built.

## Known limits

- The worked example uses three fictional cases and a small number of runs. It shows the method works, not how often.
- Approvers decide in a portal. Email carries only a link. Single sign-on beyond a proxy header is designed, not built. Demo mode has the AI play the approvers, and labels everything it produces as simulated.
- The app decides only on what is entered in the portal. Email replies are not read.
- The record is only as trustworthy as the sign-in method that identifies the approver.
- Later rounds and the signed-copy check work from uploaded Word, PDF or text files. A scanned signed copy cannot be checked, and a round continues from an earlier upload that you choose by hand.
- Changes can be placed on the matrix only in Word files. Every change in a PDF or text upload is referred.

## Adapting the framework

Replace the matrix, roles, people and settings with your own, point the app at your standard agreement, choose a qualified model, and pass the setup gate. The steps are in `docs/setup-guide.md`. Nothing in the framework depends on SaaS: the matrix format fits any contract type.
