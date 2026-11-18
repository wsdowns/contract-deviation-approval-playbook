# Demo walkthrough (5 to 8 minutes)

## How the demo works

The demo is the seller app, run on **finished runs**. A live run takes 3 to 5 minutes per stage because the model writes long, careful output, so the recording never waits on the model. Every screen you show holds real model output from a real run. Say so on camera: "This run finished earlier; the model did not see the answer key."

The simulated mailbox is the one part that is not real email. Say that too.

## Setup (once, before recording)

```bash
cd contract-deviation-approval-playbook
python3 app/server.py
```

Open http://127.0.0.1:8765. Use a light theme, browser zoom at 125%, and close other tabs. Have these open in other tabs: `examples/acme-saas/contracts/ACME_SaaS_Agreement_v1.0.docx` and the Case 1 redline Word file. On step 1, the "Or open a finished run" menu loads any finished run.

Finished runs to use:

| Case | Run to open |
|---|---|
| Case 1, Brightwater (full loop, with the 5% step and the final check) | app-20261111-170919 |
| Case 2, Lakeshore (customer paper, rulings, chase) | app-20261112-080614 |
| Case 3, Summit Ridge (wrong sender, split decision, condition) | see the table at the end |

Record with QuickTime (File, New Screen Recording). Speak while you click.

## Script and timing

| Time | On screen | Say |
|---|---|---|
| 0:00 | Title or step 1 | The task: a customer redlines a contract and each change needs the right approver. The record I produce is proof of authority for the changes, not proof of the changes. The AI finds, routes, drafts and records. A person approves. |
| 0:45 | Step 1, Case 1. Show the redline Word file with tracked changes, then ACME's standard | This is what a seller receives. Where do I start? The deal profile comes from the CRM in real life. |
| 1:30 | Step 2, summary | The AI listed every change, found the covering rule in the matrix, and drafted one request per approver. Point at one row where it flagged instead of assuming. Open one drafted request: it states the change, the standard, the deal facts and the decision needed. |
| 2:30 | Step 3, then step 4 | The seller confirms once. Replies arrive in a simulated mailbox, only for requests that were actually sent. Open the record: Net 45 approved, renewal cap denied. |
| 3:30 | Denied row, seller note | A denial is a normal outcome. The AI gives the seller words for the customer and shares neither the approver's name nor the reasoning. |
| 4:15 | Step 5 | The seller, not the AI, asks for a 5% cap. The new request quotes the denial. The AI never suggests a concession. |
| 5:00 | Open Case 3 run, step 4 | Three things the playbook caught: a Vice President of Sales approved billing but is not the named approver; the CEO approved gross negligence and said nothing on willful misconduct, so it is Unclear, not approved; the General Counsel approved with a condition, quoted word for word. |
| 6:00 | Step 6, Case 1 | The seller reports the final contract. The check lists any change without an approval. |
| 6:30 | Slide or talk: what I learned | Meta-communication changed the design (see the report). The hand-off test: an independent person plays the seller. The responsible-use note and the NIST functions. |
| 7:30 | End | Close. |

## If the app will not start

Everything on screen is also saved as files in `runs/`. Open `runs/app-.../stage4.md` (the record) and `stage3.md` (the requests) in any viewer and narrate the same script.

## What to say about limits

Cases are reconstructed stand-ins, not real company data. The mailbox is simulated. The hand-off test with an independent person is the last item.

## A live demo with AI-played approvers

Set `[app] mode = "demo"` (the default). Upload a contract on the first screen. The requests go out, and within a minute the AI-played approvers have decided them in the portal. Open the requests screen to see each one. Choose "Act as someone else" at the top to sign in as an approver and read what was decided. To show reminders and escalation, list a title under `[demo] silent_titles`, then use "Move the demo clock to the next business day" on the requests screen. Every record is labeled SIMULATED APPROVERS.
