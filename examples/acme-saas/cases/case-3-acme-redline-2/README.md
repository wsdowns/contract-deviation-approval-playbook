# Case 3

**Update.** The staged example is now a full Word redline of ACME's agreement (`inputs/SummitRidge_Redline_of_ACME_SaaS_Agreement.docx`, built by `tools/build_case_docx.py`). `inputs/redline.md` is the original excerpt list, kept for reference. The planted approval replies belong to the earlier email mailbox; in the portal only the assigned approver can decide, so this case now tests the routing: the shared Payment paragraph (billing frequency, told apart by keywords), a joint approval, and a Level 3 approval.: Summit Ridge Manufacturing redlines ACME paper

| | |
|---|---|
| Customer | Summit Ridge Manufacturing, Inc. (fictional) |
| Paper | ACME's standard SaaS Agreement |
| What the AI reads first | Summit Ridge's redline of ACME's agreement |
| Requester | Account Executive |
| Status | Design locked. Inputs, approvals and answer key to be written and frozen by December 4, 2026 |

## Folder contents

- `inputs/deal-profile.md`: the deal profile the seller provides at intake (see `docs/deal-profile.md`)
- `inputs/`: the redlined agreement the requester submits
- `approvals/`: the approvals as they came back, one file per message
- `answer-key.md`: the expected approval record, used for grading. **Testers and the AI must not see it before a run.**
