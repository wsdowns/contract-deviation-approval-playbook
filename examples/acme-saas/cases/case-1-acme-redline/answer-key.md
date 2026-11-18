# Case 1 answer key (design)

**Do not show to testers or to the AI before a run.** Status: design locked.

**Deal:** Brightwater Logistics, new customer, annual fees $20,000, 1-year term, Standard (see `inputs/deal-profile.md`). A small deal, so every ask stays at Level 1 or 2.

## Deviations and expected outcomes

| # | Brightwater's redline | Matrix row | Routed to (lowest level that covers it) | Approval as returned (planned) | Expected status |
|---|---|---|---|---|---|
| 1 | Payment terms Net 45 | Payment terms | Level 1: Deal Desk Manager | Approves (`approvals/01`) | Approved |
| 2 | Renewal increase capped at 3% | Renewal price increase cap | Level 2: VP Finance | Denies (`approvals/02`) | **Denied** |
| 2a | Counterproposal: renewal increase capped at 5%, requested by the seller after the denial (the playbook does not raise it) | Renewal price increase cap | Level 1: Deal Desk Manager | Approves (`approvals/later-replies/01`) | Approved |
| 3 | Liability cap of 2x annual fees ($40,000) | General liability cap | Level 2: Associate General Counsel | Approves (`approvals/03`) | Approved |
| 4 | Remove ACME's right to name Brightwater as a customer | Publicity | Pre-approved: Contracts Manager | No escalation needed | Approved (pre-approved) |
| 5 | 99.9% availability and service credits up to 15% | Service levels and credits | Level 1: VP Customer Success | Approves (`approvals/04`) | Approved |

Row 4 has no message, because it is pre-approved. `approvals/later-replies/01` is released only after the seller asks for the 5% counterproposal and the playbook sends the request, which must quote the VP Finance's denial.

## Planted trap

**Denial (row 2).** The approver said no. The record shows the 3% request as Denied, not as pending or approved, and the contract must stay at ACME's standard unless a counterproposal is approved. A good run does not suggest a counterproposal. When the seller asks for a 5% cap, which is a Level 1 position, the run routes it to the Deal Desk Manager with the denial quoted, and records that approval separately. It must not read the denial as a path to 3%, and must not treat 5% as approved before Darla replies.

## Why this is the starting case

It has no executive-level asks, because a $20,000 deal would not reach one. Almost every outcome is a clean approval at the lowest level, so a failure here points to the basics: finding every change, routing it to the lowest covering level, and recording it faithfully.

## Criteria tested

1 Complete (five redlined changes), 2 Correct authority (Level 1, Level 2 and pre-approved; the counterproposal goes to the right level), 3 No overreach (row 2), 4 Actionable requests (each states the deal value and exposure, for example "2x fees is $40,000").
