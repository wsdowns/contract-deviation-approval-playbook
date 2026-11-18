# Stage 2: Locate the delegation of authority rule (Brightwater Logistics, run 2)

Annual fees from the deal profile: $20,000. Term 1 year. Matrix checked: `doa_matrix.csv` (sha256 prefix 91963d57eb28fc40).

| ID | Matrix row | Outcome | Cell relied on (exact words) | Approver titles | Joint? | Prerequisites | Reasoning |
|---|---|---|---|---|---|---|---|
| D1 | General liability cap | Route to Level 2 | Level 2: "Up to 2x fees: Associate General Counsel" | Associate General Counsel | No | None | 2x of $20,000 is $40,000. Level 1 covers only "Up to 1.5x fees" ($30,000), so it does not cover 2x. Not in the Not approvable cell ("Uncapped general liability; any cap above 3x fees or $5M"). |
| D2 | Service levels and credits (one cell names availability and credits) | Route to Level 1 | Level 1: "99.9% availability, credits up to 15%: VP Customer Success" | VP Customer Success | No | None | 2a (99.9%) and 2b (15%) match the Level 1 cell word for word. 2c (sole remedy) is the standard. Nothing requested falls in Not approvable ("Availability above 99.95%; credits paid in cash; uncapped credits"). Monthly credit dollars: $20,000 / 12 = $1,666.67 a month (assumes Fees spread evenly); 15% is $250.00 a month, at most $3,000 a year; standard 10% is $166.67 a month, $2,000 a year. |
| D3 | Payment terms | Route to Level 1 | Level 1: "Net 45: Deal Desk Manager" | Deal Desk Manager | No | None | Net 45 from invoice date matches the cell. Not the Not approvable item "payment terms that run from Customer's receipt or approval of invoice", because the redline runs from "the invoice date". |
| D4 | Renewal price increase cap | Route to Level 2 | Level 2: "Cap at 3%: VP Finance" | VP Finance | No | None | A 3% cap is below the Level 1 cell ("Cap at 5%: Deal Desk Manager"), so Level 1 does not cover it. First renewal: 3% of $20,000 is $600 (fees up to $20,600); the standard 7% is $1,400 (up to $21,400). |
| D5a | Publicity | Pre-approved | Level 1: "Pre-approved: remove Provider's publicity right: Contracts Manager" | Contracts Manager | No | None | Deleting the Provider's right to name Customer or use its logo is "remove Provider's publicity right". No escalation. |
| D5b | Publicity | Authority unclear | Level 1: "Pre-approved: remove Provider's publicity right: Contracts Manager". Standard: "Provider may name Customer in customer lists". No other cell names a Provider promise or a consent condition. | Not determined | Not determined | None | The cell names removing a right. 5b adds a Provider promise ("will not ... without Customer's prior written consent") and a consent exception, which the cell does not name. The matrix does not clearly say whether Level 1 covers it. I did not pick a level. |

**Questions for the matrix owner** (General Counsel, per `settings.csv`)

1. **D5b.** Does "Pre-approved: remove Provider's publicity right: Contracts Manager" cover a clause saying "Provider will not identify Customer or use Customer's name or logo in any marketing or customer list without Customer's prior written consent"? Options as I see them: (A) yes, the Contracts Manager's pre-approval covers it; (B) no, it goes beyond "remove Provider's publicity right", and the matrix owner names who approves it; (C) no, and no row covers it, so it is Not in matrix and the owner decides whether to add a row.

**Flags**

1. **Matrix versus agreement, standard positions** (matrix used each time, for the matrix owner to review):
   - D2: agreement silent; matrix "99.5% availability; credits up to 10% of monthly fees; credits are the sole remedy".
   - D3: agreement defers to the Order Form; matrix "Net 30 from invoice date".
   - D4: agreement silent; matrix "Fees may increase up to 7% at each renewal".
   - D5: matrix "Provider may name Customer in customer lists"; agreement Section 12.8 covers "name and logo in marketing". Different scope in words.
   - Suspension (not requested, but D3 touches it): matrix says "more than 30 days overdue"; agreement says "an outstanding, undisputed balance ... for more than 30 days".
2. **D2, credit form.** The redline says Provider will "credit Customer" but not how. Not approvable lists "credits paid in cash". The redline does not ask for cash, so I did not treat it as Not approvable. The requests say the wording is silent.
3. **D2, deliverability.** Whether ACME can meet 99.9% is not in the profile. The request says "not provided".
4. **D1, mutual cap.** The 2x applies to Customer's liability as well. Included in the request so the approver sees it.
5. **Clause numbering.** Open question to the seller from Stage 1 (matched by name).
6. **Order Form** not provided.

**What I did not do or could not check**

- I did not name people. Names come in Stage 3.
- I did not check the Order Form, the CPI or any figures beyond the profile.
- I did not decide D5b. It waits for the matrix owner.
