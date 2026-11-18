# The maturity model

An organization should not start with rules. It should start with people deciding every deviation, learn from what they decide, and only then write rules to remove the decisions that never needed a person. This page describes that path in four stages.

Status: stage 1 works today, and the ledger that stage 2 needs is built. Stages 3 and 4 are designed and listed in `NEXT-PHASE.md`. They are not built.

## Stage 1. Manual

Every deviation goes to the approver the matrix names. The AI finds the changes, locates the rule, drafts the request and records the answer. People decide everything.

What you get: a complete approval record for every deal, and the data to learn from.

Move on when: you have the ledger running and at least a few months of decisions.

## Stage 2. Informed

The matrix owner reviews the approvals ledger on a schedule, quarterly to start. The review asks questions, not verdicts:

- Which terms are approved every time, with no conditions? The matrix may be sending a request up a level that never needed it.
- Which approvers approve everything, or approve nothing? See `docs/audit-and-ledger.md` for why neither pattern proves anything alone.
- Which terms take the longest, or come back conditional most often? The matrix may be unclear.
- How often does the seller concede something different from what was approved?

What you get: changes to the matrix, based on evidence. A term moves to a lower level, a threshold changes, or an approver is replaced or removed.

Move on when: a term is approved so consistently, under conditions you can state, that a person adds nothing.

## Stage 3. Rules

For those terms, the matrix owner writes a deterministic rule: this position is approved under these conditions, with no human in the loop. For example, a payment term of Net 45 on a deal under $100,000 with a standard customer.

The rule is checked by code against deal facts, never by the AI, and the owner signs it off. The record reads "approved by rule R-12, version 3, authorized by the General Counsel". See `docs/deterministic-rules.md`.

What you get: faster deals on routine changes, with the same traceability to a named person.

Move on when: rules are stable and you have a way to check that they still match what approvers would have decided.

## Stage 4. Monitored

Rules are not set and forgotten. Each has a review date and an off switch. A sample of rule-approved changes goes to a human for a second look, and the ledger compares rule outcomes with human outcomes. A rule that drifts is tightened or retired.

What you get: confidence that automation has not widened authority without anyone deciding to.

## What never changes at any stage

- The AI never approves.
- Positions the matrix marks not approvable always go to a person, or are refused.
- Anything the matrix or the rules do not cover goes to the matrix owner.
- The record shows who or what approved, on whose authority.
