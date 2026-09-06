"""교수자 원본의 요약 함수를 사용해 제공 스냅샷을 재계산한다."""
from pathlib import Path
import hashlib
import importlib.util
import json
import subprocess
import sys
from datetime import datetime, timezone

BASE = Path(__file__).resolve().parent
ROOT = BASE.parent
REPO = ROOT / '02_강의저장소' / 'mlops_public'
SOURCE = REPO / 'practice/chapter1/code/1-1-public-api.py'
RAW = REPO / 'practice/chapter1/data/output/ch1_airquality_live_raw.json'
OUT = BASE / '제출파일'
EVIDENCE = BASE / '실행증빙'

def main():
    OUT.mkdir(exist_ok=True)
    EVIDENCE.mkdir(exist_ok=True)
    spec = importlib.util.spec_from_file_location('course_ch1', SOURCE)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    payload = json.loads(RAW.read_text(encoding='utf-8'))
    assert payload['response']['header']['resultCode'] == '00', 'API 처리 실패'
    items = module.extract_items(payload)
    assert len(items) == payload['response']['body']['totalCount'], '전체 건수 불일치'
    assert items, '빈 응답'
    summary = module.summarize_live(items)
    # 원본 함수는 live로 고정하므로, 재생 결과임을 명확히 표시한다.
    summary['source'] = 'snapshot'
    summary['source_note'] = '교수자 저장소의 실제 API 응답 스냅샷 재계산. 이번 실행에서 실시간 API를 호출하지 않음.'
    summary['snapshot_file'] = RAW.relative_to(REPO).as_posix()
    summary['snapshot_sha256'] = hashlib.sha256(RAW.read_bytes()).hexdigest()
    assert summary['pm10_reported'] + summary['pm10_missing'] == summary['station_count']
    assert summary['pm25_reported'] + summary['pm25_missing'] == summary['station_count']
    for name in ('pm10', 'pm25'):
        vals = [module.to_float(r.get(name + 'Value')) for r in items]
        vals = [v for v in vals if v is not None]
        assert summary[name + '_avg'] == (round(sum(vals) / len(vals), 1) if vals else None)
    assert module.to_float('-') is None
    assert module.to_float(None) is None
    assert module.to_float('21') == 21.0
    (OUT / 'ch1_api_summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    evidence = {
        'executed_at': datetime.now(timezone.utc).isoformat(),
        'python': sys.version,
        'repository': 'https://github.com/LeeSeogMin/mlops_public',
        'commit': subprocess.check_output(['git', '-C', str(REPO), 'rev-parse', 'HEAD'], text=True).strip(),
        'source_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        'snapshot_sha256': summary['snapshot_sha256'],
        'mode': 'snapshot',
        'checks': ['API resultCode=00', 'totalCount=record count', 'nonempty records', 'PM10/PM25 count invariants', 'means recalculated', 'missing markers conversion'],
        'status': 'PASS'
    }
    (EVIDENCE / 'verification.json').write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    log = f"mode=snapshot\nstation_count={summary['station_count']}\npm10_reported={summary['pm10_reported']}\npm10_missing={summary['pm10_missing']}\npm10_avg={summary['pm10_avg']}\npm25_avg={summary['pm25_avg']}\ndata_time={summary['data_time_min']}\nchecks=PASS\n"
    (EVIDENCE / '실행결과.log').write_text(log, encoding='utf-8')
    print(log)

if __name__ == '__main__':
    main()
