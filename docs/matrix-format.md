# DoA matrix format

A delegation of authority (DoA) matrix says who may approve each deviation from an organization's standard contract positions. Here it is kept as plain CSV (UTF-8) so it can be edited in Excel, reviewed in version control, and read by an AI or a script. It fits any contract type.

A matrix is a folder with two required files and two optional files.

## `doa_matrix.csv` (required)

One row per contract term.

| Column | Required | Meaning |
|---|---|---|
| `Term` | Yes | The contract term, for example "Payment terms" or "Limitation of liability". Must be unique. |
| `Standard position` | Yes | The organization's standard position. Any change from it is a deviation. |
| `Level 1` ... `Level N` | At least one | Authority at each level, lowest first. Use as many levels as your organization has, numbered without gaps. |
| `Not approvable` | Yes (may be blank) | Positions no one may approve unless the matrix itself is amended. |
| `Contract location` | For the app | Where in the standard agreement this term is defined, so code can place each change on the right row. See below. |
| `Keywords` | Only for shared places | Words that tell two rows apart when they share a place. See below. |

### Contract location and keywords

The app finds which row a change belongs to **in code**, not by asking the AI. ACME's Word file has no section numbers, so each place is named by its heading. A place is one of:

| Form | Example | Means |
|---|---|---|
| `Key Terms > Field` | `Key Terms > General Cap Amount` | A field on the cover page |
| `Group > Heading` | `Payment & Taxes > Payment` | A headed paragraph, under its group heading |
| `New: Heading` | `New: Service Levels` | A heading the customer is expected to ADD. The standard has no such place, so list the names customers use, one per name |

Separate several places with a semicolon. List a term's defining place, and any other place where the term is changed in practice, but not clauses that only refer back to it.

Where two rows share a place (the Payment paragraph holds both payment days and billing frequency), each row lists `Keywords`, separated by semicolons, and the words the customer *added or changed* decide. If they cannot decide, the change is **ambiguous** and the AI chooses only among the rows that claim the place; the program rejects any other row. A change in a place no row claims is **unlocated**: it goes to the matrix owner as not in the matrix.

Check the columns against the standard agreement, and list every place no row claims:

```bash
python tools/doa_matrix.py validate path/to/matrix-folder --standard path/to/standard.docx
```

It reports a location that is not a real place (a typo, or a renumbered or renamed heading), two rows that claim the same place without keywords, and a keyword used by both rows.

### Level cells

Each level cell states **what may be approved**, then a colon, then **who approves**:

```
Up to $5M: General Counsel + CFO
```

- The approvers are the text after the **last** colon.
- `+` joins approvers who must **all** approve. One alone is an incomplete approval.
- Start with `Pre-approved:` when the named role may accept the change without escalation:
  `Pre-approved: remove publicity right: Contracts Manager`
- Leave a cell **blank** when no one at that level may approve the change.
- Each approver must match a `Title` or `Short title` in `roles.csv`.

A higher level may approve anything a lower level in the same row may approve.

Every row must grant authority at some level or list something under `Not approvable`.

## `roles.csv` (required)

The titles the matrix may name. The matrix names titles, never people.

| Column | Meaning |
|---|---|
| `Title` | Full title, for example "Chief Financial Officer" |
| `Short title` | Optional abbreviation used in the matrix, for example "CFO" |
| `Function` | Department |
| `Notes` | Anything an approver or the AI should know about the role |

Every role must be named somewhere in the matrix or in `settings.csv`.

## `people.csv` (optional)

Who holds each title. It is kept separate so staff changes never touch the matrix. One person may hold several titles (for example, Deal Desk Manager and Record custodian in a small team); give each title its own row.

| Column | Meaning |
|---|---|
| `Title` | Must match a `Title` in `roles.csv` |
| `Name` | The person |
| `Email` | Where approval requests go |
| `Fallback name`, `Fallback email` | Optional. A standing fallback contact the approver has named. If the approver is silent through every reminder, this person is given the request and can decide it, recorded as acting for the approver. |

## `sellers.csv` (optional)

The people who may start a deal in the seller app. Columns: `Email`, `Name`, `Team` (optional). Many people can hold the Requester title, so they are listed here instead of in `people.csv`. If the file is missing, the seller screens are open in demo mode only.

## `settings.csv` (optional)

Who does what around the matrix. Each role value must be a `Title` or `Short title` in `roles.csv`. Name roles, not people, here too.

| Setting | Meaning |
|---|---|
| `Requester` | Submits contracts to the playbook and sends the escalation requests (for example, the account executive). May have no approval authority |
| `Matrix owner` | Amends the matrix and receives any deviation the matrix does not cover |
| `Record custodian` | Receives every final approval and stores the approval record, the evidence and the signed contract together |
| `Pre-signature check` | Before signature, checks the final contract against the approvals |
| `Terms not in the matrix` | Who receives a change the matrix does not settle: a place no row claims, or a change the AI could not match to a cell with confidence. For ACME, the Deal Desk Manager. If this setting is absent, the Matrix owner receives them. |
| `Approvals mailbox` | A shared role address where approvals are sent, so evidence collects in one place and survives staff changes |

The pre-signature check is the independent review of the record custodian's own approvals. If one person holds both the Record custodian and Pre-signature check titles, no one independently checks that person's own approvals. Assign the two titles to different people where possible.

## Rules the playbook applies

The full escalation path, statuses and ambiguity rules are in [escalation-path.md](escalation-path.md).


1. A deviation the matrix does not cover goes to the matrix owner. Do not apply the nearest row by analogy.
2. An approval must state what it approves. If it covers only part of the request, or adds conditions, record exactly that.
3. An approval from someone who does not hold the named title, or from the right person on the wrong term, is not an approval.

## Check and build

```bash
python tools/doa_matrix.py validate path/to/matrix-folder
python tools/doa_matrix.py build path/to/matrix-folder out.xlsx --org "Your Company"
```

`--email-format "you+{first}{last}@example.com"` overrides the emails in `people.csv`, which helps when routing test approvals to a single inbox.

See [`examples/acme-saas/doa-matrix`](../examples/acme-saas/doa-matrix) for a complete matrix.
