# Case 2: Lakeshore Health redlines ACME paper

| | |
|---|---|
| Customer | Lakeshore Health, Inc. (fictional) |
| Paper | ACME's standard SaaS Agreement |
| What the app reads | `inputs/Lakeshore_Redline_of_ACME_SaaS_Agreement.docx` |
| Requester | Account Executive |

**What it tests.** Routing: governing law, data location, termination for convenience, a greater-of liability cap, most-favored pricing and HITRUST. The original draft on Lakeshore's own paper (`inputs/Lakeshore_Health_SaaS_Agreement.txt`) is kept for reference only; the folder name dates from it.

## Folder contents

- `inputs/`: the Word redline, the deal profile, and any earlier text drafts
- `approvals/`: replies written for the earlier manual version, one file per message. In the app, only the assigned approver can decide, in the portal.
- `answer-key.md`: the expected result of the manual version, useful for checking levels and approvers. Do not read it before a run you intend to grade.
