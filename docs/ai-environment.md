# The AI environment: a setup gate

The playbook sends a company's contract terms, pricing, deal facts and approvers' names to an AI model. **Not every AI tool is fit for that.** Before any real deal goes in, the AI environment must pass this gate. If any must-have fails, use only stand-in data.

## Must-haves

| # | Requirement | What to check |
|---|---|---|
| 1 | **No retention you do not control.** Either a **zero data retention (ZDR)** agreement in writing, or a **private instance**: a model run on the company's own infrastructure, or a hosted private deployment inside the company's own cloud tenancy under its own agreement | The signed terms, not the marketing page. Ask what is still logged (for example abuse monitoring) and for how long |
| 2 | **No training on your inputs or outputs** | The agreement says so in terms |
| 3 | **Confidentiality that covers your customers' terms** | The agreement is at least as strict as the confidentiality duties you owe your customers; subprocessors are listed |
| 4 | **Access control and audit** | Named users, company sign-in, logs the company controls |
| 5 | **Known data location and deletion** | Where data is processed, and how to delete it |
| 6 | **Sign-off on record** | Legal and security have approved this environment for this use. Name, date, and the model and version |
| 7 | **Not a personal or free account** | Consumer chat apps and personal accounts are out for real deals |

## Fit for the task

Passing the gate makes an environment safe, not good. Before real use, **qualify the model**: run Case 1 from the examples folder, a stand-in with a known answer, and compare the record with its answer key. A model that misses changes, picks authority levels on its own, or reads silence as approval is not fit, however private it is.

The model must also hold the whole input in one conversation: the standard agreement, the matrix files, the deal profile and the contract under review.

## Record it

Add to every approval record header: the AI environment used (name, version, date), and who approved it.

## What this project did

The runs in this package used only fictional stand-in data, so the gate was not required for them. The model was reached through a command-line client on the author's own account. That setup would **not** qualify for a real deal until requirements 1 to 6 were confirmed.
