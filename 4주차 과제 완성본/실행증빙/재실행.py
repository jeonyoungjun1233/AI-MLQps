"""제출본을 바꾸지 않고 저장 기록 검증 및 SQLite 실습 재현. 외부 API 호출 없음."""
from pathlib import Path
from collections import Counter
import hashlib
import json
import shutil
import sqlite3
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
CH = ROOT / 'practice/chapter4'

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))

def verify():
    out = CH / 'data/output'
    delivery = read(out / 'ch4_delivery_report.json')
    dedup = read(out / 'ch4_dedup_report.json')
    checks = []
    def check(name, ok):
        if not ok:
            raise AssertionError(name)
        checks.append(name)
    for key, group, scenario in [('A_baseline','g-baseline','baseline'), ('B_at_most_once_crash','g-amo','amo'), ('C_at_least_once_crash','g-alo','alo')]:
        data = [json.loads(s) for s in (out / f'ch4_processed_{group}.jsonl').read_text(encoding='utf-8').splitlines()]
        ids = Counter(x['event_id'] for x in data if x['scenario'] == scenario)
        report = delivery['scenarios'][key]
        producer = read(out / f'ch4_produce_{scenario}.json')
        consumer = read(out / f'ch4_consume_{group}.json')
        check(key + ': actual isolated topic', producer['topic']==consumer['topic']==delivery['scenario_topics'][key])
        check(key + ': producer count', producer['sent'] == report['produced'])
        check(key + ': processed / unique / duplicate / lost', (sum(ids.values()), len(ids), sum(ids.values())-len(ids), report['produced']-len(ids)) == tuple(report[k] for k in ['processed_records','unique_events','duplicate_records','lost_events']))
        check(key + ': duplicated IDs', sum(v>1 for v in ids.values()) == report['duplicated_events'])
    events = [json.loads(s) for s in (CH/'data/input/ch4_alo_duplicate_stream.jsonl').read_text(encoding='utf-8').splitlines()]
    counts = Counter(e['event_id'] for e in events)
    check('dedup input counts', len(events)==dedup['input']['records'] and len(counts)==dedup['input']['distinct_event_ids'])
    a,b,c,d = [dedup[k] for k in ['A_naive_insert','B_unique_or_ignore','C_upsert_do_update','D_replay_full_stream']]
    check('naive / unique / upsert rows', a['rows']==len(events) and b['rows']==c['rows']==d['rows']==len(counts))
    check('duplicates absorbed', a['rows']-c['rows']==a['duplicate_rows']==b['ignored_duplicates']==len(events)-len(counts))
    check('corresponding upstream duplicate count', a['duplicate_rows']==delivery['scenarios']['C_at_least_once_crash']['duplicate_records'])
    check('business state invariant', c['business_state_fingerprint']==d['business_state_fingerprint'])
    check('observations double', c['total_observations']==len(events) and d['total_observations']==2*len(events))
    with sqlite3.connect(f'file:{(out / "ch4_dedup.sqlite").as_posix()}?mode=ro', uri=True) as db:
        rows=db.execute('SELECT event_id, partition, offset, first_seen_at FROM complaints_upsert ORDER BY event_id').fetchall()
        check('SQLite fingerprint', hashlib.sha256(repr(rows).encode()).hexdigest()[:16]==d['business_state_fingerprint'])
        observed=dict(db.execute('SELECT event_id,seen_count FROM complaints_upsert'))
        check('SQLite observations per event', observed=={k:2*v for k,v in counts.items()})
    before={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.glob('*') if p.is_file()}
    with tempfile.TemporaryDirectory(prefix='ch4-verify-') as tmp:
        target=Path(tmp)/'chapter4'
        shutil.copytree(CH,target,ignore=shutil.ignore_patterns('output','__pycache__'))
        result=subprocess.run([sys.executable,str(target/'run_dedup.py')],capture_output=True,text=True,encoding='utf-8')
        check('dedup rerun exit 0',result.returncode==0)
        rerun=read(target/'data/output/ch4_dedup_report.json')
        for key in ['input','A_naive_insert','B_unique_or_ignore','C_upsert_do_update','D_replay_full_stream']:
            check('rerun '+key,rerun[key]==dedup[key])
    check('submission artifacts unchanged', before=={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.glob('*') if p.is_file()})
    return {'status':'PASS','checks':checks,'note':'Kafka 저장 기록 대사 + 제공 스냅샷의 SQLite 재실행. 이 검증 명령은 새 Kafka 실험이나 실시간 API 호출을 하지 않음.'}

if __name__ == '__main__':
    print(json.dumps(verify(),ensure_ascii=False,indent=2))
