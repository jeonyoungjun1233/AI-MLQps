"""제출 JSON을 고정 입력과 독립 대조한다. Airflow 실행을 대체하지 않는다."""
from pathlib import Path
import csv
import hashlib
import json

BASE = Path(__file__).resolve().parents[1]
CH = BASE / 'practice/chapter6'
OUT = CH / 'data/output'


def main():
    report_path = OUT / 'ch6_batch_run_report.json'
    report = json.loads(report_path.read_text(encoding='utf-8'))
    with (CH / 'data/input/lawd_cd_seoul.csv').open(encoding='utf-8', newline='') as f:
        mapping = {r['region_std']: r['lawd_cd'] for r in csv.DictReader(f)}
    expected = [(20, 20, 18, 1, 1, 0), (18, 17, 16, 0, 1, 1), (22, 22, 20, 1, 1, 0)]
    aliases = {'강남': '강남구', '마포': '마포구', '관악': '관악구'}
    checks = []
    assert len(report['daily_runs']) == 3
    for run, table in zip(report['daily_runs'], expected):
        day = run['logical_date']
        rows = [json.loads(l) for l in (CH / f'data/input/complaints/{day}.jsonl').read_text(encoding='utf-8').splitlines()]
        seen = set()
        mapped = missing = unmapped = dup = 0
        for row in rows:
            key = row['complaint_id']
            if key in seen:
                dup += 1
                continue
            seen.add(key)
            region = (row['region_raw'] or '').strip()
            if not region:
                missing += 1
            elif aliases.get(region, region) in mapping:
                mapped += 1
            else:
                unmapped += 1
        actual = (len(rows), len(rows) - dup, mapped, missing, unmapped, dup)
        q = run['quality']
        assert actual == table == tuple(q[k] for k in ['physical','valid','mapped','missing','unmapped','dup_removed'])
        assert q['physical'] == q['mapped'] + q['missing'] + q['unmapped'] + q['dup_removed']
        assert q['valid'] == q['mapped'] + q['missing'] + q['unmapped']
        assert q['gate'] == 'PASS' and q['preservation_ok'] is True
        assert run['dagrun_state'] == 'success' and all(t['state'] == 'success' for t in run['tasks'])
        assert (OUT / f'daily/{day}/_SUCCESS').exists()
        checks.append({'day': day, 'counts': actual, 'table_matches': True})
    idem = report['idempotency_check']
    assert idem['identical'] is True and idem['rerun_state'] == 'success'
    assert idem['sha256_before'] == idem['sha256_after']
    for name, sha in idem['sha256_after'].items():
        assert hashlib.sha256((OUT / 'daily/2026-07-01' / name).read_bytes()).hexdigest() == sha
    fail = report['failure_run']
    assert fail['dagrun_state'] == 'failed'
    assert all(t['state'] == ('failed' if t['task_id'] == 'validate_input' else 'upstream_failed') for t in fail['tasks'])
    assert not (OUT / 'daily/2026-07-04/_SUCCESS').exists()
    weekly = report['weekly_run']
    assert weekly['dagrun_state'] == 'success' and weekly['summary']['preservation_ok'] is True
    assert weekly['summary']['physical_total'] == 60 and weekly['summary']['mapped_total'] == 54
    assert 'CH6_RUN_PASS' in (BASE / '실행증빙/run.log').read_text(encoding='utf-8')
    result = {'status': 'PASS', 'verification': '실행된 JSON과 입력의 독립 대조 (Airflow 실행 대체 아님)', 'daily': checks,
              'report_sha256': hashlib.sha256(report_path.read_bytes()).hexdigest(),
              'idempotency': True, 'expected_failure_propagation': True, 'weekly': True}
    (BASE / '실행증빙/검증결과.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
