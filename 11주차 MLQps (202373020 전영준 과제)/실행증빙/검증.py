"""저장된 입력을 독립 검산하고 임시 폴더에서 원본을 재실행. 제출본은 덮어쓰지 않음."""
from pathlib import Path
import hashlib,json,math,os,shutil,subprocess,sys,tempfile
ROOT=Path(__file__).resolve().parents[1]
work=ROOT/'practice/chapter11'
ev=ROOT/'실행증빙'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest=json.loads((ev/'원본대조.json').read_text(encoding='utf-8'))
assert all(sha(ROOT/p)==h for p,h in manifest.items())
report=work/'data/output/ch11_drift_report.json'
assert sha(report)==json.loads((ev/'실행정보.json').read_text(encoding='utf-8'))['report_sha256']
r=json.loads(report.read_text(encoding='utf-8'))
assert r['comparison_a_matches_ch2'] is True
def values(name):
 rows=json.loads((work/'data/input'/name).read_text(encoding='utf-8'))['response']['body']['items']
 return [float(x['pm10Value']) for x in rows if x.get('pm10Value') not in ('-', '',None)]
base=values('airquality_seoul_2200_0628.json')
results=[]
for key,name in [('comparison_a_1hour','airquality_seoul_2300_0628.json'),('comparison_b_9days_time_aligned','airquality_seoul_2200_0707.json')]:
 x=r[key]; curr=values(name); assert len(base)==len(curr)==40
 assert x['baseline_mean']==round(sum(base)/len(base),3)
 assert x['current_mean']==round(sum(curr)/len(curr),3)
 d=max(abs(sum(v<=t for v in base)/len(base)-sum(v<=t for v in curr)/len(curr)) for t in set(base+curr))
 assert round(d,4)==x['ks_statistic']
 ordered=sorted(base)
 def quantile(q):
  i=(len(ordered)-1)*q; k=int(i); return ordered[k]+(ordered[min(k+1,len(ordered)-1)]-ordered[k])*(i-k)
 edges=[-math.inf]+[quantile(i/5) for i in range(1,5)]+[math.inf]
 def counts(v): return [sum(lo<=z<hi for z in v) for lo,hi in zip(edges[:-1],edges[1:])]
 cb,cc=counts(base),counts(curr)
 assert cb==x['bins']['baseline_counts'] and cc==x['bins']['current_counts']
 p=[(n+.5)/(len(base)+2.5) for n in cb]; q=[(n+.5)/(len(curr)+2.5) for n in cc]
 psi=sum((v-u)*math.log(v/u) for u,v in zip(p,q))
 assert round(psi,4)==x['psi']
 kl1=sum(u*math.log(u/v) for u,v in zip(p,q)); kl2=sum(v*math.log(v/u) for u,v in zip(p,q))
 assert abs(psi-kl1-kl2)<1e-12 and x['psi_equals_kl_sum']
 assert round(kl1,4)==x['kl_base_to_curr'] and round(kl2,4)==x['kl_curr_to_base']
 sig=x['p_value']<x['alpha']; assert sig==x['ks_significant']
 band='경보' if psi>=.25 else '주의' if psi>=.1 else '안정'
 level='경보' if sig and psi>=.25 else '주의' if sig or psi>=.1 else '정상'
 assert band==x['psi_band'] and level==x['alert_level']
 results.append({'comparison':key,'ks':round(d,4),'psi':round(psi,4),'AND_level':level,'OR_level':'경보' if sig or psi>=.25 else level})
with tempfile.TemporaryDirectory(prefix='ch11-verify-') as temp:
 target=Path(temp)/'chapter11'
 shutil.copytree(work,target,ignore=shutil.ignore_patterns('output','__pycache__'))
 proc=subprocess.run([sys.executable,'-u',str(target/'run_chapter11.py')],capture_output=True,env={**os.environ,'PYTHONIOENCODING':'utf-8'})
 assert proc.returncode==0 and b'CH11_RUN_PASS' in proc.stdout
 for p in (work/'data/output').glob('*.json'):
  assert p.read_bytes()==(target/'data/output'/p.name).read_bytes(),p.name
 (ev/'재실행.log').write_bytes(proc.stdout+proc.stderr)
assert sha(report)==json.loads((ev/'실행정보.json').read_text(encoding='utf-8'))['report_sha256']
answers=json.loads((ev/'답안문장.json').read_text(encoding='utf-8'))
assert len(answers)==3 and all(len(x)<=3 for x in answers)
out={'status':'PASS','source_files':len(manifest),'report_sha256':sha(report),'independent_checks':results,'rerun_json_byte_identical':True,'sentence_counts':list(map(len,answers))}
(ev/'검증결과.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(out,ensure_ascii=False,indent=2))
