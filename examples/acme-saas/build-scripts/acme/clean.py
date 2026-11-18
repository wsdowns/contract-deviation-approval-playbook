import sys, re
sys.path.insert(0, '.')
from split import elements, text
from xml.sax.saxutils import escape

SRC = 'un/word/document.xml'
x = open(SRC, encoding='utf-8').read()
pre, els, post = elements(x)
assert text(els[6]) == 'Software as a Service Agreement'
assert text(els[9]).startswith('Key Terms')
assert text(els[16]).startswith('To use these')

FONT = '<w:rFonts w:ascii="Arial" w:eastAsia="Arial" w:hAnsi="Arial" w:cs="Arial"/>'
def run(t, bold=False):
    b = '<w:b/><w:bCs/>' if bold else ''
    return f'<w:r><w:rPr>{FONT}{b}<w:sz w:val="18"/><w:szCs w:val="18"/></w:rPr><w:t xml:space="preserve">{escape(t)}</w:t></w:r>'
def para(t, bold=False, after=80, jc=None):
    j = f'<w:jc w:val="{jc}"/>' if jc else ''
    return f'<w:p><w:pPr><w:spacing w:before="0" w:after="{after}"/>{j}</w:pPr>{run(t, bold)}</w:p>'

L, R = 2600, 7470
B = '<w:tblBorders>' + ''.join(f'<w:{s} w:val="single" w:sz="4" w:space="0" w:color="000000"/>' for s in ('top','left','bottom','right','insideH','insideV')) + '</w:tblBorders>'
def cell(w, paras):
    return f'<w:tc><w:tcPr><w:tcW w:w="{w}" w:type="dxa"/><w:tcMar><w:top w:w="80" w:type="dxa"/><w:bottom w:w="40" w:type="dxa"/></w:tcMar></w:tcPr>{"".join(paras)}</w:tc>'
def row(label, lines):
    return f'<w:tr><w:trPr><w:cantSplit/></w:trPr>{cell(L, [para(label, bold=True)])}{cell(R, [para(s) for s in lines])}</w:tr>'

key_terms = [
    ("Effective Date", ["The date of the last signature on this SaaS Agreement."]),
    ("Governing Law", ["The laws of the State of Delaware."]),
    ("Chosen Courts", ["The state and federal courts located in New Castle County, Delaware."]),
    ("Covered Claims", [
        "Provider Covered Claims: Any action, proceeding, or claim that the Cloud Service, when used by Customer according to the terms of the Agreement, violates, misappropriates, or otherwise infringes upon anyone else’s intellectual property or other proprietary rights.",
        "Customer Covered Claims: Any action, proceeding, or claim that (1) the Customer Content, when used according to the terms of the Agreement, violates, misappropriates, or otherwise infringes upon anyone else’s intellectual property or other proprietary rights; or (2) results from Customer’s breach or alleged breach of Section 2.1 (Restrictions on Customer)."]),
    ("General Cap Amount", ["1x the Fees paid or payable by Customer to Provider in the 12 month period immediately before the claim."]),
    ("Uncapped Claims", [
        "Notwithstanding anything to the contrary, the following claims are not subject to the General Cap Amount: (a) death, bodily harm, or personal injury; and (b) an Indemnifying Party’s indemnification obligation."]),
    ("DPA", ["Provider’s standard Data Processing Addendum, available from Provider on request."]),
    ("Security Policy", [
        "Provider will use commercially reasonable efforts to secure the Cloud Service from unauthorized access, alteration, or use and other unlawful tampering.",
        "Provider will maintain an annually updated SOC 2 Type II report and will give Customer its most recent report on request, subject to Section 10 (Confidentiality)."]),
    ("Insurance Minimums", [
        "During the Subscription Period and for six months after, Provider will carry: (a) commercial general liability insurance with limits of at least $1,000,000 for each occurrence and $2,000,000 in the aggregate; (b) workers’ compensation insurance as required by Applicable Laws; and (c) cyber liability insurance with limits of at least $5,000,000 for each occurrence and in the aggregate.",
        "Upon request, Provider will give Customer a certificate of insurance evidencing these policies. Provider’s insurance policies will not be considered as evidence of Provider’s liability."]),
]
tbl = (f'<w:tbl><w:tblPr><w:tblW w:w="{L+R}" w:type="dxa"/>{B}<w:tblLayout w:type="fixed"/>'
       f'<w:tblLook w:val="0400" w:firstRow="0" w:lastRow="0" w:firstColumn="0" w:lastColumn="0" w:noHBand="0" w:noVBand="1"/></w:tblPr>'
       f'<w:tblGrid><w:gridCol w:w="{L}"/><w:gridCol w:w="{R}"/></w:tblGrid>'
       + row("Key Terms", ["The key legal terms of this SaaS Agreement are as follows:"]).replace('<w:tc><w:tcPr><w:tcW w:w="%d"' % L, '<w:tc><w:tcPr><w:tcW w:w="%d"' % L)
       + ''.join(row(a, b) for a, b in key_terms) + '</w:tbl>')

opening = para("This Software as a Service Agreement (“SaaS Agreement”) is between ACME, Inc. (“Provider”) and [Customer legal name] (“Customer”). The Framework Terms have two parts: (1) the Key Terms below and (2) the Standard Terms that follow, which are incorporated by reference. If there is any inconsistency between the Key Terms and the Standard Terms, the Key Terms will control. Capitalized words have the meanings given in the Key Terms or the Standard Terms.", after=160, jc="both")

def retext(e, old, new):
    assert old in e, old
    return e.replace(old, new)

assert text(els[11]).startswith('Provider and Customer have not changed')
els[11] = para('Provider and Customer have not changed the Standard Terms except as stated in the Key Terms above. By signing below, each party agrees to this SaaS Agreement.', after=120)
sig = els[12]
sig = re.sub(r'<w:r>(?:(?!</w:r>).)*?<w:t[^>]*>Use email or postal address</w:t></w:r>', '', sig, flags=re.S)
sig = sig.replace('[official company name]', '[Customer legal name]')
els[12] = sig
els[15] = retext(els[15], '>Software as a Service Agreement<', '>Standard Terms<')
els[133] = retext(els[133], '&quot; means a word or phrase that is highlighted and capitalized, such as ',
                  '&quot; means a capitalized word or phrase defined in the Key Terms or an Order Form, such as ')

new = [els[6], opening, els[8], tbl] + els[10:16] + els[17:]
x = pre + ''.join(new) + post
# Variables were shown bold and colored; make them plain capitalized text
def unstyle(m):
    r = m.group(0)
    if re.search(r'<w:color w:val="(117086|0432FF|8C8D8E)"/>', r):
        r = r.replace('<w:b/>', '').replace('<w:bCs/>', '')
    return r
x = re.sub(r'<w:rPr>(?:(?!</w:rPr>).)*</w:rPr>', unstyle, x, flags=re.S)
# remove all colors and highlights
x = re.sub(r'<w:color [^>]*/>', '', x)
x = re.sub(r'<w:highlight [^>]*/>', '', x)
open(SRC, 'w', encoding='utf-8').write(x)
print('elements', len(els), '->', len(new))
