# Deployment guide

How to put the seller app on a server for a small group. It was reviewed for security before this guide was written, and the review found five problems that are now fixed (listed at the end), plus limits you need to know about. Read "Known limits" before you invite anyone.

The example uses a Linux server with a domain (here SELLERSASSOCIATE.COM) and Caddy for HTTPS. Any reverse proxy works.

## 1. Prepare the server

- Linux with Python 3.11 or later, and `poppler-utils` if you want PDF uploads (`pdftotext`).
- A DNS record pointing your domain at the server. Open ports 80 and 443 only. The app listens on `127.0.0.1:8765` and is not reachable from outside, so keep that port closed.
- A normal user for the app, for example `sellers`, owning the app folder.
- Copy the repository to the server and run `pip install -r requirements.txt`.

## 2. HTTPS

Logins and approvals must travel over HTTPS. Put Caddy in front: `deploy/Caddyfile.example` is a working starting point (certificate, 25 MB request limit, security headers). Do not start the app for real users until `https://yourdomain/` loads with a valid certificate.

## 3. Configuration and secrets

1. `cp config.example.toml config.toml` and edit it (see the setup guide).
2. Set `[portal] base_url` to your public address, `https://yourdomain`. The app refuses form submissions from any other address.
3. Keep every secret out of files. Put them in `/etc/sellers-associate.env`, readable by root only, and load them with `EnvironmentFile` (see `deploy/sellers-associate.service.example`):
   - the model key, named by `[model] api_key_env`
   - the mail password, named by `[mail] password_env`
   - `DOA_SECRET`, a long random string that signs session cookies. If you do not set it the app makes a `.secret` file instead. Either way, keep it the same across restarts, or everyone is signed out.
4. `config.toml`, `users.csv`, `.secret`, `ledger.db` and `runs/` are git-ignored. Check that they are never copied anywhere public.
5. Restrict the files: `chmod 600 config.toml users.csv .secret ledger.db` and `chmod 700 runs`.

## 4. The model

The app can use the `claude` command, an API key, or an OpenAI-compatible server. On a server, use an API key or a private model server. The `claude` command works only if it is installed and signed in for the app's user, and that ties the service to one person's account. For real deals the model must also pass the setup gate (`docs/ai-environment.md`).

## 5. Email

1. Choose an SMTP service and fill in `[mail]`. Send from an address on a domain you control.
2. Set up SPF, DKIM and DMARC for that domain, or approval emails will land in spam.
3. Test with a mailbox you own before any real approver is added.

## 6. Run it as a service

Copy `deploy/sellers-associate.service.example` to `/etc/systemd/system/`, edit the paths and user, then enable it. Logs go to `journalctl -u sellers-associate`. Watch for `login failed for ...` lines and `reminders:` lines.

## 7. Add people

1. `sellers.csv` in your matrix folder lists who may start deals. `people.csv` lists approvers, and optional fallback contacts.
2. For each login: `python tools/users.py add person@company.com "Name"` (it asks for a password of at least 12 characters). Do this on the server, so no password crosses email or chat.
3. Everyone in `people.csv` who will decide requests needs a login. So does anyone you expect to receive a delegation.

## 8. First-run order

Do these in order, and stop at the first one that fails.

1. Start in **demo mode** with `[auth] provider = "local"`. (Demo mode needs `[mail] backend = "file"` and `stand_in_data_only = true`.)
2. Open the site. Sign in as a seller. Confirm that someone who is not signed in sees only the sign-in page.
3. Upload the Brightwater redline from `examples/`. The AI approvers should decide within a minute, and every record should say SIMULATED.
4. Sign in as an approver. You should see only your own requests.
5. Move the demo clock forward, with a silent title set, and watch reminders and an escalation appear.
6. Sign in as the matrix owner and open **Audit the approvers**. Check the tables and the CSV export.
7. Switch to **live mode** with a test mailbox, one approver you control, and still only fictional data. Upload, receive the email, click the link, decide.
8. Pass the setup gate, set `stand_in_data_only = false`, and only then use a real contract with real approvers.

## 9. Backups

Back up nightly, to somewhere that is not the same server: `runs/`, `ledger.db`, `users.csv`, `config.toml`, and the matrix folder. The `.secret` file or `DOA_SECRET` too, if you want sessions to survive a restore. Restore once as a test. Decide how long to keep contracts and the ledger, since both hold customers' terms and approvers' names.

## 10. Known limits

These are real. None blocks a small private deployment, but each is something to know.

- **Sellers are separate, in one process.** Each signed-in seller has their own current deal and running job, and sees only their own runs. The state lives in the server's memory, so run one server process (not several workers), and a restart drops open jobs (finished runs are on disk and come back). Past a few dozen sellers, move that state to a database and the model calls to a queue; the seams are `PerSeller`, `visible()` and `start_job()` in `app/server.py`.
- **The AI still names the level.** Code finds each change, places it on a matrix row, takes the approvers from the matrix cell, and checks the AI's answer (the row, the level's cell and the words it quotes must match the matrix). What code cannot check is whether the level is the lowest that covers the change, so a contract written to mislead the AI could pick a higher or lower level of the right row. The record is built from the portal's decisions, so authority is checked again there. Closing the gap needs deterministic rules (`deterministic-rules.md`). See `how-it-decides.md`.
- **No spending limit.** Every upload costs a model call. With a few trusted users this is fine. Set a budget alert with your model provider.
- **Sign-out does not cancel a session.** The cookie expires after `session_hours`. Change `DOA_SECRET` to sign everyone out at once.
- **A failed reminder email is not retried.** It is logged. Watch the log early on.
- **Local logins are basic.** Salted password hashes, a lockout after five wrong tries, and no password reset by email. Move to single sign-on for anything larger.
- **The web server is Python's standard library server.** Keep it behind the proxy, which is what the examples do.
- **Time and holidays.** The clock is the server's, and holidays are listed by hand.

## 11. What the review fixed

1. A seller could point "open a finished run" at any folder on the server. It now accepts only real run names.
2. A request body of any size was read into memory. Requests over 25 MB are refused first.
3. Forms and API calls from another website were not checked. A request whose browser origin is not `base_url` is now refused.
4. Live mode could run with no sign-in at all. It now refuses to start unless a sign-in method is set.
5. Failed logins left no trace. They are now logged.

## 12. Go or no-go

Go when all of these are true: HTTPS works; secrets are only in the environment file; demo mode passed step 8.1 to 8.6; mail reaches an inbox; backups ran and restored once; the AI environment passed the setup gate; and you accept the known limits above.
