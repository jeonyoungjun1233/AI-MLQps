"""실행 JSON 값으로 TXT와 PDF를 만든다. PDF는 별도로 렌더링 검수한다."""
from pathlib import Path
import json
from xml.sax.saxutils import escape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4

BASE=Path(__file__).resolve().parents[1]
r=json.loads((BASE/'practice/chapter10/data/output/ch10_deploy_report.json').read_text(encoding='utf-8'))
c=r['consistency']
assert c['host_equals_container'] is True and not r['container'].get('skipped',False)
sections=[
('1. 호스트·컨테이너 예측값의 일치와 보증 범위',[
f"본인 파일에서 consistency.host_forecast={c['host_forecast']}이고 consistency.container_forecast={c['container_forecast']}이다.",
"이는 이번에 실제 기동한 호스트와 컨테이너가 동일한 스모크 입력(lawd_cd=11680, 전일 건수 9)에 같은 예측을 반환하여, 이 사례에서 환경을 옮겨도 출력이 일치했음을 보증한다.",
"그러나 한 입력의 출력 일치만으로 모든 입력에서의 동등성, 모델·코드 바이트의 동일성, 실제 민원 예측 정확도, 부하 성능이나 향후 배포의 정상 동작까지 보증하지는 못한다."
]),
('2. 같은 예측값과 서로 다른 모델 출처 증명',[
f"본인 파일의 host.health.model_source=\"{r['host']['health']['model_source']}\"인 반면 container.health.model_source=\"{r['container']['health']['model_source']}\"이다.",
"호스트는 기동할 때 models:/complaint_daily_forecaster@champion으로 모델을 로드하고 레지스트리에서 별칭이 가리키는 버전 신원을 조회한다.",
"컨테이너는 빌드 시점의 champion 실물을 이미지의 /app/model에 고정하고 동봉된 export_info.json에서 이름·버전을 읽으므로, 둘 다 v1의 예측을 반환해도 출처를 확인하는 근거는 각각 레지스트리 조회와 이미지 안의 내보내기 기록이다."
]),
('3. 같은 코드라는 주장과 바이트 동일성 검증의 차이',[
"‘같은 코드로 만들었다’는 진술은 같은 소스에서 출발했다는 개발상의 출처 주장일 뿐, 다른 장으로 복사하는 동안의 한 줄 편집이나 줄바꿈·인코딩 변화를 배제하지 못한다.",
"원본과 복사본의 SHA-256을 계산해 대조하는 ‘바이트가 동일하다’는 검증은 파일 내용을 실제로 비교한 근거로서, 옮겨진 앱이 원본과 같은 파일인지 확인한다.",
"다만 같은 바이트의 앱에도 결함이 있을 수 있고 모델·설정·의존성은 별도로 달라질 수 있으므로, 파일 동일성 검증과 pytest·호스트·컨테이너 스모크 같은 실행 검증을 함께 해야 한다."
])]
text='10주차 과제 답안\nAI 데이터개발과 MLOps | 전영준 | 202373020\n\n'+'\n\n'.join(title+'\n'+'\n'.join(lines) for title,lines in sections)+'\n'
(BASE/'10주차_서술형답안.txt').write_text(text,encoding='utf-8')
pdfmetrics.registerFont(TTFont('Malgun','C:/Windows/Fonts/malgun.ttf'))
pdfmetrics.registerFont(TTFont('MalgunBold','C:/Windows/Fonts/malgunbd.ttf'))
s=ParagraphStyle('body',fontName='Malgun',fontSize=10,leading=16,wordWrap='CJK',spaceAfter=9)
h=ParagraphStyle('heading',parent=s,fontName='MalgunBold',fontSize=12,leading=19,spaceBefore=16,spaceAfter=10,textColor=colors.HexColor('#183B61'))
small=ParagraphStyle('small',parent=s,fontSize=8.2,leading=13,textColor=colors.HexColor('#666666'))
story=[Paragraph('10주차 과제 답안',ParagraphStyle('title',parent=h,fontSize=23,leading=30)),Paragraph('AI 데이터개발과 MLOps | 전영준 | 202373020',small)]
for title,lines in sections:
    story.append(Paragraph(escape(title),h))
    story.extend(Paragraph(escape(line),s) for line in lines)
story += [Spacer(1,16),Paragraph('근거: 본인 ch10_deploy_report.json의 consistency·host·container 및 실제 Docker 실행증빙.<br/>세 문항은 각각 3문장이다. 서빙 앱의 호스트·이미지 바이트 대조 결과는 별도 이미지검증.json에 보관했다.',small)]
def footer(canvas,doc):
    canvas.setFont('Malgun',8);canvas.setFillColor(colors.HexColor('#777777'))
    canvas.drawString(45,28,'10주차 | 모델 배포와 CI/CD | 실제 실행 결과')
    canvas.drawRightString(A4[0]-45,28,str(doc.page))
SimpleDocTemplate(str(BASE/'10주차_과제답안.pdf'),pagesize=A4,leftMargin=45,rightMargin=45,topMargin=30,bottomMargin=43,title='10주차 과제 답안',author='전영준').build(story,onFirstPage=footer,onLaterPages=footer)
print('Generated TXT and PDF; 3/3/3 sentences')
