# Case 2: Lakeshore Health's redline of ACME's paper

**Update.** The staged example is now a Word redline of ACME's standard agreement with the same six asks (`inputs/Lakeshore_Redline_of_ACME_SaaS_Agreement.docx`, built by `tools/build_case_docx.py`). The original draft on Lakeshore's own paper (`inputs/Lakeshore_Health_SaaS_Agreement.txt`) is kept for reference only; the app does not run contracts on a customer's own paper. The planted approval replies below belong to the earlier email mailbox: in the portal, only the assigned approver can decide, so what this case now tests is the routing.

| | |
|---|---|
| Customer | Lakeshore Health, Inc. (fictional) |
| Paper | Lakeshore Health SaaS Agreement (customer paper) |
| What the AI reads first | The agreement as received, with no redline |
| Requester | Account Executive |
| Status | Design locked. The agreement differs from ACME's standard only on the six designed terms. Approvals and answer key to be written and frozen by December 4, 2026 |

## Folder contents

- `inputs/deal-profile.md`: the deal profile the seller provides at intake (see `docs/deal-profile.md`)
- `inputs/`: the agreement as received
- `approvals/`: the approvals as they came back, one file per message
- `answer-key.md`: the expected approval record, used for grading. **Testers and the AI must not see it before a run.**
