# Stage 1: Identify each changed term (Brightwater Logistics, run 2)

Prepared for Alex Easton, Account Executive. Contract under review: Brightwater's redline of ACME SaaS Agreement v1.0. Standards used: the standard agreement and the matrix `Standard position` column.

Source rule applied (standing instruction 4 and Stage 1 step 7): where the agreement is silent but the matrix has a standard position, the matrix is the standard.

**Deviations**

| ID | Clause | Standard position | Requested position (exact words) | Kind | Notes |
|---|---|---|---|---|---|
| D1 | Key Terms, General Cap Amount | Matrix: "1x fees paid or payable in the prior 12 months". Agreement: "1x the Fees paid or payable by Customer to Provider in the 12 month period immediately before the claim." The two agree. | "2x the Fees paid or payable by Customer to Provider in the 12 month period immediately before the claim." | Changed | Takes effect through Section 8.1 Liability Cap ("will not be more than the General Cap Amount"), which the counterparty did not edit. The cap is mutual ("each party's total cumulative liability"), so it also raises the cap on Customer's liability to Provider. The Key Terms "Uncapped Claims" entry points to the General Cap Amount and is unchanged. Sections 8.2 and 8.3 apply by reference and are unchanged. |
| D2 | New "Section 3.2 Service Levels" | Matrix: "99.5% availability; credits up to 10% of monthly fees; credits are the sole remedy". Agreement is silent (Section 1.2 says only "Technical Support as described in the Order Form"). Standard from matrix; agreement silent. | "Provider will make the Product available at least 99.9% of the time in each calendar month. If availability in a month is below 99.9%, Provider will credit Customer up to 15% of the Fees for that month, as Customer's sole remedy for the shortfall." | Changed | One matrix cell names availability and the credit cap together, so this is one deviation. Sub-items: **2a** availability, "at least 99.9% of the time in each calendar month" (standard 99.5%). **2b** credit cap, "up to 15% of the Fees for that month" (standard 10% of monthly fees). **2c** "Customer's sole remedy for the shortfall": same as the standard "credits are the sole remedy"; listed only so a human can check. Other clauses: Section 7 (Disclaimer of Warranties, "Provider makes no guarantees that the Product will always be ... function without disruptions") is unedited and sits against a new availability commitment. Section 5.3 termination for uncured material breach is unedited; 2c is the only language limiting it. Section 8.1 cap applies to credits. The text does not say how a credit is applied. |
| D3 | Section 4.2 Payment (agreement's "Payment" clause is Section 4.3) | Matrix: "Net 30 from invoice date". Agreement says only "according to the payment terms in the Order Form". Standard from matrix; agreement silent. | "Unless the Order Form states otherwise, invoices are payable within 45 days of the invoice date." | Changed | The Order Form can still override. Effects through unedited clauses: the Suspension clause (Section 2) lets Provider suspend for "an outstanding, undisputed balance on its account for more than 30 days", which under Net 45 can arise before the invoice is due (matrix says "overdue", agreement says "outstanding"). Section 4.4 Payment Dispute runs from "before payment is due", so the dispute window moves with the due date. Section 5.5 final invoice is paid "according to Section 4". |
| D4 | New "Section 4.4 Renewal Pricing" | Matrix: "Fees may increase up to 7% at each renewal". Agreement is silent (Section 5.1 renews automatically; "Fees" means amounts in an Order Form). Standard from matrix; agreement silent. | "On each automatic renewal, Provider may increase the Fees by no more than 3% over the Fees for the prior Subscription Period." | Changed | Takes effect through Section 5.1 (automatic renewal), unedited. Applies to every renewal, not only the first. |
| D5 | Section 12.8 Logo Rights | Matrix (Publicity): "Provider may name Customer in customer lists". Agreement: "Provider may identify Customer and use Customer's name and logo in marketing to identify Customer as a user of Provider's products and services." The wording differs (marketing and logo versus customer lists). | Deleted: "Provider may identify Customer and use Customer's name and logo in marketing to identify Customer as a user of Provider's products and services." Inserted: "Provider will not identify Customer or use Customer's name or logo in any marketing or customer list without Customer's prior written consent." | Removed and Added | Two parts that could be approved separately. **5a** Removed: Provider's right to name Customer or use its logo. **5b** Added: a promise by Provider, "will not identify Customer or use Customer's name or logo in any marketing or customer list without Customer's prior written consent", with a consent exception. No other clause carries this change. |

**Not treated as deviations** (wording only)

- Preamble: "[Customer legal name]" replaced by "Brightwater Logistics, Inc." (fills the blank).
- Section 12.3 Notices (wording only): "Notices will be deemed given" became "A notice is deemed given". Method, timing and addressee are unchanged.

**Questions for the seller**

1. Clause numbers in the redline do not match agreement v1.0. I matched by clause name. Please confirm:
   - "Section 12.3 Notices" is Section 12.9 in v1.0 (12.3 is Governing Law and Chosen Courts).
   - "Section 4.2 Payment" is Section 4.3 in v1.0 (4.2 is Taxes).
   - New "Section 3.2" would collide with 3.2 Prohibited Data, and new "Section 4.4" with 4.4 Payment Dispute.
2. The Order Form is not provided. Payment terms, support and fees sit there. Does it say anything on payment, availability or renewal pricing?
3. The profile does not say whether ACME can meet 99.9% availability today. Is that known?

**What I did not do or could not check**

- I did not judge any change or decide who approves. That is Stage 2.
- I could not check the Order Form (not provided) or the exhibits to the agreement beyond the Key Terms and Standard Terms.
- I relied on the redline's own statement that only clauses with changes are shown.
