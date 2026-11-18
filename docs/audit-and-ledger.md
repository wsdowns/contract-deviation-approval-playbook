# Auditing approvers: the approvals ledger

Status: built for uploaded contracts. The staged demo cases use a simulated mailbox and do not write to the ledger.

If the system runs for a year or more, the organization needs to be able to look back and ask whether its approvers are doing the job the matrix gave them. An approver who always says yes, or who never says yes, raises a fair question about why that person is in the matrix. The ledger exists to make the question answerable.

## What it is

One SQLite file, `ledger.db`. SQLite is a single file with no server. Python reads it with no install, and anyone can query it with SQL or export it to CSV. The app writes to it and never edits or deletes a row. A correction is a new row that refers to the old one.

## What it records

Five tables in one file. The app only adds rows. Triggers in the database refuse any UPDATE or DELETE, so history cannot be rewritten. A correction would be a new row that names the row it corrects.

| Table | One row for | Main fields |
|---|---|---|
| `decisions` | each decision an approver makes in the portal | request ID, deal, when requested and decided, hours to decide, subject, approver title, name and email, who they acted for if delegated, the decision, their exact words, matrix version, rule ID (empty until rules exist) |
| `request_events` | each time a request is created, delegated, questioned, reminded or escalated | request ID, deal, time, event, approver title and name, detail. A silent approver never makes a decision row, so this is where silence shows up |
| `record_rows` | each row of the approval record, every time the record is produced | deal, run, row ID, change, matrix row and level, approver, decision words, status, conditions, final outcome, matrix version |
| `deals` | each uploaded round | deal ID, seller, customer, annual fees, term in months, standard or strategic, file name |
| `matrix_versions` | each distinct version of the four matrix files | a short hash and the file contents, so any version can be reconstructed |

Deal facts are typed as numbers on the upload screen, not left in prose, so the audit can group by deal size. In real use they come from the CRM.

## Where to read it

The matrix owner opens **Audit the approvers** on the home page (`/audit`). Anyone else the organization lists under `[ledger] viewers` in `config.toml` can too. The page shows four views, by approver, by term, by deal size and responsiveness (requests received, decided, reminded and escalated, per approver), and links to a CSV export of each table. Counts always show. A rate shows only once a group has `min_requests` requests (20 by default).

## What it answers

- **Per approver:** how many requests, and the share approved, conditional and denied. How long they take.
- **Per term:** which terms are always approved, always denied, or often conditional.
- **Per deal size:** whether approval depends on the size of the deal.
- **Over time:** whether any of this is changing.

## Reading the numbers carefully

A rate is a question for the matrix owner, not a verdict.

- **An approver who always approves** might be rubber-stamping, or the matrix might be sending them requests that never needed escalating. Check the deal sizes and terms before judging the person.
- **An approver who never approves** might be a blocker, or sellers might only ask for what is genuinely out of bounds.
- **Selection effect.** Sellers send the requests they expect to win, so the data shows what was asked, not what was possible.
- **Small numbers mislead.** The audit views should show no rate until an approver or term has about 20 requests.

## What changes when you act on it

A term that is approved every time can move to a lower level, or become a rule (`docs/deterministic-rules.md`). A threshold can change. An approver can be added, replaced or removed. Each change to the matrix raises its version, so later rows say which matrix they were checked against.

## Privacy and access

The ledger holds approvers' names and customers' deal facts. Treat it as confidential. Limit who can read it, back it up, and decide a retention period. Keep it out of the repository: it is git-ignored.
