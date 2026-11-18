# Stage 1: Identify each changed term

## Purpose

List every substantive change between the contract under review and the organization's standard positions, so that none is missed.

## Inputs

- The standard positions (standard agreement and the matrix `Standard position` column).
- The contract under review: a redline, or the counterparty's paper as received.

## Steps

1. Read the standard positions first. Note the position on every term the matrix covers.
2. Read the contract under review in full. Do not stop at the sections you expect to differ.
3. **For a redline:** list every inserted, deleted or modified provision.
   **For paper as received:** there are no marked changes, so compare each provision with the standard and list each substantive difference. Include provisions the standard has no equivalent for.
4. **One deviation per requested change.** Combine edits that together make one change. If a change has parts that could be approved separately, list the parts as sub-items (for example 4a and 4b).
5. **Follow each change through the document.** A change can take effect through more than one clause: a defined term, a cross-reference, an exclusion, an exception to a cap. Under each deviation, list every clause through which it takes effect. If you find an effect through a clause the counterparty did not edit, say so.
6. **Do not list** differences in wording that change no right, obligation, number, period or remedy. Name them briefly in a separate list so a human can check your judgment.
7. If a provision cannot be compared because the standard says nothing about it, list it as a deviation of kind **Added** and say that no standard position exists. If the agreement is silent but the matrix has a `Standard position` for the term, use the matrix position as the standard, list the deviation as **Changed**, and note "standard from matrix; agreement silent". If the agreement and the matrix disagree, use the matrix position and flag the difference.
8. **One matrix cell, one deviation.** When a matrix cell names several figures as one position (for example an availability level and a credit cap), list one deviation and show each figure as a sub-item. Split into separate deviations only when the matrix has separate rows or levels for the parts. **Parts that fall in the same matrix cell and need the same approvers are never separate rows, separate requests or separate record entries**: write them in one row, in the Requested position, and name them in Notes. An approver who replies "Approved" to the cell has answered all of them. Sub-items (4a, 4b) are only for parts that different approvers decide, or that a later counterproposal changes.
9. **Counterproposals.** If the seller proposes a position without giving clause text, draft the clause by changing only the disputed figure or words in the earlier redline wording. Label it "assumed wording, seller to confirm" and never present it as the counterparty's words. If there is no earlier wording, ask the seller for it.
10. If the redline's clause numbers do not match the standard agreement, match by clause name, say so, and ask the seller to confirm.
11. **Computed differences.** If the input has a `<computed_differences>` block, a plain text comparison found those differences exactly and completely. Account for every item: list it as a deviation, or name it under "Not treated as deviations" with the reason. If the input has an `<untracked_differences>` block that is not "None.", those edits are in the file's text but were not marked as tracked changes. List each as a deviation and tell the seller, under Questions for the seller, that the customer made an untracked change.
12. **Later rounds.** If the input has a `<prior_approval_record>`, this is a later round of a deal that already has decisions. Add a column **Round status** to the Deviations table and give each deviation one value: **New** (not in the prior record); **Already decided** (in the prior record, with the same position; say the prior ID and its status); **Changed since decided** (in the prior record, but the wording or figures differ from what was approved or denied; it needs a new decision); **Reinserted after denial** (the prior record says Denied or Not conceded and the customer asked for it again); **Dropped** (in the prior record, but this round no longer differs from the standard). Use `<differences_since_previous_round>` to see what moved this round. Never treat an earlier approval as covering different wording or figures.

## Output

**Deviations**

| ID | Clause | Standard position | Requested position (exact words) | Kind | Notes |
|---|---|---|---|---|---|

- `Kind` is **Changed**, **Added** or **Removed**.
- `Notes` holds sub-items, other clauses through which the change takes effect, and cross-references.

**Not treated as deviations** (wording-only differences, one line each)

**Questions for the seller** (anything you could not compare or are unsure of)

## Rules

- Count completeness above brevity. A missed deviation is worse than a long list.
- Use the counterparty's exact words in `Requested position`.
- Do not decide who approves anything. That is Stage 2.
- Do not judge whether a change is acceptable. That is the approver's decision.

## Check before you finish

- Every inserted or deleted provision in a redline appears in the table or in the wording-only list.
- Every deviation shows the standard position, or says none exists.
- Every sub-item and every clause through which a change takes effect is listed.
