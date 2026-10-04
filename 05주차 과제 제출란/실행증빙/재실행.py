"""원본 제출 JSON을 보존하며 별도 임시 폴더에서 실제 Spark 실습을 재실행한다."""
from pathlib import Path
import json
import os
import shutil
import subprocess
import sys
import tempfile
import hashlib

ROOT=Path(__file__).resolve().parents[1]
CH=ROOT/'practice/chapter5'
EV=ROOT/'실행증빙'

def normalize(report):
    report=dict(report)
    report.pop('generated_at',None)
    report['micro_batches']=[{'micro_batch':b['micro_batch'],'rows':sorted(b['rows'],key=lambda r:(r['window_start'],r['district']))} for b in report['micro_batches']]
    return report

def main():
    env=os.environ.copy()
    # 이 PC에서 준비한 환경이 있으면 사용. 다른 PC에서는 사용자 환경을 사용한다.
    alias=Path(env.get('LOCALAPPDATA',''))/'Temp/mlops-ch5-work'
    local_python=alias/'tmp/ch5-venv/Scripts/python.exe'
    if os.name=='nt' and local_python.exists():
        python=str(local_python)
        java=next((alias/'tmp/ch4-runtime').glob('zulu*'))
        hadoop=alias/'tmp/ch5-hadoop'
        env.update(JAVA_HOME=str(java),HADOOP_HOME=str(hadoop),SPARK_HOME=str(alias/'tmp/ch5-venv/Lib/site-packages/pyspark'))
        env['PATH']=str(hadoop/'bin')+os.pathsep+str(java/'bin')+os.pathsep+env['PATH']
    else:
        python=sys.executable
    env.update(PYSPARK_PYTHON=python,PYSPARK_DRIVER_PYTHON=python,SPARK_LOCAL_IP='127.0.0.1',PYTHONIOENCODING='utf-8',PYTHONUNBUFFERED='1')
    outputs=[p for p in (CH/'data/output').iterdir() if p.is_file()]
    before={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in outputs}
    # Windows의 종료 중인 JVM이 디렉터리를 잠근 경우에도 검증 결과와 구분한다.
    # tempfile이 자신이 만든 디렉터리만 정리하며 제출 폴더에는 실행하지 않는다.
    with tempfile.TemporaryDirectory(prefix='ch5-rerun-',ignore_cleanup_errors=True) as temp:
        target=Path(temp)/'chapter5'
        target.mkdir()
        shutil.copy2(CH/'run_chapter5.py',target/'run_chapter5.py')
        shutil.copytree(CH/'code',target/'code',ignore=shutil.ignore_patterns('__pycache__'))
        with (EV/'재실행로그.txt').open('wb') as log:
            result=subprocess.run([python,str(target/'run_chapter5.py')],env=env,stdout=log,stderr=subprocess.STDOUT)
        if result.returncode:
            raise RuntimeError(f'Spark 재실행 실패(exit={result.returncode}); 재실행로그.txt 확인')
        original=json.loads((CH/'data/output/ch5_late_event_report.json').read_text(encoding='utf-8'))
        fresh=json.loads((target/'data/output/ch5_late_event_report.json').read_text(encoding='utf-8'))
        assert normalize(original)==normalize(fresh),'실제 Spark 재실행 결과 불일치'
        assert before=={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in outputs},'제출본 변경'
        record={'status':'PASS','spark_rerun_exit_code':0,'comparison':'generated_at과 동일 micro-batch 내부 행 순서만 제외, 나머지 제출 JSON 전체 동일','original_generated_at':original['generated_at'],'rerun_generated_at':fresh['generated_at'],'submission_unchanged':True,'api_requests':0}
    record['temporary_directory_retained']=Path(temp).exists()
    record['cleanup_note']='Windows 파일 잠금 시 임시 디렉터리가 남을 수 있으며 제출본과 무관함.'
    (EV/'재실행검증.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(record,ensure_ascii=False,indent=2))

if __name__=='__main__':
    main()
