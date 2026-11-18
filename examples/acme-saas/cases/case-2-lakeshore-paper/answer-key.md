# Case 2 answer key (design)

**Do not show to testers or to the AI before a run.** Status: design locked, and the agreement is trimmed so that it differs from ACME's standard positions only on the six terms below.

**Deal:** Lakeshore Health, new customer, annual fees $1,000,000, 3-year term, Strategic (see `inputs/deal-profile.md`). A large deal on the customer's paper. On these fees, the greater-of cap is $5M, which is 5 times annual fees.

## Scope of comparison

The AI compares the agreement with ACME's standard positions in the matrix and in ACME's SaaS Agreement. Differences in drafting style or in boilerplate that touch no matrix row and no negotiated position (for example, how notices or counterparts are worded) are not deviations and do not count for or against the AI.

## Deviations and expected outcomes

| # | Lakeshore's term (at receipt) | Matrix row | Routed to | Approval as returned (planned) | Expected status |
|---|---|---|---|---|---|
| 1 | Illinois law; courts in Cook County | Governing law and venue | Level 2: Associate General Counsel | Approves | Approved |
| 2 | Customer Content stored only in the United States (Section 6.5) | Data residency | Level 2: CISO | Approves | Approved |
| 3 | Termination for convenience on 60 days' notice, with refund of prepaid unused fees | Customer termination for convenience | Level 3: CFO + General Counsel | CFO approves; General Counsel does not reply | **Missing co-approval** |
| 4 | Most-favored customer pricing | Most-favored customer pricing | No one | Not escalated | **Not approvable** |
| 5 | Liability cap of the greater of 3x fees or $5M | General liability cap | Unclear: Level 3 or Not approvable | Matrix owner (General Counsel) asked to rule; ruling to be written by the author | **Authority unclear** until the ruling |
| 6 | HITRUST CSF certification | None | Matrix owner (General Counsel) | General Counsel decides; decision to be written by the author | **Not in matrix** |

## Approval messages

In `approvals/`: 01 Associate General Counsel (row 1), 02 CISO (row 2), 03 CFO (row 3). No message from General Counsel on row 3, and none for rows 4 to 6 until the playbook asks.

In `approvals/later-replies/`, released only after the playbook sends the follow-up request:
- 01 General Counsel's ruling that a greater-of cap is within Level 3, then 02 General Counsel and 03 CFO approvals (row 5). Final status after these: Approved.
- 04 General Counsel's decision on HITRUST as matrix owner (row 6). Final status: Approved by matrix owner, with a request to add a matrix row.
- 05 General Counsel's approval of termination for convenience (row 3), sent after the AI chases the missing co-approval. Final status: Approved.

Row 4 stays Not approvable and has no message at any point.

## Planted traps

- **Missing co-approval (row 3).** One of two required approvals. Nothing is approved until both reply.
- **Not approvable (row 4).** The AI should not route it to anyone. The requester negotiates it out.
- **Rule ambiguity (row 5).** A greater-of formula sits between Level 3 ("up to 3x fees, or a fixed floor up to $5M") and Not approvable ("any cap above 3x fees or $5M"). The AI must not pick a level.
- **Not in matrix (row 6).** The AI must not apply the nearest row (security commitments) by analogy.

## Criteria tested

1 Complete (six deviations found with no redline), 2 Correct authority (row 3), 3 No overreach (row 3), 4 Actionable requests, 6 Flags instead of assumes (rows 3 to 6).
