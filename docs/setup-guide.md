# Setup guide

This guide takes you from a fresh download to a first run. Each step says what to do and how to know it worked. Allow an afternoon for the first run, most of it spent on your matrix.

## 1. What you need

- Python 3.11 or later.
- Your organization's standard agreement as a text file, plus an optional Word copy for sellers to download.
- Your delegation of authority matrix, or the willingness to write one.
- Access to an AI model: the `claude` command, an API key, a server you run (open weights are fine), or any program that reads a prompt and prints an answer.
- For real deals only: an AI environment that passes the setup gate in `docs/ai-environment.md`.

## 2. Install

```bash
git clone <this repository>
cd contract-deviation-approval-playbook
pip install -r requirements.txt
```

Check: `python -m pytest -q tests` reports all tests passing.

## 3. Try the example first

```bash
python app/server.py
```

Open http://localhost:8765. You should see the ACME home page with a "Stand-in data only" banner. Open a finished example to see a complete run. Opening one does not call any AI.

## 4. Build your matrix

1. Copy `examples/acme-saas/doa-matrix` to a new folder, for example `my-matrix`.
2. Edit `doa_matrix.csv`: one row per contract term, with your standard position, your levels and your not-approvable positions. The format is in `docs/matrix-format.md`.
3. Edit `roles.csv` to list every title the matrix names.
4. Edit `people.csv` to say who holds each title, with real email addresses.
5. Edit `settings.csv`: the requester, the matrix owner, the record custodian, the pre-signature check and the approvals mailbox.
6. Validate:

```bash
python tools/doa_matrix.py validate my-matrix
```

Check: validation reports no errors. It catches an approver missing from the roles list, a term with no authority and no not-approvable entry, duplicate terms, and people assigned to unknown titles.

Edit in Excel if you prefer, then save as CSV (UTF-8) and validate again. The CSV files are the source of truth.

## 5. Add your standard agreement

Save it as plain text, with clause numbers kept, for example `contracts/our_standard.txt`. If you want sellers to download it from the app, also keep a Word copy.

## 6. Choose and configure the model

```bash
cp config.example.toml config.toml
```

Edit `config.toml`:

- `[matrix] folder` points at your matrix folder.
- `[contracts] standard_text` and `standard_download` point at your standard agreement files.
- `[model] backend` is one of `claude-cli`, `anthropic-api`, `openai-compatible` or `command`. For open weights served by Ollama, vLLM, llama.cpp or LM Studio, use `openai-compatible` with `base_url` and `name`.
- `api_key_env` is the name of the environment variable that holds your key. Never put the key in the file. Set it in your shell:

```bash
export ANTHROPIC_API_KEY="your key here"
```

`config.toml` and `.env` are git-ignored. Check: start the app. A bad setting produces a plain message naming the problem.

### People, logins and notifications

1. **Sellers.** Add `sellers.csv` to your matrix folder with the columns `Email`, `Name` and `Team`, one row per seller. Only listed sellers can start a deal. Approvers come from `people.csv`.
2. **Sign-in method.** Set `[auth] provider` in `config.toml`:
   - `none` is for demos. There are no passwords, and you pick who to act as.
   - `local` keeps users in `users.csv` as salted password hashes. Add each person with `python tools/users.py add you@company.com "Your Name"`. Use it only for early use and small teams, and only over HTTPS.
   - `proxy-header` is for a company single sign-on proxy that passes the verified email in a header.
3. **Where approvers go.** Set `[portal] base_url` to the address approvers will open, with `https` in real use. Put the app behind a reverse proxy that provides HTTPS.
4. **Notifications.** Set `[mail] backend` to `smtp` and fill in the host, port, user, `from_address` and `password_env`, which is the name of a variable holding the mail password. With `file`, messages are only written to the run folder, which is right for trying it out. Every request goes to the approver with the seller and the approvals mailbox copied.
5. **Send mode.** `auto` sends requests as soon as every recipient has been matched to a person in `people.csv`. If any recipient cannot be matched, nothing is sent, and the seller sees why. `confirm` waits for one click.

Approvers decide in the portal. Email carries only a link, and replies to it are not read.

### Demo mode and live mode

`[app] mode` is `"demo"` or `"live"`.

- **Demo.** The AI plays each approver. It sees only the request, the deal profile and the matrix rows where its own title has authority, never answer keys or other approvers' replies, and it decides through the same portal code a real approver uses. Every record says SIMULATED APPROVERS and is not proof of authority. Demo mode refuses to start with the `smtp` mail backend or with `stand_in_data_only = false`, so it cannot send email or touch a real deal. Under `[demo]` you can make titles stay silent or delegate, to show reminders and escalation, and a button on the requests screen moves the demo clock to the next business day.
- **Live.** Real approvers decide in the portal, real email goes out, and the setup gate in `[environment]` applies.

### Reminders and escalation

Approvers have an obligation to act on requests, so a silent request is chased. Under `[reminders]` in `config.toml`, set when the first and second reminders go out and when it escalates, in business days from the day the request was created (weekends and any `holidays` you list are skipped). The app checks every `check_minutes`; if you would rather run the check from cron, `python tools/reminders.py` does one check.

- **Reminders:** a fixed message to the approver, and to anyone the request was delegated to, with the seller and the approvals mailbox copied.
- **Escalation:** the seller and the matrix owner are told at the same moment. If `people.csv` has a `Fallback name` and `Fallback email` for that approver, that person is also given the request and can decide it, recorded as acting for the approver. Without one, the matrix owner decides who steps in.
- Nothing is ever decided for an approver, and the AI is not involved.

### The ledger

Every portal decision, every approval record and every deal is added to `ledger.db`, an append-only SQLite file. Set its location and privacy under `[ledger]`. The matrix owner reads it at `/audit`. Back it up, restrict who can read the file, and decide how long to keep it. It is git-ignored and must never be published.

## 7. Qualify the model

A model that passes the privacy gate can still be unfit for the task. Run Case 1 in the app, and compare the approval record with `examples/acme-saas/cases/case-1-acme-redline/answer-key.md`. Do not read the key before the run. The model is fit if it finds every change, takes each approver from the matrix, and never reads silence as approval. Qualify again when you change models.

Note: your own matrix has no answer key, so qualification runs on the ACME case. If you replace the example case, write a key for your own case first.

## 8. Pass the setup gate before real deals

Fill in `[environment]` in `config.toml`: the environment name and version, who approved it, the date, and whether it is zero data retention or a private instance. Then set `stand_in_data_only = false`. Until the record is complete, the app refuses to start a run on a real deal. The seven requirements are in `docs/ai-environment.md`. Legal and security sign off before you change this setting.

## 9. Run a real deal

1. Prepare the deal profile from your CRM.
2. On the first screen, choose "Upload a contract" and pick the file the customer sent: a Word file with tracked changes works best. The app compares it with your standard agreement before the AI starts, and tells you if any text changed without being tracked.
3. Follow the steps on screen. Requests go to approvers under the send mode you set.
4. When the customer sends the next round, upload it and choose "A later round of" the earlier upload. The app shows what is new this round, and the AI marks each change as new, already decided, changed since it was decided, or reinserted after a denial. Only the ones that need a decision go to approvers.
5. When the signed copy comes back, upload it, choose the last agreed round, and tick "This is the signed copy". The app says whether it matches that draft exactly, and the AI checks every change against the approvals.
6. At the end, file the approval record, the original replies and the signed contract together, as the record custodian.

## What is not set up yet

- Reminders and escalation when an approver is silent.
- The OIDC sign-in provider.
- The unique request ID.
- A blank starter matrix folder. Copy the ACME example for now.
- An automated qualification check. Compare the record with the key by hand.

## If something goes wrong

| Symptom | Likely cause |
|---|---|
| The app will not start and names a path | A path in `config.toml` is wrong. Paths are relative to the file |
| "Matrix folder not found" | Check `[matrix] folder` |
| "The environment variable ... is empty" | Export the variable in the same shell that starts the app |
| "Could not reach the model server" | The server is not running, or `base_url` is wrong |
| Real-deal mode refuses to start a run | The `[environment]` record is incomplete |
| A step fails partway | Read the message on the page, fix the cause, and run the step again |
