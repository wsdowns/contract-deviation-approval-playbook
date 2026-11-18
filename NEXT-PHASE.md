# Next-phase enhancements

Planned enhancements. Nothing here is built unless marked.

## Decisions made

- The portal is the only way an approver responds in version 1. Email only notifies and carries a link. Nothing reads email replies.
- After decisions: the seller is told the outcome, concedes only what was approved, and alone asks for a different position after a denial. The customer's next redline re-enters the upload loop. The signed copy gets the final check, and the record custodian files everything.
- Version 1 scope, in order: contract upload loop, approval portal with local logins, approvals ledger, AI-played approvers for demo mode. Single sign-on and deterministic rules wait; both stay specified.
- Hosting: the author hosts it privately for one or two people. There is no public demo. The public gets the repository with three staged contracts and the ACME standard contract, and runs it on their own site with their own AI key.
- The deal profile comes from a form in version 1. A CRM guide is written: `docs/crm-integration.md` explains how to feed the deal profile, and later the rule conditions, from a CRM.
- Approvers have an obligation to act on requests. A silent approver is escalated after the reminders, the seller and the matrix owner are told at the same time, and the seller is always kept informed because it is their account. Response times go in the ledger.
- Requests send automatically. The default for `send_mode` is `auto`, after code validates every recipient against the matrix and the people list, with the seller copied. `confirm` stays available for organizations that want a review click.
- The author owns the domain SELLERSASSOCIATE.COM for the private deployment. Nothing is deployed yet; HTTPS is required before any login is used there.

## Highest value

1. **Unique request ID.** A request number in the subject and first line of every request. The system or the seller issues it; the AI only formats it. Stage 3 adds the header, Stage 4 step 1 matches on ID first and flags a reply with no ID as "matched without an ID", the record gets a Request ID column, and follow-ups say "follows R-nnn". Optional: a content hash of each sent message. An ID proves linkage, not who sent it, so the sender check stays. Then re-run all three cases.
2. **Automated grading against the answer keys.** A script that compares each run's record with its key, so every prompt change gets a regression check. Doubles as the model qualification run for the AI environment gate.
3. **AI-played approvers.** Each person in `people.csv` gets a short role brief; the model writes the reply to the request actually received. Removes the fragile subject matching in the simulator. The approver never sees the answer key or the Associate's reasoning.
4. **Web portal.** An ACME-branded "Seller's Associate" on the Lightsail server. Mockups were reviewed (intake, change review, approvals inbox and record). Needs the model reached by an API key held on the server, a shared password and a daily run limit, and a go-ahead before any deploy.
5. **Real email adapter.** Replace the simulated mailbox with the approvals mailbox, without changing the playbook.

## Prompt and playbook

6. **Examples element.** Add a short worked example to each stage prompt, then re-run to confirm no regression. Today it is the thinnest of the seven elements.
7. **Stage 1 sub-item rule.** Check it holds across all cases and models.
8. **Seller note.** One draft ended "I am glad to confirm anything else in the agreement", which edges toward a promise. Tighten.
9. **Reminder default.** Two business days is my choice; confirm or change.
10. **Order Form.** The AI flags that the Order Form is not provided. Decide whether the playbook should take it as an input.
11. **Dates.** Stand-in cases carry dates in early 2026; the AI flags the conflict with today. Set dates when the wording is frozen.
12. **Real tracked-changes input.** The app reads a text form of the redline; read the Word file's tracked changes directly.

## Matrix and process design

13. **Separate approver and checker.** In the example matrix the Deal Desk Manager approves Level 1 changes and runs the pre-signature check.
14. **Lower-level approval after a higher-level denial.** The matrix is silent; the record flags it. Decide the rule.
15. **Pin the matrix version in each record** (commit or file hash) and record the AI environment used.

## Evidence and testing

16. **Independent hand-off test** with a protocol, and keeping answer keys and later-replies out of the tester's view if the repository is public.
17. **More runs per case and more than one model,** to measure how often it fails, not only that it works.
18. **A third public case,** from a published SaaS master agreement.

## Reference architecture

19. **Configuration file** (built): `config.toml`, model backends including open weights, the setup-gate record. Still to do: own case folders in the app, so a downloader can load their own contract.
20. **Demo and live modes.** Built: [app] mode, AI-played approvers (own matrix rows only, through the portal, labeled simulated in the inbox, the ledger and the record), silent and delegating scenarios, a demo clock, and refusal to combine demo mode with smtp or real data. Not built: a seller-facing mode switch (it is a deployment setting by design), email replies. Demo: AI-played approvers (replay of scripted replies kept for the three cases), every record labeled "SIMULATED APPROVERS, not proof of authority", fictional addresses only. Live: SMTP send and IMAP read, one confirmation screen listing every recipient, blocked until the setup gate is complete, and a draft-only setting for testing.
21. **Approvals ledger.** Built for uploaded contracts: append-only SQLite with triggers, decisions, record rows, deals and matrix versions, audit page for the matrix owner, CSV export, rates hidden below min_requests. Not built: corrections API, the rule ID column is empty until rules exist, staged demo cases do not write to it, reminders counts. One append-only SQLite file, written at record time: request ID, date, deal, deal size and term, term, matrix row and level, approver title and name, decision, exact words, response time, final outcome, matrix version. CSV export. Needs a parser for the AI's record tables. Audit views per approver, per term and per deal-size band; suppress rates below about 20 requests; present results as questions for the matrix owner, not verdicts (sellers send only requests they expect to win).
22. **Maturity path: manual, informed, rules, monitored.** A separate `auto_rules.csv` (term, condition, covered position, rule owner, effective date, review-by date), evaluated by code, never by the AI. Records read "Approved by rule R-n, version v, authorized by <matrix owner>". Guardrails: deal facts must come from the CRM, not seller-typed; not-approvable positions always go to a human; sampled human review of auto-approvals; review dates; kill switch.
23. **Scripted qualification check** that runs Case 1 on a chosen model and compares the record with its key.

24. **Approval portal.** Built: sign-in (demo, local users file, proxy header), portal pages, decisions written to the inbox in reply shape, delegation by the approver, questions, SMTP or file notifications, auto or confirm send, recipients checked against people.csv. Reminders and escalation: built (business-day schedule, fixed-template messages, escalation to seller and matrix owner together, optional fallback columns in people.csv, silence recorded in the ledger). Not built: OIDC, sellers.csv checks in the matrix validator. The request email carries only a notification and a link carrying the request ID. The approver signs in and decides on a page: Approve, Approve with conditions, Deny, Delegate, Ask a question. Decisions are structured data, written straight to the ledger; code checks stated limits against the matrix. Email replies are an optional later fallback. Seller identity and `sellers.csv` come from the same login.
25. **Pluggable authentication.** One interface: a provider returns a verified email, and `people.csv` and `sellers.csv` decide what that person may do. Providers: `none` (demo), `local` (users file with salted scrypt hashes, `tools/users.py` to add and reset, HTTPS, failed-attempt limits, secure cookies, administrator reset, git-ignored), `proxy-header` (behind company single sign-on), `oidc` (Okta, Entra, Google). Build `none` and `local` first. Document that `local` is for early use and small teams.
26. **Delegation and follow-up.** Approver-initiated delegation (reply or button, from the approver's own identity, no sub-delegation, matrix owner copied), optional fallback columns in `people.csv`, reminder schedule in `settings.csv`, escalation to the seller and matrix owner when silent, and an `allow_approver_delegation` setting. No central delegation register.
27. **Contract upload loop.** Built: upload of Word (tracked changes read directly), PDF or text; exact comparison with the standard; untracked edits found; later rounds compared with the previous round and the prior approval record; signed-copy check with a tick; AI told every difference. Not yet tried with a live model. Still to do: finding the previous round automatically, and OCR for scanned copies. One "upload a contract" action; code compares against the last approved version; AI explains differences; reads tracked changes from Word; flags untracked differences; PDFs with a warning; a "signed" tick that expects zero differences; signed-copy check closes each deal.
28. **Send mode.** `send_mode = "auto"` (default) or `"confirm"`: requests sent from a fixed template after code validates every recipient against the matrix and `people.csv`.

## Found in the deployment review

- **Separate deals per seller: done.** The current deal and running job are kept per signed-in seller (`PerSeller` in `app/server.py`), and each seller sees only their own runs. Still in memory in one process; for many sellers, move that state to a database and the model calls to a queue.
- **Placement and routing in code: done.** `app/locate.py` places each change on a matrix row from the `Contract location` and `Keywords` columns (see `docs/how-it-decides.md`); `app/assess.py` takes one AI reading per contract and checks it against the matrix (row, level cell, quoted words); approvers come from the cell, never from the AI; requests and the approval record are built in code. Still the AI's job: naming the level. That closes only with deterministic rules (`docs/deterministic-rules.md`).
- **Cap spending.** A per-user and per-day limit on uploads, and a budget alert.
- **Retry failed reminder emails** and surface failures to the matrix owner.
- **End a session on sign-out** (server-side sessions) and add password reset by an administrator command.
- **Run behind a production web server** or add request timeouts.

## Decisions made (standard contracts only)

- **The app handles ACME's standard agreement with changes.** A contract on the customer's own paper is refused (fewer than half of the standard's sentences present) until a method for it is designed. Example Case 2 (Lakeshore) is kept for reference only.
- **Section numbers are not in the Word file**, so headings and Key Terms field names are the matching keys. A matrix row lists its places in `Contract location`.
- **Changes no row claims, or that a cell does not clearly cover, are referred to the Deal Desk** (setting `Terms not in the matrix`), one request per change, never guessed at. See the first-test decisions below. `python tools/doa_matrix.py validate <matrix> --standard <docx>` lists every place no row claims (44 in the ACME example), for the matrix owner to claim or to accept.
- **Staged examples run through the same path as an upload.** All three are full Word redlines of ACME's agreement with real tracked changes (Case 1 by hand; Cases 2 and 3 built by `tools/build_case_docx.py`).

## To do next from this build

- A customer-added section with a heading the matrix does not list goes to the matrix owner. Offer a switch for an AI-assisted placement of such sections, off by default.
- Numeric rules for levels (Net days, percentages, multiples of fees) so the AI's level can be checked or replaced.

## Decisions from the first test (2026-11-18)

1. **"The changes" table** reads ID, Requested (exact words), Standard (exact words), Where, Kind, so the two wordings sit side by side. Built.
2. **"Placed by" is not shown to the seller.** The seller does not need to know what the AI is doing. Built.
3. **"Who may approve" table has no "Cell relied on" column.** The matrix wording stays stored with the analysis for audit. Built.
4. **Terms the matrix does not settle go to the Deal Desk**, not to the matrix owner. Each change is its own request. It shows what the clause is (a plain explanation from the one AI call), what the standard says, what the customer's version says, and the exact words that changed. Built.
5. **The Deal Desk resolves it outside the system and answers inside it.** The answer has an outcome (approved, approved with conditions, denied, no approval needed), an authority or basis in free text (a person and title, a policy, or a fact; required), an optional reference, and notes. There is no approver list, because the authority may not be an approver at all (for example an operational fact). The record shows it as "Resolved by the Deal Desk", marked as the Deal Desk's statement and not verified in the system. Built.
6. **The seller is not ready to sign while a referral is open.** A referral that has no answer shows as "Referred to Deal Desk" and under "Still open" in the record. Built.
7. **Setting.** `Terms not in the matrix` in `settings.csv` names the title that receives them; the matrix owner authorizes it by setting it. Built.

8. **Requests and Replies are one page, "Requests/Status".** A status table with the outcome in color and the approver's exact words, with "Requests Sent" and "Approver Response" below. It updates by itself. The approval record is saved to the ledger when the last request in a deal is answered. Built.
9. **Appeals replace "Next move".** The seller selects a denial and may add new context; the same approver decides again; one appeal per denial; the record shows both decisions; a "not approvable" change has no appeal; going over an approver's head is out of scope. The follow-up and draft-new-request features are removed (reminders and escalation already run by themselves; a different position goes in a new round). Built.
10. **Final check is a pass or fail upload.** The seller does not describe the final contract. When an approval is given the contract is updated (the redline accepted, with an "approved" comment) or a denial is explained, so the final check is a new upload of the same contract at its latest revision. Code finds every change still in it and compares each with the approvals. If it fails, it shows where. Conditions are listed as a note. Built, with no AI.
11. **One banner in demo mode.** The two banners are merged into one short line, with no model name. Built.
12. **Home and Contracts restructure.** Home has two large cards (Start Here: Demo (Staged Examples); Seller's Associate: Your Contracts) and small ones below (standard contract download, approval matrix, audit, how it works). Both large cards open the renamed **Contracts** page, which lists the active contracts (demo and real kept apart), each with its own menu: Summary, Requests/Status, Appeals, Final Check, Archive. The upload form (or the staged examples) sits below the list, and is all that shows when there are no contracts. The selected contract follows the seller through every page, each page shows its name with a way back to Contracts. Built, not yet deployed at the time of writing.
13. **Archive.** Any time, after a confirmation. Open requests are withdrawn (approvers see "Withdrawn by the seller", reminders stop), the deal leaves the seller's screens, and the ledger records it (`deal_events`, plus a `withdrawn` event per request). Files and the audit record stay. No reopen. There is no signed or closed status: a CRM close would trigger the archive. Built, not yet deployed at the time of writing.

Not included, for the next round: the repeated customer and tier lines in each request's deal section; the AI's "reasoning" column in the "Who may approve" table, which the seller may not need; the other places that mention the AI to the seller (subtitles, progress messages, the model banner, the How it works page).

## Observed on Haiku 5.5 (live runs, 2026-11-18)

- Case 1: all runs match the answer key. Case 3: all runs match. Case 2: governing law, data residency, most-favored pricing (not approvable) and HITRUST (unclear) match in every run; the greater-of liability cap is "unclear" in most runs (the key) and once "not approvable"; termination for convenience routes to CFO and General Counsel in most runs and was "unclear" in one. An "unclear" always goes to the matrix owner, never to a wrong approver.
- One analysis takes about 15 to 20 seconds for a five-change contract and 30 to 45 for Case 2's eight changes.

## Housekeeping

29. Darla's email spelling in `people.csv`.
30. Before publishing: keep the attribution for the seven-element framework in `ATTRIBUTION.md`.
31. The model call currently runs on the author's own account; use a generic client and keep personal details out of requests.
32. Word workbook layout: the AI-gate table's last row falls on the next page; keep it together.
