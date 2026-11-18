# Seller app

A small local web app that walks a seller through the playbook, one screen per step. It runs the playbook prompts through the `claude` command (Claude Code), so no API key is needed. It uses the Python standard library only.

```bash
python app/server.py
```

Then open http://localhost:8765. Set `PORT` to use another port. Set `DOA_STUB=1` to use canned model output when testing the app itself.

## Configuration

Copy `config.example.toml` to `config.toml` (git-ignored) to point the app at your own matrix folder and standard agreement, and to choose the model. With no `config.toml` it runs the ACME example on the `claude` command.

Backends: `claude-cli`, `anthropic-api`, `openai-compatible` (Ollama, vLLM, llama.cpp, LM Studio, OpenRouter, private deployments, open weights) and `command` (any program that reads the prompt on stdin). The file never holds a key, only `api_key_env`, the name of the environment variable that does. While `stand_in_data_only = true` the app shows a banner; set it to false for real deals and record the AI environment, or the app will not start a run (setup gate, `docs/ai-environment.md`). Any model must be qualified on Case 1 before real use.

## Approvers and the portal

Requests from an uploaded contract go to approvers as an email with a link. The approver signs in to `/portal`, reads the request and decides: approve, approve with conditions, deny, delegate to a colleague at their company (who cannot pass it on) or ask the seller a question. A decision is written to the run's inbox in the shape of a reply, with the signed-in person as sender, so the recording stage reads it unchanged. Staged cases keep their simulated mailbox. Sign-in methods and mail settings are in `config.example.toml`; `docs/setup-guide.md` has the steps.

## The six screens

1. **Hand over the contract.** The customer's redline, the standard agreement and the deal profile. "Find the changes" runs Stages 1 to 3. Nothing is sent.
2. **Check the summary.** The changes, who may approve each, and the drafted requests. One confirmation sends them.
3. **Requests sent.** The messages in the simulated outbox.
4. **Replies and record.** "Check the approvals mailbox" delivers replies and runs Stage 4.
5. **Next move.** The seller asks for a different position after a denial. The app never suggests one.
6. **Final check.** The seller says what the final contract says; the app checks every change against its approval.

## Simulated mailbox

Each run is a folder under `runs/app-<time>/` with `outbox/` and `inbox/`. Nothing is emailed. Replies come from the case's `approvals/` folder, and a reply arrives only if a request about the same point (same numbers, mostly the same words in the subject) was sent. All three cases are wired in: pick one on the first screen. A later reply (one in a case's `later-replies/` folder) arrives only after a request newer than the last reply on that point is sent, so a follow-up, a re-send or a chase is needed to get it. Case 2's paper and Case 3's redline are stand-ins built by `tools/build_case_inputs.py`.

## What it does not do

It does not send or read real email, check who really sent a reply, or keep a database. The model sees only the files it is given.
