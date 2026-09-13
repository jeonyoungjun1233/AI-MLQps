"""교수자 원본 실습 실행, 실제 결과 검증, LMS 서술형 답안 생성.

저장소 루트에서:
  .venv/Scripts/python.exe "01주차 과제 제출/02주차/실행증빙/재실행.py"
--current 와 --eda-input은 practice/chapter2 기준의 저장 응답 경로이다.
인증키와 네트워크 요청 없이 저장 응답을 재계산한다.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import platform
import statistics
import subprocess
import sys
from datetime import datetime, timezone, timedelta

BASE = Path(__file__).resolve().parents[1]
CHAPTER = BASE / 'practice/chapter2'
EVIDENCE = BASE / '실행증빙'


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def items(path):
    payload = read(path)
    assert payload['response']['header']['resultCode'] == '00'
    rows = payload['response']['body']['items']
    assert rows and len({r['stationName'] for r in rows}) == len(rows)
    assert len({r['dataTime'] for r in rows}) == 1, '입력 응답에 여러 측정 시각이 섞여 있습니다.'
    return rows


def values(rows, col):
    result = []
    for row in rows:
        try:
            value = float(row.get(col))
            if math.isfinite(value):
                result.append(value)
        except (ValueError, TypeError):
            pass
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--current', default='data/input/airquality_seoul_current.json')
    parser.add_argument('--eda-input', default='data/input/airquality_seoul_2200.json')
    args = parser.parse_args()
    baseline = CHAPTER / 'data/input/airquality_seoul_2200.json'
    current = (CHAPTER / args.current).resolve()
    eda_input = (CHAPTER / args.eda_input).resolve()
    for path in (current, eda_input):
        assert path.is_relative_to(CHAPTER.resolve()), '실습 폴더 내부의 저장 응답을 지정하세요.'
    provenance = read(EVIDENCE / '교수자_원본_해시.json')
    for entry in provenance['files']:
        assert sha(CHAPTER / entry['path']) == entry['sha256'], entry['path']
    base_rows, curr_rows, eda_rows = items(baseline), items(current), items(eda_input)
    assert base_rows[0]['dataTime'] != curr_rows[0]['dataTime'], '서로 다른 이벤트 시각이 필요합니다.'
    started = datetime.now(timezone(timedelta(hours=9))).isoformat()
    commands = [
        ['code/2-1-parse-api.py', '--input', eda_input.relative_to(CHAPTER.resolve()).as_posix()],
        ['code/2-2-drift-visualize.py', '--baseline', 'data/input/airquality_seoul_2200.json', '--current', current.relative_to(CHAPTER.resolve()).as_posix(), '--col', 'pm10Value', '--alpha', '0.05'],
    ]
    env = dict(os.environ, PYTHONIOENCODING='utf-8', PYTHONUTF8='1')
    runs = []
    for command in commands:
        result = subprocess.run([sys.executable, *command], cwd=CHAPTER, env=env, capture_output=True, text=True, encoding='utf-8')
        log = EVIDENCE / (Path(command[0]).stem + '.log')
        # These commands only read snapshots and never receive credentials.
        log.write_text(result.stdout + result.stderr, encoding='utf-8')
        runs.append({'command': ['python', *command], 'cwd': 'practice/chapter2', 'exit_code': result.returncode, 'log': log.relative_to(BASE).as_posix(), 'log_sha256': sha(log)})
        print(result.stdout, end='')
        if result.returncode:
            print(result.stderr, file=sys.stderr)
            raise SystemExit(result.returncode)
    output = CHAPTER / 'data/output'
    eda, drift = read(output / 'ch2_eda_summary.json'), read(output / 'ch2_drift_result.json')
    assert eda['station_count'] == len(eda_rows)
    assert eda['data_time'] == eda_rows[0]['dataTime']
    for col, count in eda['missing_by_field'].items():
        assert count == len(eda_rows) - len(values(eda_rows, col))
    for col, key in [('pm10Value', 'pm10_summary'), ('pm25Value', 'pm25_summary')]:
        seq = values(eda_rows, col)
        expected = {k: round(f(seq), 3) for k, f in [('min', min), ('max', max), ('mean', statistics.mean), ('median', statistics.median)]}
        assert eda[key] == expected
    assert sum(eda['pm10_grade_counts'].values()) == len(eda_rows)
    base, curr = values(base_rows, 'pm10Value'), values(curr_rows, 'pm10Value')
    assert drift['baseline_n'] == len(base) and drift['current_n'] == len(curr)
    assert drift['baseline_time'] == base_rows[0]['dataTime']
    assert drift['current_time'] == curr_rows[0]['dataTime']
    assert drift['baseline_mean'] == round(statistics.mean(base), 3)
    assert drift['current_mean'] == round(statistics.mean(curr), 3)
    from scipy.stats import ks_2samp
    ks = ks_2samp(base, curr)
    # Independently compute the empirical CDF maximum, including ties.
    d = max(abs(sum(x <= t for x in base) / len(base) - sum(x <= t for x in curr) / len(curr)) for t in set(base + curr))
    assert drift['ks_statistic'] == round(d, 4) == round(float(ks.statistic), 4)
    assert math.isclose(drift['p_value'], float(ks.pvalue), rel_tol=1e-12)
    assert drift['drift_detected'] == (drift['p_value'] < drift['alpha'])
    p, alpha, n = drift['p_value'], drift['alpha'], drift['baseline_n']
    if drift['drift_detected']:
        first = f'실행 결과 p_value={p:.16g}는 alpha={alpha}보다 작으므로, p_value < alpha일 때 드리프트를 감지한다는 판정 규칙에 따라 drift_detected=true가 되었다. 따라서 이 유의수준에서는 두 시점의 PM10 분포가 같다는 귀무가설을 기각한다.'
    else:
        relation = '크므로' if p > alpha else '같으므로'
        first = f'실행 결과 p_value={p:.16g}는 alpha={alpha}보다 {relation}, p_value < alpha일 때만 드리프트를 감지한다는 판정 규칙에 따라 drift_detected=false가 되었다. 따라서 이 유의수준에서는 두 시점의 PM10 분포가 같다는 귀무가설을 기각하지 못한다.'
    second = f'drift_detected=false는 두 시점의 분포가 같다는 증명이 아니라, 차이가 있다고 판단할 통계적 증거가 충분하지 않다는 뜻이다. 내 실행의 baseline_n={n}은 결측을 제외한 기준 시점의 PM10 표본 수로, 비교적 작은 표본에서는 검정력이 부족하여 실제 변화도 놓칠 수 있다. 따라서 분포의 동일성이 확인되었다고 보고하지 않고, 해당 표본과 유의수준에서 유의한 차이를 감지하지 못했다고 서술해야 한다.'
    answer = f'02주차 과제 서술형 답안\n\n1. p_value와 alpha에 따른 판정\n{first}\n\n2. false를 분포 동일성의 확인으로 보고하면 안 되는 이유\n{second}\n'
    (BASE / '02주차_서술형_답안.txt').write_text(answer, encoding='utf-8')
    paths = [baseline, current, eda_input, *[CHAPTER / c[0] for c in commands], *[output / f for f in ['ch2_eda_summary.json', 'ch2_drift_result.json', 'ch2_drift_visual.txt']], BASE / '02주차_서술형_답안.txt']
    evidence = {
        'status': 'PASS', 'started_at': started,
        'finished_at': datetime.now(timezone(timedelta(hours=9))).isoformat(),
        'execution_mode': 'saved_response_recalculation', 'network_calls_during_recalculation': 0,
        'time_basis': 'event_time: response.body.items[].dataTime (KST)',
        'python': platform.python_version(),
        'packages': {pkg: importlib.metadata.version(pkg) for pkg in ['pandas', 'numpy', 'scipy', 'requests', 'matplotlib']},
        'runs': runs,
        'checks': ['instructor_source_and_snapshot_hashes', 'API_response_structure', 'unique_station_names', 'uniform_event_time_per_input', 'distinct_baseline_current_event_times', 'station_count', 'field_missing_counts', 'PM10_PM25_min_max_mean_median', 'grade_count_total', 'baseline_current_n_and_means', 'independent_empirical_CDF_KS_statistic', 'scipy_KS_p_value', 'strict_p_less_than_alpha_rule'],
        'sha256': {p.resolve().relative_to(BASE.resolve()).as_posix(): sha(p) for p in paths},
        'drift_result': drift,
        'lms_submission_confirmed': False,
    }
    write(EVIDENCE / '검증결과.json', evidence)
    print('VERIFICATION PASS: 원본 코드, 입력, 산출물, 판정 규칙 검증 완료')


if __name__ == '__main__':
    main()
