from pathlib import Path
from xml.sax.saxutils import escape
import json
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

ROOT = Path(__file__).resolve().parents[1]
r = json.loads((ROOT/'practice/chapter11/data/output/ch11_drift_report.json').read_text(encoding='utf-8'))
a, b = r['comparison_a_1hour'], r['comparison_b_9days_time_aligned']
answers = [
 [f"비교 A(1시간)는 ks_significant=false(p_value={a['p_value']})와 psi_band=주의(psi={a['psi']})가, 비교 B(9일)는 ks_significant=false(p_value={b['p_value']})와 psi_band=경보(psi={b['psi']})가 엇갈렸으며, 두 비교의 alert_level은 모두 주의이다.",
  'alert_rule.combine의 경보 조건은 KS 유의 AND PSI≥0.25이므로 A는 false AND false, B는 false AND true가 되어 모두 경보 조건을 충족하지 않는다.',
  '이후 주의 조건인 KS 유의 OR PSI≥0.1을 적용하면 두 비교 모두 false OR true이므로 주의로 확정된다.'],
 ['KS는 분포 차이의 통계적 유의성을, PSI는 구간 비율 이동의 크기를 판단하므로, 경보에 AND를 적용해 큰 표본의 사소한 차이에 대한 KS 유의와 작은 표본의 PSI 출렁임이 각각 단독으로 경보를 만들지 못하게 한다.',
  '경보 조건을 KS 유의 OR PSI≥0.25로 바꾸면 본인 비교 B는 PSI=0.3324만으로 경보가 되어 담당자 호출 대상으로 바뀌지만, 비교 A는 PSI=0.1193이고 KS도 비유의이므로 여전히 주의이다.',
  '따라서 OR는 더 쉽게 경보를 내어 대응 기회를 늘리는 대신 헛경보와 알림 피로를 늘릴 수 있고, AND는 보수적인 규칙이므로 주의 단계에서도 감시 강화와 원인 확인을 계속해야 한다.'],
 ['원인이 단위 오류나 결측 급증 같은 데이터 결함이라면, 그 데이터로 재학습한 모델은 실제 세상의 관계가 아니라 잘못된 단위와 누락 패턴에 맞춰진 손상된 상태를 학습한다.',
  '따라서 드리프트 경보와 성능 저하가 함께 확인됐어도 재학습부터 실행하지 말고 상류 파이프라인을 수리하고 오염 데이터를 정정하거나 격리해야 한다.',
  '복구된 데이터와 정답으로 성능을 다시 평가한 뒤 실제 관계 변화가 남아 있을 때 재학습을 검토하고, 새 모델도 challenger로 등록하여 승격 게이트를 통과시켜야 한다.']
]
titles=['KS·PSI의 엇갈림과 최종 알림 판정','AND를 사용하는 이유와 OR로 바꿀 때의 차이','데이터 결함일 때 재학습하면 안 되는 이유']
text='11주차 과제 서술형 답안\n202373020 전영준\n\n'+'\n\n'.join(f'{i}. {title}\n'+' '.join(ans) for i,(title,ans) in enumerate(zip(titles,answers),1))+'\n'
(ROOT/'11주차_서술형답안.txt').write_text(text,encoding='utf-8')
(ROOT/'실행증빙/답안문장.json').write_text(json.dumps(answers,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
pdfmetrics.registerFont(TTFont('Malgun','C:/Windows/Fonts/malgun.ttf'))
pdfmetrics.registerFont(TTFont('MalgunBold','C:/Windows/Fonts/malgunbd.ttf'))
styles={
 'title':ParagraphStyle('title',fontName='MalgunBold',fontSize=20,leading=29,textColor=HexColor('#183D60'),spaceAfter=9),
 'meta':ParagraphStyle('meta',fontName='Malgun',fontSize=10,leading=16,textColor=HexColor('#546474'),spaceAfter=19),
 'head':ParagraphStyle('head',fontName='MalgunBold',fontSize=12,leading=19,textColor=HexColor('#183D60'),spaceAfter=8),
 'body':ParagraphStyle('body',fontName='Malgun',fontSize=10.5,leading=18,wordWrap='CJK',spaceAfter=15),
 'foot':ParagraphStyle('foot',fontName='Malgun',fontSize=8,leading=13,textColor=HexColor('#546474'))}
story=[Paragraph('11주차 과제 | 모니터링',styles['title']),Paragraph('AI 데이터개발과 MLOps · 202373020 전영준',styles['meta'])]
for i,(title,ans) in enumerate(zip(titles,answers),1):
 story.extend([Paragraph(f'{i}. {title}',styles['head']),Paragraph(escape(' '.join(ans)),styles['body'])])
story.extend([Spacer(1,9),Paragraph('근거: 본인 실행 ch11_drift_report.json · 강의자료 4-8쪽<br/>교수자 제공 스냅샷 3종을 실제 재계산한 결과이며, 신규 API 수집은 수행하지 않았습니다.',styles['foot'])])
def footer(c,d):
 c.setFont('Malgun',8); c.setFillColor(HexColor('#546474')); c.drawRightString(A4[0]-43,28,str(d.page))
SimpleDocTemplate(str(ROOT/'11주차_과제답안.pdf'),pagesize=A4,rightMargin=43,leftMargin=43,topMargin=39,bottomMargin=40,title='11주차 과제 - 202373020 전영준',author='전영준').build(story,onFirstPage=footer,onLaterPages=footer)
print('PDF/TXT created; sentence counts:',list(map(len,answers)))
