# Deterministic rules for delegated approval

Status: designed, not built. This page is the specification.

A rule says: this position is approved under these conditions, without a person deciding each time. It extends the matrix's existing Pre-approved status, which is unconditional, with conditions.

## The principle

The AI is not the approver. The matrix owner decides, once, that a position is acceptable under stated conditions, and signs the rule. After that, code checks whether a deal meets the conditions. The check is the same every time. If it passes, the change is approved by the rule, on the authority of the person who signed it. If it fails for any reason, the change goes to a human approver as it does today.

## Where rules live

A separate file, `auto_rules.csv`, next to the matrix. The matrix stays readable and unchanged.

| Column | Meaning |
|---|---|
| Rule ID | For example R-12 |
| Term | The matrix term the rule covers |
| Covered position | Exactly what is approved, for example "Payment within 45 days of invoice" |
| Condition | Tests on deal facts, joined by AND, for example `deal_value < 100000 AND term_months <= 24 AND data_types == none` |
| Authorized by | The title that signed the rule, normally the matrix owner |
| Effective | Start date |
| Review by | The date the rule must be reviewed or lapses |
| Status | Active, suspended or retired |

## How a rule is checked

1. Identify the change and its matrix row as usual.
2. Look for an active rule for that term whose covered position matches the change exactly. If none, go to the human approver.
3. Read the deal facts from the system of record. If any fact the condition needs is missing, go to the human approver.
4. Test the condition. If it fails, go to the human approver.
5. If it passes, record the change as approved by the rule, with the rule ID, version and authorizing title.

The test is a plain comparison in code. The AI does not interpret conditions or decide whether they hold.

## Guardrails

- **Deal facts come from the CRM, not the seller.** Today a seller can edit the deal profile. A rule that reads seller-typed facts can be gamed, so rules must read from the system of record.
- **Not-approvable positions never get a rule.** The matrix says no one may approve them.
- **Anything uncovered goes to the matrix owner.**
- **Exact match only.** A rule covers one stated position. A near match goes to a person.
- **Every rule expires.** The review-by date is mandatory. A rule past its date does not fire.
- **Kill switch.** Setting a rule to suspended stops it immediately.
- **Sampled review.** A share of rule-approved changes goes to a human for a second look, and the ledger compares the two.
- **Changes are versioned.** A rule's text is never edited in place. A change is a new version, and the ledger records which version fired.

## Choosing what to automate

Use the ledger (`docs/audit-and-ledger.md`). A good candidate is a term that is approved consistently, in a narrow band of conditions you can state, with no conditions attached by the approver. Start with one rule, watch it for a quarter, then add more.
