"""교수자 강의 Markdown을 읽기용 PDF로 변환. 원본 저장소는 변경하지 않는다."""
from pathlib import Path
import re
import html
import shutil
import json
import hashlib
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import HexColor
import pymupdf

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / '02_강의저장소/mlops_public/lecture'
OUT = ROOT / '02_강의PDF'
OUT.mkdir(exist_ok=True)
QA = ROOT / 'tmp/pdfs/lectures'
QA.mkdir(parents=True, exist_ok=True)
pdfmetrics.registerFont(TTFont('Korean', 'C:/Windows/Fonts/malgun.ttf'))
pdfmetrics.registerFont(TTFont('KoreanBold', 'C:/Windows/Fonts/malgunbd.ttf'))
pdfmetrics.registerFontFamily('Korean', normal='Korean', bold='KoreanBold', italic='Korean', boldItalic='KoreanBold')
body = ParagraphStyle('body', fontName='Korean', fontSize=10, leading=16, spaceAfter=4, wordWrap='CJK', textColor=HexColor('#24364a'))
styles = {n: ParagraphStyle(f'h{n}', parent=body, fontName='KoreanBold', fontSize={1:22,2:15,3:12,4:11}[n], leading={1:31,2:22,3:19,4:17}[n], spaceBefore=14, spaceAfter=9, keepWithNext=True, textColor=HexColor('#174a70')) for n in range(1,5)}
cellstyle = ParagraphStyle('cell',parent=body,fontSize=8.4,leading=13,spaceAfter=0)
code = ParagraphStyle('code',parent=body,fontSize=8,leading=12,backColor=HexColor('#f1f4f8'),borderPadding=5,spaceAfter=1)

def inline(s):
    s=html.escape(s)
    s=re.sub(r'`([^`]+)`',r'<font color="#174a70">\1</font>',s)
    s=re.sub(r'\*\*(.+?)\*\*',r'<b>\1</b>',s)
    s=re.sub(r'\[([^\]]+)\]\((https?://[^)]+)\)',r'<link href="\2" color="#176090">\1</link>',s)
    return s

def convert(md, dest):
    lines=md.read_text(encoding='utf-8').splitlines()
    story=[]; i=0; fenced=False
    while i<len(lines):
        line=lines[i]; i+=1
        if line.strip().startswith('```'):
            fenced=not fenced
            story.append(Spacer(1,5)); continue
        if fenced:
            safe=html.escape(line).replace(' ','&#160;')
            story.append(Paragraph(safe or '&#160;',code)); continue
        if not line.strip():
            story.append(Spacer(1,3)); continue
        if line.lstrip().startswith('|'):
            block=[line]
            while i<len(lines) and lines[i].lstrip().startswith('|'):
                block.append(lines[i]); i+=1
            rows=[]
            for row in block:
                values=re.split(r'(?<!\\)\|',row.strip().strip('|'))
                if all(re.fullmatch(r'\s*:?-+:?\s*',v) for v in values): continue
                rows.append([Paragraph(inline(v.strip()),cellstyle) for v in values])
            n=max(map(len,rows))
            for row in rows: row.extend([Paragraph('',cellstyle)]*(n-len(row)))
            table=Table(rows,colWidths=[499/n]*n,repeatRows=1,hAlign='LEFT')
            table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),HexColor('#e5eef6')),('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,-1),.4,HexColor('#d5e0e8')),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]))
            story.extend([table,Spacer(1,9)]); continue
        match=re.match(r'^(#{1,4})\s+(.+)',line)
        if match:
            story.append(Paragraph(inline(match[2]),styles[len(match[1])]))
            continue
        line=re.sub(r'^>\s*','',line)
        if line.strip() in ('---','***'): continue
        indent=len(line)-len(line.lstrip())
        st=ParagraphStyle('indented',parent=body,leftIndent=min(indent*4,28))
        story.append(Paragraph(inline(line.strip()),st))
    def footer(c,d):
        c.setFont('Korean',8); c.setFillColor(HexColor('#62748a'))
        c.drawString(48,25,f'{md.stem} | 교수자 Markdown 원문 PDF 변환본')
        c.drawRightString(547,25,str(d.page))
    SimpleDocTemplate(str(dest),pagesize=(595.28,841.89),leftMargin=48,rightMargin=48,topMargin=38,bottomMargin=45,title=lines[0].lstrip('# '),author='원문: LeeSeogMin/mlops_public').build(story,onFirstPage=footer,onLaterPages=footer)

manifest=[]; combined=pymupdf.open(); toc=[]
for md in sorted(SOURCE.glob('ch[0-9][0-9].md')):
    week=int(md.stem[2:]); dest=OUT/f'{week:02}주차_강의자료.pdf'
    supplied=md.with_suffix('.pdf')
    if supplied.exists(): shutil.copy2(supplied,dest)
    else: convert(md,dest)
    doc=pymupdf.open(dest)
    toc.append([1,f'{week}주차 - '+md.read_text(encoding='utf-8').splitlines()[0].lstrip('# '),len(combined)+1])
    combined.insert_pdf(doc)
    for j,p in enumerate(doc):
        # PDF의 모든 페이지에 대해 텍스트가 존재하고 페이지 밖으로 벗어나지 않는지 확인한다.
        assert p.get_text().strip(),(dest.name,j)
        for b in p.get_text('blocks'):
            assert b[0]>=-1 and b[1]>=-1 and b[2]<=p.rect.width+1 and b[3]<=p.rect.height+1,(dest.name,j,b[:4])
        p.get_pixmap(matrix=pymupdf.Matrix(.7,.7)).save(QA/f'{week:02}-{j+1:02}.png')
    manifest.append({'week':week,'file':dest.name,'pages':len(doc),'mode':'original_pdf' if supplied.exists() else 'markdown_to_pdf','source':md.relative_to(ROOT).as_posix(),'source_sha256':hashlib.sha256(md.read_bytes()).hexdigest()})
    print(dest.name,len(doc),'pages')
combined.set_toc(toc)
combined.save(OUT/'00_전체강의_모아보기.pdf',garbage=4,deflate=True)
(OUT/'변환기록.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print('Combined pages:',len(combined))
