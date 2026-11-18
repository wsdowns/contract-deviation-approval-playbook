# Stage 2: Locate the delegation of authority rule

## Purpose

For each deviation, find the matrix row and the lowest level that may approve it, or say plainly that the matrix does not settle it.

## Inputs

- The Stage 1 deviations table.
- The matrix files: `doa_matrix.csv`, `roles.csv`, `people.csv`, `settings.csv`.
- The deal profile, for annual fees (needed to turn multiples such as "2x fees" into amounts).

## Steps

For each deviation, in order:

1. **Find the row.** Match the deviation to a matrix `Term`. If two rows could apply, name both and say which governs and why. If no row applies, the outcome is **Not in matrix**.
2. **Check Not approvable first.** If the requested position is in the `Not approvable` cell, the outcome is **Not approvable**. Quote the cell. Do not route it to anyone.
3. **Find the level.** Read the Level 1 cell, then Level 2, and so on. The lowest level whose cell covers the request is the route. A higher level may approve anything a lower level may approve, but the request goes to the lowest covering level.
   - A blank level cell means that level may not approve it.
   - If the cell begins with `Pre-approved:` and covers the request, the outcome is **Pre-approved**. Name the role. No escalation is needed.
4. **Read the approvers.** The titles after the last colon in the cell. A `+` means every named title must approve. List each one.
5. **Note prerequisites.** Some cells add a condition, such as "on General Counsel's recommendation". List each as a prerequisite that must be shown in the evidence.
6. **Check fit.** Compare the cell's words with the words requested. Anything the request does that the cell does not name (an extra promise, a wider scope) means the cell does not clearly cover it. If the request falls between cells, or two cells conflict, or the cell's wording does not clearly cover the request, the outcome is **Authority unclear**. Quote the cells and explain the gap. Do not pick a level. The question goes to the matrix owner (see `settings.csv`).
7. **Do the arithmetic.** Where a cell uses a multiple of fees or a percentage, convert it with the annual fees from the deal profile and show the amount. If annual fees are not provided, flag it and do not guess. Where you add a derived figure (for example monthly credit dollars), state the assumption behind it.

## After a denial

A counterproposal that follows a denial is routed like any new request, to the lowest level that covers it. Do not route it upward or to the same approver to "fix" the denial. Add a flag: "decided at a lower level after a higher-level denial; the matrix does not say whether this is allowed". Do not decide the question; the seller and the matrix owner can.

## Output

| ID | Matrix row | Outcome | Cell relied on (exact words) | Approver titles | Joint? | Prerequisites | Reasoning |
|---|---|---|---|---|---|---|---|

- `Outcome` is one of: **Route to Level N**, **Pre-approved**, **Not approvable**, **Not in matrix**, **Authority unclear**.
- `Reasoning` is one or two sentences.

**Questions for the matrix owner** (one per Not in matrix and Authority unclear outcome, each stating the question and the options as you see them, without choosing)

**Flags** (missing profile facts, conflicting cells, anything else a human must settle)

## Rules

- **Never apply the nearest row by analogy.** If no row covers the change, the outcome is Not in matrix.
- **Never choose a level when the matrix does not clearly give one.** Flag it.
- Resolve titles through `roles.csv`, including short titles. Do not name people here; names come from `people.csv` when requests are addressed in Stage 3.
- Route to the lowest covering level. Do not route upward "to be safe".
- A prerequisite you cannot see in the evidence is a flag, not an assumption.

## Check before you finish

- Every deviation from Stage 1 has an outcome.
- Every outcome quotes the cell it relied on, or the cells that conflict.
- Every joint approval lists all required titles.
- Every multiple is converted to an amount, or flagged.
