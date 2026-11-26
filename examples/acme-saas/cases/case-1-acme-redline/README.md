# Case 1: Brightwater Logistics redlines ACME paper

| | |
|---|---|
| Customer | Brightwater Logistics, Inc. (fictional) |
| Paper | ACME's standard SaaS Agreement |
| What the app reads | `inputs/Brightwater_Redline_of_ACME_SaaS_Agreement.docx` |
| Requester | Account Executive |

**What it tests.** A small redline with routine changes.

## Folder contents

- `inputs/`: the Word redline, the deal profile, and any earlier text drafts
- `approvals/`: replies written for the earlier manual version, one file per message. In the app, only the assigned approver can decide, in the portal.
- `answer-key.md`: the expected result of the manual version, useful for checking levels and approvers. Do not read it before a run you intend to grade.
