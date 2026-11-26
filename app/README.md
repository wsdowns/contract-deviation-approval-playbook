# The app

Seller screens, an approver portal and an audit page for the playbook. Python standard library only.

```bash
python app/server.py
```

Then open http://localhost:8765. Set `PORT` to use another port. Set `DOA_STUB=1` to use canned model output when testing the app itself.

## Configuration

Copy `config.example.toml` to `config.toml` (git-ignored) to point the app at your own matrix folder and standard agreement, and to choose the model. With no `config.toml` it runs the ACME example in demo mode on the `claude` command.

Backends: `claude-cli`, `anthropic-api`, `openai-compatible` (Ollama, vLLM, llama.cpp, LM Studio, OpenRouter, private deployments, open weights) and `command` (any program that reads the prompt on stdin). The file never holds a key, only `api_key_env`, the name of the environment variable that does. While `stand_in_data_only = true` the app shows a banner. For real deals set it to false and record the AI environment, or the app will not start a run (setup gate, `docs/ai-environment.md`). Qualify any model on Case 1 before real use.

## The seller's screens

| Screen | What it does |
|---|---|
| Home | Staged examples, your contracts, the standard contract, the approval matrix, the audit page, how it works |
| Contracts | The list of active deals; upload a contract or start a staged example |
| Summary | Every change, who may approve it, and the requests |
| Requests/Status | Where each change stands, with approvers' exact words |
| Appeals | One appeal per denial, to the same approver |
| Final Check | Pass or fail on the final contract |

Any deal can be archived from the Contracts list.

## Approvers and audit

An approver gets an email with a link, signs in to `/portal`, reads the request and approves, approves with conditions, denies, delegates to a colleague at their company (who cannot pass it on) or asks the seller a question. The matrix owner reads the ledger at `/audit`.

## Files

| File | Job |
|---|---|
| `server.py` | Web server, screens' API and the run flow |
| `contract_io.py` | Reads Word, PDF and text; finds every difference |
| `locate.py` | Places each change on a matrix row |
| `assess.py`, `prompts/assess.md` | The one AI reading, its checks, and the request templates |
| `routing.py` | Checks every request against the matrix before it is sent |
| `portal.py` | Sign-in pages, requests, decisions, delegation, questions |
| `reminders.py`, `notify.py` | Reminder and escalation schedule; email or file notifications |
| `record.py`, `finalcheck.py` | The approval record and the final check |
| `ledger.py` | The append-only approvals ledger |
| `demo.py`, `prompts/demo_referral.md` | AI-played approvers (with `playbook/demo/approver.md`) |
| `auth.py`, `config.py`, `models.py` | Logins, settings, model backends |
| `static/index.html` | The seller's page |

Each deal is a folder under `runs/app-<time>/`. In demo mode, messages are written to its `outbox/` and nothing is emailed.

## Limits

One server process; no database beyond the ledger file; placement on the matrix needs a Word file. See `docs/deployment.md` for the full list.
