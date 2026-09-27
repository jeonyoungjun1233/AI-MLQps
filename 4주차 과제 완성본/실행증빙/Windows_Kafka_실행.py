"""원본 전달/장애 코드를 유지하고 Windows의 토픽 삭제 파일 잠금을 피한다.

실습 전용 localhost:9092 브로커가 필요하다. 시나리오마다 새 토픽을 만들어
오염을 방지한다. 제출본을 재작성하므로 새 실험은 폴더 복사본에서 실행한다.
"""
from pathlib import Path
from datetime import datetime, timezone
import importlib.util
import json
import subprocess
import sys
import uuid

CH=Path(__file__).resolve().parents[1]/'practice/chapter4'
spec=importlib.util.spec_from_file_location('instructor_kafka',CH/'run_kafka.py')
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
prefix='public.complaint.received.v1.'+uuid.uuid4().hex[:12]
topics=[]
original_popen=subprocess.Popen

def new_topic(groups=('g-baseline','g-amo','g-alo')):
    # 신규 토픽은 기존 그룹의 커밋 대상이 아니므로 이전 실험 오프셋과 분리된다.
    suffix=['baseline','amo','alo'][len(topics)]
    module.TOPIC=prefix+'.'+suffix
    admin=module.KafkaAdminClient(bootstrap_servers=module.BOOTSTRAP,request_timeout_ms=15000)
    try:
        admin.create_topics([module.NewTopic(name=module.TOPIC,num_partitions=3,replication_factor=1)])
    finally:
        admin.close()
    topics.append(module.TOPIC)
    print('[Windows isolated topic]',module.TOPIC,flush=True)

class TopicPopen(original_popen):
    def __init__(self,args,*pos,**kwargs):
        args=list(args)
        if any(Path(str(s)).name in ('4-1-kafka-producer.py','4-2-kafka-consumer.py') for s in args) and '--topic' not in args:
            args+=['--topic',module.TOPIC]
        super().__init__(args,*pos,**kwargs)

if __name__=='__main__':
    module.reset_topic=new_topic
    subprocess.Popen=TopicPopen
    try:
        module.main()
    finally:
        subprocess.Popen=original_popen
    path=CH/'data/output/ch4_delivery_report.json'
    report=json.loads(path.read_text(encoding='utf-8'))
    report['topic']=prefix+'.<scenario>'
    report['scenario_topics']=dict(zip(report['scenarios'],topics))
    report['execution_note']='Windows 파일 잠금으로 토픽 삭제 대신 시나리오별 신규 토픽을 사용. 생산/소비/커밋/장애/집계 코드는 교수자 원본.'
    path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    subprocess.run([sys.executable,str(CH/'run_dedup.py')],cwd=CH,check=True)
