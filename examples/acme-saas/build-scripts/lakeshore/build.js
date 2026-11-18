const fs = require('fs');
const { Document, Packer, Paragraph, TextRun, AlignmentType, Table, TableRow, TableCell, WidthType, BorderStyle, Footer, PageNumber, ShadingType } = require('docx');

const FONT = 'Times New Roman';
const SZ = 22; // 11 pt
const r = (t, o = {}) => new TextRun({ text: t, font: FONT, size: SZ, ...o });

// Paragraph helpers
const title = (t) => new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 240 }, children: [r(t, { bold: true, size: 28 })] });
const center = (t, o = {}) => new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 160 }, children: [r(t, o)] });
const body = (t) => new Paragraph({ alignment: AlignmentType.JUSTIFIED, spacing: { after: 160 }, children: [r(t)] });
const article = (n, t) => new Paragraph({ keepNext: true, spacing: { before: 240, after: 120 }, children: [r(`${n}.  ${t.toUpperCase()}`, { bold: true })] });
// section: number, heading, text
const sec = (n, h, t) => new Paragraph({ alignment: AlignmentType.JUSTIFIED, spacing: { after: 140 }, indent: { left: 0 },
  children: [r(`${n}  `), r(`${h}.`, { underline: {} }), r(`  ${t}`)] });
// sub-clause: (a) text
const sub = (l, t) => new Paragraph({ alignment: AlignmentType.JUSTIFIED, spacing: { after: 100 }, indent: { left: 720, hanging: 360 }, children: [r(`(${l})\t${t}`)] });
// definition
const def = (term, t) => new Paragraph({ alignment: AlignmentType.JUSTIFIED, spacing: { after: 120 }, indent: { left: 360 }, children: [r('“'), r(term, { bold: true }), r(`” ${t}`)] });

const border = { style: BorderStyle.SINGLE, size: 4, color: '000000' };
const borders = { top: border, bottom: border, left: border, right: border };
function table(widths, rows, header = true) {
  return new Table({
    width: { size: widths.reduce((a, b) => a + b, 0), type: WidthType.DXA },
    columnWidths: widths,
    rows: rows.map((cells, i) => new TableRow({
      cantSplit: true,
      children: cells.map((c, j) => new TableCell({
        width: { size: widths[j], type: WidthType.DXA }, borders,
        shading: header && i === 0 ? { type: ShadingType.CLEAR, fill: 'E7E6E6', color: 'auto' } : undefined,
        margins: { top: 60, bottom: 60, left: 100, right: 100 },
        children: [new Paragraph({ children: [r(c, { bold: header && i === 0, size: 20 })] })],
      })),
    })),
  });
}

const C = []; // content

C.push(title('SOFTWARE AS A SERVICE AGREEMENT'));
C.push(body('This Software as a Service Agreement (this “Agreement”) is entered into as of the date of the last signature below (the “Effective Date”) by and between Lakeshore Health, Inc., an Illinois corporation (“Customer”), and ACME, Inc., a Delaware corporation (“Supplier”). Customer and Supplier are each a “Party” and together the “Parties.”'));
C.push(center('RECITALS', { bold: true }));
C.push(body('A.  Customer is an integrated health care delivery system that requires secure, reliable, and compliant technology services to support its business operations.'));
C.push(body('B.  Supplier provides software as a service and wishes to provide its services to Customer on the terms of this Agreement.'));
C.push(body('NOW, THEREFORE, in consideration of the mutual promises in this Agreement, the Parties agree as follows:'));

// 1 Definitions
C.push(article(1, 'Definitions'));
C.push(body('Capitalized terms have the meanings given below or where they first appear in this Agreement.'));
C.push(def('Authorized User', 'means any employee, contractor, agent, or other individual authorized by Customer to use the Services.'));
C.push(def('Customer Data', 'means all data, information, and content, including Personal Information, that is submitted to, stored in, or processed by the Services by or for Customer or its Authorized Users.'));
C.push(def('Documentation', 'means Supplier’s user guides, specifications, and other descriptions of the Services, as updated from time to time.'));
C.push(def('Fees', 'means the amounts payable for the Services as stated in an Order.'));
C.push(def('Order', 'means an ordering document signed by both Parties that references this Agreement and describes the Services, quantities, Subscription Term, and Fees.'));
C.push(def('Personal Information', 'means any information that identifies or could reasonably be used to identify an individual, and any information protected by applicable privacy or data protection law.'));
C.push(def('Services', 'means the software as a service offerings, support, and related services described in an Order and the Documentation.'));
C.push(def('Subscription Term', 'means the period during which Customer may use the Services under an Order.'));

// 2 Services
C.push(article(2, 'Services'));
C.push(sec('2.1', 'Provision of Services', 'Supplier will provide the Services to Customer and its Authorized Users during each Subscription Term in accordance with this Agreement, the applicable Order, and the Documentation.'));
C.push(sec('2.2', 'Order of Precedence', 'If there is a conflict, the following order of precedence applies: (a) this Agreement, including its Exhibit; (b) the applicable Order; and (c) the Documentation.'));
C.push(sec('2.3', 'Restrictions on Customer', 'Customer will not (a) reverse engineer, decompile, or attempt to discover the source code of the Services, except to the extent applicable law prohibits this restriction; (b) sell, sublicense, or otherwise allow anyone other than its Authorized Users to access or use the Services; or (c) use the Services in violation of this Agreement or applicable law.'));

// 3 Fees and Payment
C.push(article(3, 'Fees and Payment'));
C.push(sec('3.1', 'Fees', 'Customer will pay the Fees stated in each Order. Except for the refunds expressly provided in this Agreement, Fees are non-refundable.'));
C.push(sec('3.2', 'Renewal Pricing', 'Fees for any renewal Subscription Term may increase by up to seven percent (7%) over the Fees for the prior Subscription Term.'));
C.push(sec('3.3', 'Invoicing', 'Supplier will invoice Fees annually in advance.'));
C.push(sec('3.4', 'Payment', 'Customer will pay each undisputed invoice within thirty (30) days after the invoice date.'));
C.push(sec('3.5', 'Disputes; Suspension', 'If Customer disputes any Fees in good faith, Customer must notify Supplier before payment is due and must pay all undisputed amounts on time. Supplier may temporarily suspend Customer’s access to the Services if an undisputed balance is more than thirty (30) days overdue, and will reinstate access promptly after Customer pays the balance.'));
C.push(sec('3.6', 'Taxes', 'Customer is responsible for sales, use, and similar taxes that Supplier itemizes on an invoice, but not for Supplier’s income taxes. Customer will provide its tax exemption certificate where applicable.'));
C.push(sec('3.7', 'Most Favored Customer', 'Supplier represents that the Fees and terms in each Order are at least as favorable as those Supplier offers to any other customer for similar services in similar volumes. If Supplier offers more favorable fees or terms to another customer, Supplier will promptly offer them to Customer, effective as of the date first offered to the other customer.'));

// 4 Term and Termination
C.push(article(4, 'Term and Termination'));
C.push(sec('4.1', 'Term', 'This Agreement begins on the Effective Date and continues for the longer of one (1) year or until all Orders have ended. Each Order continues for the Subscription Term stated in it and renews automatically for additional Subscription Terms unless either Party gives notice of non-renewal at least thirty (30) days before the Subscription Term ends.'));
C.push(sec('4.2', 'Termination for Convenience', 'Customer may terminate this Agreement or any Order for any reason or no reason on sixty (60) days’ written notice to Supplier. Supplier will refund any prepaid Fees for the period after the effective date of termination.'));
C.push(sec('4.3', 'Termination for Cause', 'Either Party may terminate this Agreement or any Order if the other Party materially breaches it and fails to cure the breach within thirty (30) days after written notice. Either Party may also terminate on notice if the other Party dissolves or stops conducting business without a successor, or becomes the subject of insolvency, receivership, or bankruptcy proceedings that continue for more than sixty (60) days.'));
C.push(sec('4.4', 'Effect of Termination', 'Upon expiration or termination, Customer’s right to use the Services ends, Supplier will delete Customer Data within sixty (60) days after Customer’s request, and each Party will return or destroy the other Party’s Confidential Information. Supplier will invoice all Fees accrued before termination, and Customer will pay the invoice according to Article 3.'));

// 5 Service Levels and Support
C.push(article(5, 'Service Levels and Support'));
C.push(sec('5.1', 'Service Levels', 'Supplier will meet the service levels in Exhibit A (Service Levels and Support). Service credits are Customer’s sole and exclusive remedy for a failure to meet a service level.'));
C.push(sec('5.2', 'Support', 'Supplier will provide support during Supplier’s normal business hours, as described in Exhibit A.'));

// 6 Customer Data
C.push(article(6, 'Customer Data, Privacy, and Security'));
C.push(sec('6.1', 'Ownership', 'As between the Parties, Customer owns all right, title, and interest in Customer Data. Supplier acquires no rights in Customer Data other than the limited right to use it as described in this Article 6.'));
C.push(sec('6.2', 'Use of Customer Data', 'Supplier may copy, display, modify, and use Customer Data only as needed to provide and maintain the Services. Supplier may also collect and analyze data about the use and performance of the Services and use it to maintain, improve, and promote Supplier’s products and services, but may disclose it to others only if it is aggregated and does not identify Customer or its Authorized Users.'));
C.push(sec('6.3', 'Data Location', 'Supplier will store Customer Data only in data centers located in the United States.'));
C.push(sec('6.4', 'Security', 'Supplier will use commercially reasonable efforts to secure the Services from unauthorized access, alteration, or use and other unlawful tampering.'));
C.push(sec('6.5', 'Certifications', 'Supplier will maintain a current SOC 2 Type II report and will give Customer its most recent report on request, subject to Article 10 (Confidentiality). Supplier will also maintain a current HITRUST CSF certification covering the Services and will give Customer a copy of its current certification on request.'));
C.push(sec('6.6', 'Prohibited Data', 'Customer will not submit to the Services patient, medical, or other protected health information regulated by the Health Insurance Portability and Accountability Act, unless the Parties have agreed in writing that Supplier may receive it.'));

// 7 Warranties
C.push(article(7, 'Warranties'));
C.push(sec('7.1', 'Mutual', 'Each Party represents and warrants that (a) it has the legal power and authority to enter into this Agreement; (b) it is duly organized, validly existing, and in good standing under the laws of the jurisdiction of its origin; and (c) it will comply with all applicable laws in performing its obligations or exercising its rights under this Agreement.'));
C.push(sec('7.2', 'From Customer', 'Customer represents and warrants that it and its Authorized Users have all rights necessary to submit Customer Data to the Services and to allow its use as described in this Agreement.'));
C.push(sec('7.3', 'From Supplier', 'Supplier represents and warrants that it will not materially reduce the general functionality of the Services during the Subscription Term.'));
C.push(sec('7.4', 'Warranty Remedy', 'If Supplier breaches the warranty in Section 7.3, Customer must give Supplier notice, with enough detail for Supplier to understand or replicate the issue, within forty-five (45) days after discovering the issue. Within forty-five (45) days after receiving that notice, Supplier will attempt to restore the general functionality of the Services. If Supplier cannot, Customer may terminate the affected Order and Supplier will refund a prorated portion of prepaid Fees for the remainder of the Subscription Term. Supplier’s restoration obligation and Customer’s termination right are Customer’s only remedies for a breach of Section 7.3.'));
C.push(sec('7.5', 'Disclaimer', 'Except for the warranties in this Article 7, each Party disclaims all other warranties and conditions, whether express or implied, including any implied warranties of merchantability, fitness for a particular purpose, and non-infringement.'));

// 8 Indemnification
C.push(article(8, 'Indemnification'));
C.push(sec('8.1', 'By Supplier', 'Supplier will defend, indemnify, and hold harmless Customer from and against any third-party claim that the Services, when used by Customer according to this Agreement, infringe or misappropriate that third party’s intellectual property rights, and all damages, awards, settlements, costs, and expenses, including reasonable attorneys’ fees, that arise from the claim.'));
C.push(sec('8.2', 'By Customer', 'Customer will defend, indemnify, and hold harmless Supplier from and against any third-party claim that (a) Customer Data, when used according to this Agreement, infringes or misappropriates that third party’s intellectual property rights; or (b) results from Customer’s breach of Section 2.3 (Restrictions on Customer), and all damages, awards, settlements, costs, and expenses, including reasonable attorneys’ fees, that arise from the claim.'));
C.push(sec('8.3', 'Procedure', 'The indemnifying Party’s obligations in this Article 8 are contingent upon the other Party (a) promptly notifying it of the claim; (b) providing reasonable assistance at the indemnifying Party’s expense; and (c) giving the indemnifying Party sole control over the defense and settlement of the claim. The other Party may participate in the claim with its own attorneys at its own expense.'));
C.push(sec('8.4', 'Changes to the Services', 'If required by settlement or court order, or if reasonably necessary in response to a claim under Section 8.1, Supplier may (a) obtain the right for Customer to continue using the Services; (b) replace or modify the affected component of the Services without materially reducing their general functionality; or (c) if neither (a) nor (b) is reasonable, terminate the affected Order and refund a prorated portion of prepaid Fees for the remainder of the Subscription Term.'));
C.push(sec('8.5', 'Exclusive Remedy', 'This Article 8, together with any termination rights, describes each protected Party’s exclusive remedy and each indemnifying Party’s entire liability for a claim covered by this Article 8.'));

// 9 Limitation of Liability
C.push(article(9, 'Limitation of Liability'));
C.push(sec('9.1', 'Exclusion of Certain Damages', 'Except for Excluded Claims and a breach of Article 10 (Confidentiality), neither Party will be liable to the other for lost profits or revenues, whether direct or indirect, or for consequential, special, indirect, exemplary, punitive, or incidental damages arising out of this Agreement.'));
C.push(sec('9.2', 'Cap on Liability', 'Except for Excluded Claims, each Party’s total cumulative liability arising out of this Agreement will not exceed the greater of (a) three (3) times the Fees paid or payable under this Agreement during the twelve (12) months before the event giving rise to the claim, or (b) five million dollars ($5,000,000).'));
C.push(sec('9.3', 'Excluded Claims', 'The limitations in Sections 9.1 and 9.2 do not apply to (a) a Party’s indemnification obligations under Article 8; or (b) death, bodily harm, or personal injury (together, “Excluded Claims”).'));
C.push(sec('9.4', 'Exceptions', 'Nothing in this Agreement will limit, exclude, or restrict a Party’s liability to the extent prohibited by applicable law.'));

// 10 Confidentiality
C.push(article(10, 'Confidentiality'));
C.push(sec('10.1', 'Obligations', 'Each Party will hold the other Party’s non-public information that is marked or would reasonably be understood as confidential (“Confidential Information”) in confidence and will use it only to perform this Agreement. Each Party will protect the other Party’s Confidential Information using at least the same protections it uses for its own similar information, but no less than a reasonable standard of care. A Party may disclose Confidential Information only to its personnel and advisors who need to know it and are bound by obligations at least as protective, and remains responsible for their compliance. Customer’s Confidential Information includes non-public Customer Data.'));
C.push(sec('10.2', 'Exceptions', 'Confidential Information does not include information that is or becomes public through no fault of the receiving Party, was known to the receiving Party without restriction before disclosure, is received from a third party without restriction, or is independently developed without use of the disclosing Party’s Confidential Information.'));
C.push(sec('10.3', 'Required Disclosures', 'A Party may disclose Confidential Information to the extent required by applicable law if, unless prohibited by law, it gives the other Party reasonable advance notice and reasonably cooperates, at the other Party’s expense, with its efforts to obtain confidential treatment.'));

// 11 Insurance
C.push(article(11, 'Insurance'));
C.push(sec('11.1', 'Required Coverage', 'During the term of this Agreement and for six (6) months after it ends, Supplier will carry (a) commercial general liability insurance with limits of at least $1,000,000 for each occurrence and $2,000,000 in the aggregate; (b) workers’ compensation insurance as required by law; and (c) cyber liability insurance with limits of at least $5,000,000 for each occurrence and in the aggregate. On request, Supplier will give Customer a certificate of insurance evidencing these policies.'));

// 12 IP
C.push(article(12, 'Intellectual Property'));
C.push(sec('12.1', 'Supplier Property', 'Supplier retains all rights in the Services and Documentation, subject to the rights granted to Customer in this Agreement.'));
C.push(sec('12.2', 'Customer Property', 'Customer retains all rights in Customer Data, subject to the rights granted to Supplier in this Agreement.'));
C.push(sec('12.3', 'Feedback', 'Supplier may use all feedback Customer provides about the Services freely and without restriction or obligation.'));

// 13 Publicity
C.push(article(13, 'Publicity'));
C.push(body('Supplier may identify Customer and use Customer’s name and logo in marketing to identify Customer as a user of Supplier’s products and services.'));

// 14 General
C.push(article(14, 'General'));
C.push(sec('14.1', 'Governing Law and Venue', 'This Agreement is governed by the laws of the State of Illinois, without regard to its conflict of laws rules. The Parties submit to the exclusive jurisdiction of the state and federal courts located in Cook County, Illinois.'));
C.push(sec('14.2', 'Assignment', 'Neither Party may assign any rights or obligations under this Agreement without the prior written consent of the other Party. However, either Party may assign this Agreement on notice to a successor if the assigning Party undergoes a merger, change of control, reorganization, or sale of all or substantially all of its equity, business, or assets to which this Agreement relates. Any attempted but non-permitted assignment is void.'));
C.push(sec('14.3', 'Force Majeure', 'Neither Party is liable for delay or failure to perform caused by an unforeseen event outside its reasonable control, provided that it took reasonable measures to avoid or mitigate the effects of the event. This section does not excuse Customer’s obligation to pay Fees. If such an event prevents the Services from materially operating for thirty (30) or more consecutive days, either Party may terminate the affected Order on notice, and Supplier will refund a prorated portion of prepaid Fees for the remainder of the Subscription Term.'));
C.push(sec('14.4', 'Notices', 'Notices must be in writing and sent to the notice address below. Notices are deemed given on confirmed delivery by email, registered or certified mail, or personal delivery, or two days after mailing by overnight commercial delivery.'));
C.push(sec('14.5', 'Independent Contractors', 'The Parties are independent contractors. Nothing in this Agreement creates a partnership, joint venture, or agency relationship.'));
C.push(sec('14.6', 'Survival', 'Articles 8, 9, 10, and 12, Section 4.4, and any other provision that by its nature should survive, will survive expiration or termination of this Agreement.'));
C.push(sec('14.7', 'Entire Agreement; Amendment', 'This Agreement, including its Exhibit and all Orders, is the entire agreement between the Parties about its subject matter and supersedes all prior agreements and understandings. It may be amended only by a written document signed by authorized representatives of both Parties.'));
C.push(sec('14.8', 'Waiver; Severability', 'No waiver is effective unless in writing. If any provision is held unenforceable, the rest of this Agreement remains in effect.'));
C.push(sec('14.9', 'Counterparts', 'This Agreement may be signed in counterparts, including by electronic signature, each of which is an original and all of which together are one instrument.'));

C.push(new Paragraph({ keepNext: true, spacing: { before: 240, after: 240 }, children: [r('IN WITNESS WHEREOF, the Parties have signed this Agreement by their authorized representatives.')] }));
const sigRows = [
  ['LAKESHORE HEALTH, INC.', 'ACME, INC.'],
  ['By: ______________________________', 'By: ______________________________'],
  ['Name: ____________________________', 'Name: ____________________________'],
  ['Title: _____________________________', 'Title: _____________________________'],
  ['Date: _____________________________', 'Date: _____________________________'],
  ['Notice address: [Customer address]', 'Notice address: [Supplier address]'],
];
const nob = { style: BorderStyle.NONE, size: 0, color: 'FFFFFF' };
C.push(new Table({
  width: { size: 9360, type: WidthType.DXA }, columnWidths: [4680, 4680],
  rows: sigRows.map((row, i) => new TableRow({ cantSplit: true, children: row.map(t => new TableCell({
    width: { size: 4680, type: WidthType.DXA }, borders: { top: nob, bottom: nob, left: nob, right: nob },
    children: [new Paragraph({ keepNext: true, spacing: { before: i === 0 ? 0 : 200 }, children: [r(t, { bold: i === 0 })] })] })) })),
}));

// Exhibit A
C.push(new Paragraph({ pageBreakBefore: true, alignment: AlignmentType.CENTER, spacing: { after: 240 }, children: [r('EXHIBIT A', { bold: true }), new TextRun({ break: 1 }), r('SERVICE LEVELS AND SUPPORT', { bold: true })] }));
C.push(sec('A.1', 'Availability', 'The Services will be available at least 99.5% of the time in each calendar month, excluding scheduled maintenance performed on reasonable advance notice.'));
C.push(sec('A.2', 'Service Credits', 'If availability falls below the commitment, Supplier will credit Customer the following percentage of the monthly Fees for the affected Services, applied to the next invoice. Service credits are Customer’s sole and exclusive remedy for a failure to meet the availability commitment.'));
C.push(table([4680, 4680], [
  ['Monthly availability', 'Service credit'],
  ['Below 99.5% but at least 99.0%', '5% of monthly Fees'],
  ['Below 99.0%', '10% of monthly Fees'],
]));
C.push(new Paragraph({ spacing: { after: 120 }, children: [] }));
C.push(sec('A.3', 'Support', 'Supplier will provide support during its normal business hours and will respond to support requests within the following times:'));
C.push(table([2340, 4680, 2340], [
  ['Severity', 'Description', 'Response'],
  ['1 - Critical', 'Services unavailable', '4 business hours'],
  ['2 - High', 'Major function impaired with no reasonable workaround', '1 business day'],
  ['3 - Medium', 'Function impaired with a reasonable workaround', '2 business days'],
  ['4 - Low', 'Questions and minor issues', '5 business days'],
]));
C.push(new Paragraph({ spacing: { after: 120 }, children: [] }));

const doc = new Document({
  styles: { default: { document: { run: { font: FONT, size: SZ } } } },
  sections: [{
    properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [
      r('Lakeshore Health SaaS Agreement (Supplier Form, Rev. 2026)    Page ', { size: 18 }),
      new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 18 }),
      r(' of ', { size: 18 }), new TextRun({ children: [PageNumber.TOTAL_PAGES], font: FONT, size: 18 }),
      r('    CONFIDENTIAL', { size: 18 }),
    ] })] }) },
    children: C,
  }],
});
Packer.toBuffer(doc).then(b => { fs.writeFileSync(process.argv[2], b); console.log('ok'); });
