"""
문제 6 (7주). 훈련 샘플에 붙인 피처
====================================
구별 일일 민원 건수를 피처로 삼아, 인력 배치 모델의 훈련 샘플 12행에 피처를 붙인다.
피처 값은 7주차 실습이 읽는 6주차 확정 집계(3일치 x 3개 구 = 9행)이다.
피처의 타임스탬프는 "값이 알려진 시점"이며, 대상일의 집계는 그날이 끝나야 확정되므로 대상일 다음 날 00:00(UTC)이다.
피처의 유효 기간(TTL)은 3일이다. 학번마다 훈련 샘플의 구와 기준 시점(7월 1일~10일 09:00 UTC)이 다르다.

팀의 보고: "훈련 샘플 12행 전부에 피처를 붙였다. 훈련 셋이 줄지 않았으므로 조인은 정상이다."

실행: python exam/q6.py --id 학번
수정본은 q6_fixed.py 로 저장해 같은 방식으로 실행한다.
"""

import json
from datetime import datetime, timedelta, timezone

from common import PRACTICE, key, parse_id, pick_choice, pick_int

sid = parse_id()
INPUT_DIR = PRACTICE / "chapter7" / "data" / "input" / "ch6_daily"
DAYS = ["2026-07-01", "2026-07-02", "2026-07-03"]
TTL = timedelta(days=3)
CDS = ["11440", "11620", "11680"]


def build_feature_rows():
    rows = []
    for day in DAYS:
        summary = json.loads((INPUT_DIR / day / "daily_summary.json").read_text(encoding="utf-8"))
        known_at = datetime.fromisoformat(day + "T00:00:00+00:00") + timedelta(days=1)
        for r in summary["by_region"]:
            rows.append({"lawd_cd": r["lawd_cd"], "covers": day, "event_timestamp": known_at,
                         "complaint_count": int(r["count"])})
    return rows


SAMPLES = []
for i in range(12):
    cd = pick_choice(sid, f"q6-cd-{i}", CDS)
    day = pick_int(sid, f"q6-day-{i}", 0, 9)
    SAMPLES.append((cd, datetime(2026, 7, 1 + day, 9, 0, tzinfo=timezone.utc)))
SAMPLES.sort(key=lambda s: (s[1], s[0]))


def latest_value(rows, cd):
    cands = [r for r in rows if r["lawd_cd"] == cd]
    return max(cands, key=lambda r: r["event_timestamp"]) if cands else None


def latest_available(rows, cd, as_of):
    # 결함 1: 기준 시점까지 알려진 행에서만 최신값을 선택한다.
    cands = [r for r in rows if r["lawd_cd"] == cd and r["event_timestamp"] <= as_of]
    return max(cands, key=lambda r: r["event_timestamp"]) if cands else None


rows = build_feature_rows()
joined = []
n_dropped_no_value = 0
n_dropped_ttl = 0
n_leaked_future = 0
dropped = []
for cd, as_of in SAMPLES:
    original_hit = latest_value(rows, cd)
    if original_hit is not None and original_hit["event_timestamp"] > as_of:
        n_leaked_future += 1
    hit = latest_available(rows, cd, as_of)
    if hit is None:
        n_dropped_no_value += 1
        dropped.append({"lawd_cd": cd, "as_of": as_of, "reason": "값 없음", "row": None})
        continue
    # 결함 2: 알려진 값도 TTL 3일을 초과하면 훈련 샘플에 붙이지 않는다.
    if as_of - hit["event_timestamp"] > TTL:
        n_dropped_ttl += 1
        dropped.append({"lawd_cd": cd, "as_of": as_of, "reason": "TTL 초과", "row": hit})
        continue
    joined.append({"lawd_cd": cd, "as_of": as_of, "row": hit})

print(f"피처 원천 {len(rows)}행, 훈련 샘플 {len(SAMPLES)}행")
for j in joined:
    print(f"  {j['lawd_cd']}  기준 {j['as_of']:%m-%d %H:%M} UTC  건수 {j['row']['complaint_count']}"
          f"  대상일 {j['row']['covers']}  알려진 시점 {j['row']['event_timestamp'].isoformat()}"
          f"  경과 {(j['as_of'] - j['row']['event_timestamp']).total_seconds() / 3600:g}시간")
for j in dropped:
    detail = ""
    if j["row"] is not None:
        detail = (f"  최근 알려진 시점 {j['row']['event_timestamp'].isoformat()}"
                  f"  경과 {(j['as_of'] - j['row']['event_timestamp']).total_seconds() / 3600:g}시간")
    print(f"  탈락 {j['lawd_cd']}  기준 {j['as_of']:%m-%d %H:%M} UTC  사유 {j['reason']}{detail}")
assert len(SAMPLES) == len(joined) + n_dropped_no_value + n_dropped_ttl
assert all(timedelta(0) <= j["as_of"] - j["row"]["event_timestamp"] <= TTL for j in joined)
print(f"조인 결과 {len(joined)}행 -- 피처 부착 완료")
key("n_samples", len(SAMPLES))
key("n_joined", len(joined))
key("n_dropped_no_value", n_dropped_no_value)
key("n_dropped_ttl", n_dropped_ttl)
key("n_leaked_future", n_leaked_future)
key("sum_count", sum(j["row"]["complaint_count"] for j in joined))
