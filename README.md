# Contract Deviation Approval Playbook

**Author: William Scott Downs**

An open, reproducible framework for using AI to manage **contract deviations under a delegation of authority (DoA)**. It works with any contract type and any organization's approval matrix. A complete worked example for SaaS selling is included.

When a counterparty changes a contract, each changed term needs approval from the person the organization's DoA names for that term. The playbook has an AI partner do four things, with a human in control. The seller hands over a contract and confirms one batch; the playbook sends the requests, tracks the replies and speaks up only when a human decision is needed (see [docs/seller-experience.md](docs/seller-experience.md)):

1. **Identify** each changed term against the organization's standard position.
2. **Locate** the DoA rule (level and approver) for each change.
3. **Draft** the escalation request for each approver.
4. **Document** the actual decisions: who approved what, with the approver's exact conditions and limits.

The output is a consolidated approval record: **proof of authority for the changes, not proof of the changes.**

Standing rule: when authority is unclear, information conflicts, or an approval is incomplete, the AI **flags it** instead of assuming.

**Start here:** [docs/framework.md](docs/framework.md) explains the contract delegation of authority framework, and [docs/setup-guide.md](docs/setup-guide.md) walks through setup step by step.

> **Status:** the framework, prompts, tooling, seller app and three worked cases are complete and checked against answer keys. Real email, a unique request ID and an automated qualification check are not built yet; see the limits in [docs/framework.md](docs/framework.md).

## How it matures

1. **Manual.** People decide every deviation. The AI finds, routes, drafts and records. This works today.
2. **Informed.** An approvals ledger records every decision, so the matrix owner can audit approvers and terms. An approver who always approves, or never does, raises a fair question about the matrix. Designed, not built.
3. **Rules.** The owner writes deterministic rules: this position is approved under these conditions, with no person deciding each time. Code checks the rule, never the AI, and a named person authorizes it. Designed, not built.
4. **Monitored.** Rules expire, are sampled for human review, and can be switched off.

See [docs/maturity-model.md](docs/maturity-model.md). The full documentation map is in [docs/README.md](docs/README.md).

## Why this is hard for AI

- Approvals are **term by term**, not one go/no-go decision on the whole contract.
- Real approvals come back **partial, conditional, ambiguous, or from the wrong person.**
- One outcome can enter a contract through several clauses. In the SaaS example, uncapped data breach liability can come in through the indemnity, the data security article, and confidentiality.
- A clean-looking record that overstates what was approved is worse than no record.

## Use it with your own contracts

The DoA matrix is a few plain CSV files, so it can be adapted to any organization and contract type (SaaS, supply, services, licensing, procurement):

| File | Contents |
|---|---|
| `doa_matrix.csv` | One row per contract term: standard position, `Level 1` to `Level N`, and Not approvable |
| `roles.csv` | The approver titles the matrix may name |
| `people.csv` | Optional. Who holds each title, kept separate so the matrix never hard-codes names |
| `settings.csv` | Optional. Matrix owner, record custodian, pre-signature check, and the approvals mailbox |

The full format is in [docs/matrix-format.md](docs/matrix-format.md). How requests move, what each status means, and how ambiguity is handled are in [docs/escalation-path.md](docs/escalation-path.md). The approval record's format is in [docs/approval-record.md](docs/approval-record.md). To check and publish your own matrix:

```bash
pip install -r requirements.txt
python tools/doa_matrix.py validate path/to/your-matrix
python tools/doa_matrix.py build path/to/your-matrix your_matrix.xlsx --org "Your Company"
```

`validate` catches an approver missing from the roles list, a term with no authority and no Not approvable entry, duplicate terms, and people assigned to unknown titles. `build` validates, then writes a formatted workbook with Read Me, DoA Matrix, Roles and People sheets.

## Repository layout

| Path | Contents |
|---|---|
| `tools/` | `doa_matrix.py`: validates and builds any DoA matrix |
| `docs/` | Matrix format, the seller's experience, the deal profile, escalation path, statuses and ambiguity rules |
| `playbook/` | Standing instructions and the four stage prompts (contract-type neutral) |
| `examples/acme-saas/` | Worked example: a fictional SaaS vendor's contracts, DoA matrix and three test cases |
| `runs/` | AI output for each run, graded against the success criteria |
| `tests/` | Tests for the tooling |

## Worked example: ACME SaaS

Three cases for a fictional vendor, ACME, Inc., under one DoA matrix. See [examples/acme-saas](examples/acme-saas/README.md).

| Case | Customer | What the app reads |
|---|---|---|
| 1 | Brightwater Logistics, a small standard deal | A Word redline of ACME's standard SaaS Agreement, with tracked changes |
| 2 | Lakeshore Health, a large strategic deal | A Word redline of ACME's agreement: governing law, data location, termination for convenience, a greater-of liability cap, most-favored pricing, HITRUST |
| 3 | Summit Ridge Manufacturing, a mid-market deal | A Word redline of ACME's agreement: quarterly billing, service credits, cyber insurance, gross negligence carve-out, indemnity for violation of law |

All three are redlines of ACME's agreement, which is adapted from the public Common Paper Cloud Service Agreement, so the base contract was not written by the author. Contracts on a customer's own paper are not supported yet. Cases 2 and 3 are rebuilt with `python tools/build_case_docx.py`, which applies the customer's changes to ACME's Word file as real tracked changes.

Each case is designed backward from its answer key: a short list of deviations, each with a known outcome, plus one or two planted traps (partial approval, missing co-approval, not approvable, matrix ambiguity).

## Success criteria

1. **Complete:** every contract change appears in the record, with none missing.
2. **Correct authority:** every approval comes from the role the DoA names for that term.
3. **No overreach:** the record matches each approver's actual decision and claims nothing they did not approve.
4. **Actionable requests:** every escalation request states the change, the policy position, the risk, the proposed compromise, and the decision needed.
5. **Hand-off:** a colleague who did not build the playbook runs it without help and meets criteria 1 through 4.
6. **Flags instead of assumes:** unclear authority, conflicting information, and incomplete approvals are flagged, not resolved by guesswork.
7. **Reproducible:** everything is published here under open licenses, so anyone can rerun each case and check the results.

## Scope and assumptions

- **Deal context comes from the CRM.** In a real deployment, the [deal profile](docs/deal-profile.md) is pulled from the CRM and other systems. For this project it is a file in each case folder, so the tests need no system access.
- **Email is simulated in tests.** The playbook is designed to send requests and match replies automatically; tests use a simulated mailbox so every run is reproducible.
- **The matrix is an example.** Every threshold in the ACME matrix is a placeholder. Adopters set their own.

## Roadmap

- [x] DoA matrix format, validator and workbook builder, with tests
- [x] SaaS example: seller paper (ACME, adapted from Common Paper) and customer paper (Lakeshore Health, original)
- [x] SaaS example: DoA matrix, roles and people
- [ ] Case design and answer keys, frozen before any playbook run
- [x] Playbook prompts for the four stages (Case 1 run end to end; Cases 2 and 3 first round only)
- [x] Seller app, a local web app with a simulated mailbox (all three cases; see [app/](app/README.md))
- [ ] Runs and grading
- [ ] Hand-off test by an independent tester

## About the author

William Scott Downs is an executive with deep technology roots and the author of two books on putting AI to work in business:

- [*AI's Missing Playbook: Aligning AI With the Goals That Move Your Business*](https://aismissingplaybook.com/)
- [*Balancing the AI Value Equation: Building Method and Execution That Matter*](https://aivalueequation.com/)

## Everything here is fictional

ACME, Inc., Lakeshore Health, Inc., every person named, and every figure are invented. Nothing reflects any real company's contract terms, prices or approval policies. The documents are examples for teaching and testing, not legal advice.

## License

- Code and prompts: [MIT](LICENSE)
- Documents, contracts, matrices and cases: [CC BY 4.0](LICENSE-DOCS.md)
- Third-party material and required attributions: [ATTRIBUTION.md](ATTRIBUTION.md)

## Citation

Downs, W. S. (2026). *Contract Deviation Approval Playbook* [Computer software and documentation]. GitHub.
