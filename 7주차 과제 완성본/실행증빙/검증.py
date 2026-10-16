"""표준 라이브러리만 사용해 실제 실습 JSON과 원천 스냅샷을 대조한다."""
from pathlib import Path
import hashlib
import json

BASE = Path(__file__).resolve().parents[1]
CH = BASE / 'practice/chapter7'
OUT = CH / 'data/output'

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))

def main():
    r = read(OUT / 'ch7_feature_report.json')
    c = r['consistency']
    assert r['feast_version'] == '0.64.0'
    assert c == read(OUT / 'ch7_consistency_report.json')
    assert c['all_consistent'] is True and c['checked_keys'] == 3 and len(c['rows']) == 3
    latest = read(CH / 'data/input/ch6_daily/2026-07-03/daily_summary.json')
    rate = read(CH / 'data/input/ch6_daily/2026-07-03/quality_check.json')['unmapped_rate']
    by_key = {v['lawd_cd']: v['count'] for v in latest['by_region']}
    assert {v['lawd_cd'] for v in c['rows']} == set(by_key)
    for row in c['rows']:
        assert row['consistent'] is True
        assert row['offline_latest'] == row['online'] == {'complaint_count': by_key[row['lawd_cd']], 'day_unmapped_rate': rate}
    assert r['entity_rows_requested'] == 4
    assert len(r['historical_join']) == 3 and len(r['historical_dropped_rows']) == 1
    assert r['historical_dropped_rows'][0]['lawd_cd'] == '11620'
    expected = [('11680', '2026-07-02T09:00:00+00:00', 8, .05), ('11440', '2026-07-03T09:00:00+00:00', 5, .059), ('11680', '2026-07-04T09:00:00+00:00', 9, .045)]
    assert [(v['lawd_cd'],v['as_of'],v['complaint_count'],v['day_unmapped_rate']) for v in r['historical_join']] == expected
    assert read(OUT / 'ch7_feature_definitions.json')['feature_view']['ttl_days'] == 3
    t = read(BASE / '실행증빙/TTL검증결과.json')
    assert t['PASS'] is True and t['feature_age_hours_at_as_of'] == 105 and t['ttl_hours'] == 72
    assert t['historical_requested'] == 3 and t['historical_returned'] == 0
    assert dict(zip(t['online']['lawd_cd'], t['online']['complaint_count'])) == by_key
    assert 'CH7_RUN_PASS' in (BASE / '실행증빙/run.log').read_text(encoding='utf-8')
    result = {'status': 'PASS', 'all_consistent': True, 'checked_keys': 3,
              'historical_requested': 4, 'historical_returned': 3, 'historical_dropped': 1,
              'TTL_probe_passed': True, 'report_sha256': hashlib.sha256((OUT/'ch7_feature_report.json').read_bytes()).hexdigest()}
    (BASE/'실행증빙/검증결과.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__ == '__main__':
    main()
