"""검증된 JSON으로 답안 TXT·PDF와 선택 제출용 ZIP을 만든다."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
from html import escape
import json
import zipfile
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import HexColor

BASE = Path(__file__).resolve().parent.parent
s = json.loads((BASE / 'ch1_api_summary.json').read_text(encoding='utf-8'))
e = json.loads((BASE / '실행증빙/verification.json').read_text(encoding='utf-8'))
assert s['source'] == 'snapshot' and e['status'] == 'PASS'
stamp = datetime.fromisoformat(e['executed_at']).astimezone(timezone(timedelta(hours=9))).strftime('%Y-%m-%d %H:%M:%S KST')
questions = [
    ('1. 실제와 어긋난 예측 항목과 그 이유', [
        '실행 전 예측표를 작성하지 않아 실제와 어긋난 사전 예측 항목과 그 이유를 제시할 수 없다.',
        f'실행 후 원본 응답에서 pm10Value가 숫자형이 아니라 "{e["sample_pm10_value"]}"과 같은 문자열임을 확인했으며, 집계를 위해 숫자 변환이 필요함을 알게 되었다.',
        '이는 실행 후 관찰로, 사전 예측과의 비교 활동을 대신하지는 못한다.'
    ]),
    ('2. 코드가 가장 먼저 깨질 지점과 자동 검사 방법', [
        '응답의 response.body.items가 누락되거나 배열이 아니면 측정소 목록을 추출하는 단계에서 코드가 깨질 수 있다.',
        '집계 전에 response.header.resultCode가 "00"인지와 items가 배열인지 자동 검사하고, 조건을 만족하지 않으면 오류를 기록한 뒤 처리를 중단한다.',
        'HTTP 요청의 성공 여부만으로 정상 데이터라고 판단하지 않고 API 처리 결과와 응답 구조를 함께 확인한다.'
    ]),
    ('3. 보고값·결측·측정소 수 사이의 등식', [
        'pm10_reported + pm10_missing = station_count가 성립해야 한다.',
        f'이번 실행에서 {s["pm10_reported"]} + {s["pm10_missing"]} = {s["station_count"]}으로 검증되었으며, 각 측정소 레코드의 PM10 값은 보고값 또는 결측 중 하나로 분류된다.',
        '이번 관측 시각의 결측 0건이 모든 시각에 결측이 없음을 의미하지는 않는다.'
    ])
]
assert all(len(sentences) <= 3 for _, sentences in questions)
intro = [
    '학번: 202373020    이름: 전영준',
    f'실행 일시: {stamp}',
    '실행 방식: API 키 없이 교수자 제공 실제 응답 스냅샷 재계산 (source=snapshot).',
    '강의 PDF 9쪽의 스냅샷 실행 안내에 따라 원본 요약 함수를 사용했으며, 이번 실행에서 실시간 API를 호출하거나 가상 데이터를 생성하지 않았다.',
    '원본 코드는 키가 없으면 종료하므로 별도 재실행 파일에서 제공된 응답을 읽어 원본 요약 함수를 호출했다.'
]
result = f'원본 측정 시각 {s["data_time_min"]} | 서울 측정소 {s["station_count"]}개\nPM10 평균 {s["pm10_avg"]} μg/m³ | PM2.5 평균 {s["pm25_avg"]} μg/m³'
source = '근거: 01주차 강의자료 PDF 9쪽(스냅샷 실행), 10-11쪽(9. 과제).'
text = '01주차 과제 제출\n\n' + '\n'.join(intro) + '\n\n실행 결과\n' + result
for heading, sentences in questions:
    text += '\n\n' + heading + '\n' + '\n'.join(sentences)
text += '\n\n첨부: ch1_api_summary.json\n' + source + '\n'
(BASE / '01주차 과제 제출.txt').write_text(text,encoding='utf-8')
pdfmetrics.registerFont(TTFont('Malgun','C:/Windows/Fonts/malgun.ttf'))
pdfmetrics.registerFont(TTFont('MalgunBold','C:/Windows/Fonts/malgunbd.ttf'))
body=ParagraphStyle('body',fontName='Malgun',fontSize=9.5,leading=15,spaceAfter=5,wordWrap='CJK',textColor=HexColor('#26394b'))
heading=ParagraphStyle('heading',parent=body,fontName='MalgunBold',fontSize=11.5,leading=18,spaceBefore=12,spaceAfter=7,keepWithNext=True,textColor=HexColor('#17496a'))
title=ParagraphStyle('title',parent=heading,fontSize=24,leading=32,spaceBefore=0,spaceAfter=15)
story=[Paragraph('01주차 과제 제출',title)]
story += [Paragraph(escape(line),body) for line in intro]
story += [Paragraph('실행 결과',heading),Paragraph(escape(result).replace('\n','<br/>'),body)]
for label,sentences in questions:
    story.append(Paragraph(escape(label),heading))
    story.extend(Paragraph(escape(sentence),body) for sentence in sentences)
story += [Spacer(1,12),Paragraph('첨부: ch1_api_summary.json',body),Paragraph(escape(source),body)]
def footer(c,d):
    c.setFont('Malgun',8);c.setFillColor(HexColor('#66778a'))
    c.drawString(44,25,'AI 데이터개발과 MLOps | 202373020 전영준 | 스냅샷 실행')
    c.drawRightString(551,25,str(d.page))
pdf=BASE/'01주차 과제 제출.pdf'
SimpleDocTemplate(str(pdf),pagesize=(595.28,841.89),leftMargin=44,rightMargin=44,topMargin=34,bottomMargin=43,title='01주차 과제 제출',author='전영준').build(story,onFirstPage=footer,onLaterPages=footer)
with zipfile.ZipFile(BASE/'01주차 과제 제출.zip','w',zipfile.ZIP_DEFLATED) as z:
    for p in [pdf,BASE/'ch1_api_summary.json']: z.write(p,p.name)
print('PDF/TXT/ZIP 생성 완료. 각 문항 3문장.')
