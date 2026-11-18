# The playbook

Prompts for an AI partner that helps a seller get contract changes approved under a delegation of authority (DoA) matrix. They work with any contract type and any matrix in the format described in [../docs/matrix-format.md](../docs/matrix-format.md).

| File | Purpose |
|---|---|
| [00-standing-instructions.md](00-standing-instructions.md) | Rules for every stage. Give these first |
| [01-identify.md](01-identify.md) | Stage 1: list every changed term |
| [02-locate.md](02-locate.md) | Stage 2: find the matrix row and the lowest covering level |
| [03-draft-requests.md](03-draft-requests.md) | Stage 3: draft one request per approver, and follow-ups |
| [04-record-decisions.md](04-record-decisions.md) | Stage 4: record the actual decisions, then check the final contract |

The record's format is in [../docs/approval-record.md](../docs/approval-record.md). The escalation path and statuses are in [../docs/escalation-path.md](../docs/escalation-path.md).

## Running it by hand

**Pass the setup gate first.** The playbook sends contract terms and pricing to an AI model, so not every model will do. For real deals you need an environment with zero data retention (in writing) or a private instance, with no training on your inputs, sign-off on record, and a model that passes a qualification run on Case 1. The full gate is in [../docs/ai-environment.md](../docs/ai-environment.md). With stand-in data only, any capable AI chat works.

0. **Check the gate.** Confirm the AI environment passes `docs/ai-environment.md`, and note it in the record header.
1. **Start the run.** Paste `00-standing-instructions.md`. Attach the matrix files, the standard agreement, the deal profile and the contract under review.
2. **Stage 1.** Paste `01-identify.md`. Check the deviations table against the contract yourself.
3. **Stage 2.** Paste `02-locate.md`. Read every outcome, especially Authority unclear and Not in matrix.
4. **Stage 3.** Paste `03-draft-requests.md`. Review the batch summary, then send the requests yourself (or, in an automated setup, confirm once and the system sends them).
5. **Stage 4.** Paste `04-record-decisions.md`, then give the AI each reply as it arrives, one at a time. When the contract is final, tell the AI what it says.
6. **Save the outputs** with the inputs under `runs/`.

In an automated deployment, sending and receiving are handled by the system and the seller confirms once; see [../docs/seller-experience.md](../docs/seller-experience.md). The prompts are the same.

## Using it with your own contracts

Replace four inputs: the standard agreement, the matrix files, the deal profile, and the contract under review. The prompts do not mention any contract type, company or person.

## What the prompts do not do

They do not approve anything, decide who has authority when the matrix is unclear, or send anything themselves. Approving, and deciding who has authority, are human decisions.

Note: these prompts are the manual version of the process, for use in any chat AI. The app (`app/`) does most of these steps in code and asks the AI one question per contract; see `docs/how-it-decides.md`. The app's own prompts are in `app/prompts/`.
