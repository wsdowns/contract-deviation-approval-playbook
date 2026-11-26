# Case 3: Summit Ridge Manufacturing redlines ACME paper

| | |
|---|---|
| Customer | Summit Ridge Manufacturing, Inc. (fictional) |
| Paper | ACME's standard SaaS Agreement |
| What the app reads | `inputs/SummitRidge_Redline_of_ACME_SaaS_Agreement.docx` |
| Requester | Account Executive |

**What it tests.** Routing: the shared Payment paragraph (billing frequency, told apart by keywords), a joint approval and a Level 3 approval.

## Folder contents

- `inputs/`: the Word redline, the deal profile, and any earlier text drafts
- `approvals/`: replies written for the earlier manual version, one file per message. In the app, only the assigned approver can decide, in the portal.
- `answer-key.md`: the expected result of the manual version, useful for checking levels and approvers. Do not read it before a run you intend to grade.
