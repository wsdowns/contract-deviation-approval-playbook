# Worked example: ACME SaaS

By William Scott Downs. A complete example of the playbook for outbound SaaS selling by a fictional vendor, ACME, Inc. All three cases run under one DoA matrix.

## Contents

| Path | Contents |
|---|---|
| `contracts/ACME_SaaS_Agreement_v1.0.docx` | ACME's standard SaaS Agreement (seller paper), adapted from the Common Paper Cloud Service Agreement v3.0 |
| `contracts/Lakeshore_Health_SaaS_Agreement.docx` | A customer-favorable SaaS agreement from a fictional health system (customer paper), written for this project. Kept for reference: the app does not run customer paper |
| `contracts/reference/` | The unmodified Common Paper original |
| `doa-matrix/` | ACME's DoA matrix: `doa_matrix.csv`, `roles.csv`, `people.csv`, and the built workbook |
| `cases/` | The three test cases, each with inputs, approvals as received, and an answer key |
| `build-scripts/` | How the contract documents were produced |

## The cases

| Case | Deal | What it tests in the app |
|---|---|---|
| 1 | Brightwater Logistics, $20K a year, standard | A small redline with routine changes |
| 2 | Lakeshore Health, $1M a year, strategic | Not approvable and unclear terms alongside routed ones |
| 3 | Summit Ridge Manufacturing, $250K a year, standard | A shared payment paragraph, a joint approval and a Level 3 approval |

All three are Word redlines of ACME's agreement with tracked changes. The answer keys and `approvals/` messages were written for the earlier, manual version of the process, which read email replies.

Deal size changes what is realistic to ask and to approve, so each case ships with a deal profile (`inputs/deal-profile.md`).

## Rebuild the matrix workbook

```bash
python tools/doa_matrix.py build examples/acme-saas/doa-matrix examples/acme-saas/doa-matrix/ACME_DoA_Matrix.xlsx --org "ACME, Inc."
```

Everything in this example is fictional. People's emails use the reserved `acme.example` domain.

Background on the author's approach to business AI: [*AI's Missing Playbook*](https://aismissingplaybook.com/) and [*Balancing the AI Value Equation*](https://aivalueequation.com/).
