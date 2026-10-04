"""실행 산출물과 입력·Spark 체크포인트를 대사한다. 실습을 재실행하지 않는다."""
from pathlib import Path
from datetime import datetime, timedelta, timezone
import ast
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
CH = ROOT / 'practice/chapter5'

def verify():
    report_path = CH / 'data/output/ch5_late_event_report.json'
    report = json.loads(report_path.read_text(encoding='utf-8'))
    source = CH / 'code/5-1-streaming-window-aggregation.py'
    tree = ast.parse(source.read_text(encoding='utf-8'))
    batches = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name) and n.target.id == 'BATCHES')
    checks = []
    def check(label, success):
        if not success:
            raise AssertionError(label)
        checks.append(label)
    check('watermark delay and window size', report['watermark_delay'] == report['window_size'] == '10 minutes')
    delay = timedelta(minutes=int(report['watermark_delay'].split()[0]))
    max_seen = None
    calculations = []
    events = {e['event_id']:e for e in report['late_events']}
    for name, rows in batches.items():
        disk_rows = [json.loads(line) for line in (CH/'data/input/stream'/name).read_text(encoding='utf-8').splitlines()]
        check('generated input matches source: '+name, rows == disk_rows)
        for row in rows:
            if row['event_id'] in events:
                event = events[row['event_id']]
                watermark = max_seen-delay
                event_time = datetime.fromisoformat(row['event_time'])
                check(row['event_id']+' event_time', event_time.strftime('%H:%M') == event['event_time'])
                check(row['event_id']+' watermark arithmetic', watermark.strftime('%H:%M') == event['watermark_at_arrival'].split()[0])
                start = event_time.replace(minute=(event_time.minute//10)*10,second=0)
                end = start + timedelta(minutes=10)
                calculated = '폐기' if end <= watermark else '수용'
                check(row['event_id']+' window decision', calculated==event['decision'])
                calculations.append({'event_id':row['event_id'],'max_event_time_before_arrival':max_seen.isoformat(),'watermark_delay':report['watermark_delay'],'watermark':watermark.isoformat(),'window_start':start.isoformat(),'window_end':end.isoformat(),'decision':event['decision']})
        for row in rows:
            t=datetime.fromisoformat(row['event_time'])
            max_seen=max(t,max_seen) if max_seen else t
    rows = [r for b in report['micro_batches'] for r in b['rows']]
    jsonl_rows = [json.loads(s) for s in (CH/'data/output/ch5_window_counts.jsonl').read_text(encoding='utf-8').splitlines()]
    check('report and JSONL output identical',rows==jsonl_rows)
    check('accepted late event updates count 3 to 4',[r['count'] for r in rows if r['window_start']=='22:00' and r['district']=='강남구']==[3,4])
    check('dropped event window absent',not any(r['window_start']=='21:40' for r in rows))
    check('drop counter 0,0,1',report['dropped_by_watermark_cumulative']=={'batch1.json':0,'batch2.json':0,'batch3.json':1})
    final={}
    for row in rows:
        final[(row['window_start'],row['window_end'],row['district'])]=row['count']
    check('latest counts total 13 accepted of 14 inputs',sum(final.values())==13 and sum(map(len,batches.values()))==14)
    sliding=json.loads((CH/'data/output/ch5_sliding_demo.json').read_text(encoding='utf-8'))
    check('sliding batch count 14',sum(r['count'] for r in sliding['rows'])==14)
    # Raw Spark checkpoint metadata uses UTC epoch milliseconds.
    metadata=[]
    for p in sorted((ROOT/'실행증빙/checkpoint_offsets').glob('[0-9]*'),key=lambda p:int(p.name)):
        data=json.loads(p.read_text(encoding='utf-8').splitlines()[1])
        metadata.append({'batch':int(p.name),'batchWatermarkMs':data['batchWatermarkMs']})
    check('checkpoint offset evidence exists',bool(metadata))
    expected_ms=[int(datetime.fromisoformat(c['watermark']).replace(tzinfo=timezone(timedelta(hours=9))).timestamp()*1000) for c in calculations]
    by_batch={m['batch']:m['batchWatermarkMs'] for m in metadata}
    check('calculated arrival watermarks recorded in Spark batches 2 and 4',[by_batch.get(2),by_batch.get(4)]==expected_ms)
    return {'status':'PASS','checks':checks,'watermark_calculations':calculations,'checkpoint_watermarks':metadata,'final_accepted_count':sum(final.values()),'submission_sha256':hashlib.sha256(report_path.read_bytes()).hexdigest(),'note':'실제 실행 산출물 대사이며 새 Spark 실행·API 호출이 아님.'}

if __name__=='__main__':
    print(json.dumps(verify(),ensure_ascii=False,indent=2))
