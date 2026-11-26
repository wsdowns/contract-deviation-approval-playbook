# Roadmap

What is built, what is next, and the decisions behind it.

## Built

- Configuration file with four model backends and a setup gate for real data.
- Contract upload: Word tracked changes, PDF or text; untracked edits found; later rounds; signed-copy check; refusal of a customer's own paper.
- Placement and routing in code, one AI reading per contract checked against the matrix, requests from a fixed template.
- Approver portal with local logins or a proxy header, delegation, questions, send mode, recipient checks.
- Deal Desk referrals for terms the matrix does not settle.
- Reminders and escalation on business days.
- Requests/Status, one appeal per denial, pass or fail final check, archive.
- Append-only approvals ledger, audit page, CSV export.
- Demo mode with AI-played approvers and a demo clock.
- Separate current deal and jobs for each signed-in seller.
- A private deployment behind HTTPS at SELLERSASSOCIATE.COM, with fictional data.

## Next

1. **Deterministic rules** (`docs/deterministic-rules.md`), including numeric rules for levels so the AI's level can be checked or replaced.
2. **Scripted qualification check** that runs Case 1 on a chosen model and compares the result with its key.
3. **Spending limit** per user and per day, with a budget alert.
4. **Single sign-on (OIDC)**; end sessions on sign-out; administrator password reset.
5. **Answering questions:** let the seller reply to an approver inside the app.
6. **Record header:** customer, deal value, matrix version and AI environment on the record itself; deliver the finished record to the custodian.
7. **Retry failed notification emails** and show failures to the matrix owner.
8. **Ledger:** a correction entry, and reminder counts in the views.
9. **Own paper:** a method for contracts on a customer's paper.
10. **Scale:** move in-memory state to a database, run behind a production web server.
11. **Custom headings:** an optional AI-assisted placement of customer-added sections the matrix does not list, off by default.
12. **CRM connection** (`docs/crm-integration.md`).

## Evidence still needed

- An independent hand-off test.
- Live email with real approvers.
- More runs, more cases and more than one model, to measure how often it fails.
- Use of the audit page on real approval history.

## Design decisions

- The portal is the only way an approver responds. Email notifies and carries a link.
- Requests send automatically after code checks every recipient; `confirm` is available.
- Approvers have an obligation to act. Silence is escalated to the seller and the matrix owner together, and is never approval.
- Terms the matrix does not settle go to the Deal Desk, one request per change. Its stated authority is recorded, not verified.
- The seller concedes only what was approved, may appeal a denial once, and never goes over an approver's head.
- The final check is a pass or fail upload with no AI.
- Archiving withdraws open requests and keeps the history. A CRM close would trigger it.
- Headings and Key Terms field names are the matching keys, because the Word file has no section numbers.
- Matrix design questions for adopters: separate the approver from the checker, and decide whether a lower level may approve after a higher level denied.

## Observed on Haiku 5.5 (live runs, 2026-11-18)

- Case 1: all runs match the answer key. Case 3: all runs match. Case 2: governing law, data residency, most-favored pricing (not approvable) and HITRUST (unclear) match in every run; the greater-of liability cap is "unclear" in most runs (the key) and once "not approvable"; termination for convenience routes to CFO and General Counsel in most runs and was "unclear" in one. An "unclear" always goes to the matrix owner, never to a wrong approver.
- One analysis takes about 15 to 20 seconds for a five-change contract and 30 to 45 for Case 2's eight changes.
