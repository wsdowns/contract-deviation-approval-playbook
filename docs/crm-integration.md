# Connecting Seller's Associate to your CRM

Version 1 does not talk to a CRM. A seller types four deal facts into the upload form. This page says what to do about that today, what you can safely automate with the code as it is, and what you would have to build. Each section is marked **Works today**, **Possible with a small script**, or **Not built**.

## What the CRM supplies, and what it receives

Seller's Associate needs four facts about a deal and gives back a decision trail.

| In (from the CRM) | Form field | Used for |
|---|---|---|
| Account name | Customer | Request subjects, the ledger |
| Annual contract value | Annual fees | Turning "2x fees" into dollars; deal size in audit and rules |
| Contract term in months | Term | The deal profile; later, rules |
| Strategic or standard flag | Tier | The deal profile; later, rules |

| Out (to the CRM) | Where it lives today |
|---|---|
| Whether every change on a deal is decided | The seller's status screen; the `decisions` table |
| Who approved what, when, in their own words | `decisions`, `record_rows` in the ledger |
| The approval record and the signed-copy check | The run folder (`stage6.md`, `signed-check.md`) |

## Option 1: the seller copies four facts (works today)

The seller opens the opportunity, copies the four values into the upload form, and uploads the customer's file. It is the right start: it takes about a minute, needs no credentials and no CRM change, and the numbers on the form are visible to the seller before they go anywhere. Blank facts carry over from the earlier round of the same deal.

Add a link to the app on the opportunity page (a custom button or a URL field) so the seller does not have to remember where it is.

## Option 2: a script posts the deal (possible with a small script)

The upload endpoint accepts the same fields as JSON, so a script on your side can send a contract that arrives by email or sits in the CRM:

```
POST /api/upload
{"filename": "Customer_redline.docx",
 "data": "<the file, base64>",
 "deal": {"customer": "Brightwater", "annual_fees": "250,000", "term_months": "24", "tier": "standard"},
 "previous": "<earlier run name, for round 2 or later>",
 "signed": false}
```

The endpoint needs a signed-in seller. Do not give a script a seller's password. Put the app behind your single sign-on proxy (`[auth] provider = "proxy-header"`, see `deployment.md`) and let the script call through that proxy as a service identity that your identity team has listed as a seller in `sellers.csv`.

Two cautions:
- **The proxy must set the identity header itself and strip any copy sent by the caller.** If it passes the caller's header through, anyone can claim to be any seller or approver.
- **The seller must still be the person of record.** The ledger records the signed-in email as the seller, and every request copies that email. A service identity makes the service the seller. If you need the real seller on the trail, have the proxy pass the seller's own verified email, not a shared account.

## Option 3: read the trail back (possible with a small script)

Two read paths exist.

1. **CSV export.** An auditor or matrix owner signed in to the audit page can download `deals.csv`, `decisions.csv`, `record_rows.csv`, `request_events.csv` and `matrix_versions.csv` from `/audit`. A scheduled job that fetches `decisions.csv` and updates a custom field on the opportunity (for example "Approvals: 3 of 3 decided") is a few lines of code.
2. **The ledger file.** `ledger.db` is SQLite. A reporting job on the same server may open it read-only. Never open it for writing: it is append-only by design, and the app enforces that with database triggers.

Join key: the `deals` table holds `customer`, `seller_email` and `created_at`. It does not hold your CRM's opportunity id. If you want a reliable join, put the opportunity id in the form's Customer field (for example `Brightwater (OPP-10432)`), or add a column. The first costs nothing and survives export.

## Not built

These are the things a CRM integration would normally want. They are specified here so the work is clear; none exists in the code.

| Want | What it takes |
|---|---|
| A button on the opportunity that opens the form already filled | Accept the four facts as query parameters on the home page. Never put a contract or personal data in a URL |
| Facts pulled from the CRM by API instead of typed | A connector module per CRM that, given an opportunity id, returns the four fields. The `deal_facts()` function is the one place those facts enter; the connector should feed it |
| A webhook or CRM update when a request is decided | A call from the portal's `decide()` path to your CRM. Send the status, not the approver's words, unless your CRM's access controls match the ledger's |
| The contract file attached to the opportunity | Fetch it from the CRM in the connector and pass it to the upload path; store the approval record back as an attachment |
| An opportunity id as a first-class ledger field | One column on `deals` and one form field |

## Field mapping examples

These are starting points. Field names differ by company; check yours.

| Seller's Associate | Salesforce | HubSpot | Generic |
|---|---|---|---|
| Customer | `Account.Name` | Company name | Account name |
| Annual fees | `Opportunity.Amount` (if annual) or an ARR field | Deal amount (if annual) | Annual recurring revenue |
| Term (months) | A contract-term field on the opportunity or order | A custom property | Contract length |
| Tier | A strategic-account flag | A custom property | Any flag you already keep |

Check what "amount" means in your CRM before mapping it. A three-year total entered as the amount would make every cap look three times larger than it is, and the approvers would be deciding on the wrong number. If your CRM stores total contract value, divide by the term in years in the connector or the script, and say so in the deal profile.

## Principles to keep when you integrate

- **The CRM supplies facts, not authority.** Who may approve what still comes only from the matrix files.
- **Nothing from the CRM approves anything.** A stage change, a field value or a "closed won" flag never stands in for a recorded decision.
- **Keep the approver's decision where it was made.** The portal and the ledger are the system of record for approvals. The CRM holds a pointer and a status.
- **Send the minimum.** Statuses and counts go to the CRM freely. Contract text and approvers' reasons stay in the ledger unless your access controls match.
