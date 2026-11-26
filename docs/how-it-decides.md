# How the app decides

Code does everything it can. Analyzing a contract uses the AI once, for the one step that needs reading comprehension, and its answer is checked by code before anything happens. Two other uses are listed at the end of the table.

| Step | Who does it | How |
|---|---|---|
| Find every change | **Code** | Compares the contract with ACME's standard, sentence by sentence. Tracked changes are read directly. Edits made without tracking are found by comparing the file's text with the standard. |
| Skip a blank being filled in | **Code** | A change that only fills a bracketed blank of the standard, such as the customer's legal name, is not a deviation. |
| Find the matrix row for each change | **Code** | By the heading or Key Terms field where the change sits, and by the heading of a section the customer added. See [matrix-format.md](matrix-format.md). Rows that share a place are told apart by keywords. |
| Changes no row claims, or that a cell does not clearly cover | **Code** | Each is referred to whoever handles terms not in the matrix (the Deal Desk, for ACME), one request per change. Never guessed at. The Deal Desk finds out what is needed, gets any approval, and records the outcome and the authority it relied on, in its own words. The record shows that as the Deal Desk's statement, not verified in the system. |
| Say which level covers the change | **The AI, once** | Reads each change against its one row (or a short list) and names the lowest level whose cell covers it, quoting the cell. |
| Check the AI's answer | **Code** | The row must be one the code found. The level's cell must exist. The words quoted must really be in that cell. If any check fails, the AI is asked once more, and then the change is **not routed**: it goes to the matrix owner instead. |
| Cross-check the level against the numbers | **Code** | If the numbers the customer introduced (45 days, 3%, 2x, 99.9%) appear in a more senior level's cell and not in the level the AI named, code raises the routing to the lowest level that names them. It never lowers the AI's level. |
| Name the approvers | **Code** | Read from the matrix cell, not from the AI. A person is found by title in `people.csv`. |
| Draft the requests | **Code** | A fixed template. The AI supplies only two short lines: the exposure arithmetic and a labelled recommendation. |
| Record what each approver decided | **Code** | The portal stores each decision as data (who, approve or deny, their exact words, any delegation). The approval record is a table built from it. |
| Reminders, escalation, the ledger | **Code** | See [audit-and-ledger.md](audit-and-ledger.md). |
| Final check | **Code** | The seller uploads the contract at its latest revision. Code finds every change it still has against the standard and compares each one with the approvals. It passes only if every change is covered: approved, in the same words. A denied change still in the contract, a change still waiting, changed wording, or a change nobody submitted all fail, and the result shows where. Conditions are listed as a note, because the app cannot check they are met. |
| Appeals | **Code** | A denial can be appealed once, to the same approver, with the seller's new context. The record shows both decisions. |
| Signed-copy check (optional) | **Code, then the AI** | When the seller uploads a signed copy against an earlier round, code lists the differences from that round and the AI writes a check of each against the approvals. It approves nothing. |
| Playing approvers (demo mode only) | **The AI** | Stands in for the people, so the process can be shown. Every record says SIMULATED. |

## What this does not do

- **It does not decide the level by itself.** Reading "Net 45" against the cells needs the AI today. The checks above stop it from naming a row, a cell or an approver the matrix does not contain, and the numbers check stops it from choosing too low a level when a number matches a higher one. Neither can tell that it picked Level 2 where Level 1 would do, or catch a change with no number in it. Closing that gap is what [deterministic-rules.md](deterministic-rules.md) is for.
- **It handles ACME's standard agreement with changes.** A contract on the customer's own paper is refused with a plain message. It would need a different method and is not supported yet.
- **It places changes only in Word files.** A PDF or text file has no headings the program can read, so every change in it goes to the matrix owner. Ask the customer for the Word file.
