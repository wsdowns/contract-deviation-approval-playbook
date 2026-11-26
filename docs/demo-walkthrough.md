# Demo walkthrough (about 5 minutes)

## Setup

```bash
python app/server.py
```

Open http://localhost:8765 with the default demo mode. A model must be configured (`config.example.toml`). Analyzing a staged case usually takes under a minute with a fast hosted model, and longer with the `claude` command or a local model. The AI plays the approvers, nothing is emailed, and every record says SIMULATED.

## Script

| Step | On screen | Say |
|---|---|---|
| 1 | Home | A customer redlines a contract and each change needs the right approver. The record is proof of authority for the changes, not proof of the changes. |
| 2 | Contracts, staged Case 1. Open the Brightwater redline | This is what a seller receives. In real use the deal facts come from the CRM. |
| 3 | Summary | Code found every change and its matrix row. One AI reading named the level, code checked it, and the approvers came from the matrix. |
| 4 | Requests/Status | The requests went out. AI-played approvers decide through the same portal a person uses, and their exact words are recorded. |
| 5 | Approver portal ("Act as someone else") | What an approver sees: one request, the deal facts, and a clear choice. |
| 6 | Appeals | A denial can be appealed once, to the same approver. |
| 7 | Final Check | Upload the final revision. It passes only if every change in it was approved, and otherwise shows where it fails. |
| 8 | Audit the approvers | Every decision is kept in an append-only ledger for the matrix owner. |

Decisions made by AI-played approvers vary between runs, so check what was denied before narrating steps 6 and 7.

## Showing reminders and escalation

List a title under `[demo] silent_titles` in `config.toml`, start a case, then use "Move the demo clock to the next business day" on Requests/Status.

## What to say about limits

The companies and contracts are fictional. Demo approvals are simulated. The app works on the standard agreement with changes, not on a customer's own paper.
