import re
def elements(x):
    s=x.index('<w:body>')+8; e=x.rindex('</w:body>'); body=x[s:e]
    out=[];i=0;pat=re.compile(r'<(w:p|w:tbl|w:sectPr)[ >]')
    while True:
        m=pat.search(body,i)
        if not m: break
        tag=m.group(1);depth=0;o=re.compile(r'<(/?)'+tag+r'(?=[ >/])[^>]*?(/?)>')
        for mm in o.finditer(body,m.start()):
            if mm.group(2): continue
            depth+= -1 if mm.group(1) else 1
            if depth==0: j=mm.end();break
        out.append(body[m.start():j]); i=j
    return x[:s],out,x[e:]
def text(e): return ''.join(re.findall(r'<w:t[^>]*>([^<]*)</w:t>',e))
