"""
문제 2 (3주). 같은 집계를 두 계층에 두었다
===========================================
대기질 PM10을 한 시간 창으로 집계하는 파이프라인이 배치 계층과 스피드 계층에 같은 집계를 하나씩 두었다.
자료는 3주차 실습의 실제 응답 두 시점(22시, 23시) 80건이다. 원자료에는 도착 시각이 없으므로
3주차 실습과 같은 방식으로 도착 시각을 붙였다(기본 3분 지연, 일정 주기마다 72분 지연).
시험용으로 학번마다 지연 이벤트의 주기와 지연 허용 시간의 설정이 다르다.

운영팀의 보고: "두 계층 모두 정상 종료(종료 코드 0). 같은 규칙으로 집계했다."

실행: python exam/q2.py --id 학번
수정본은 q2_fixed.py 로 저장해 같은 방식으로 실행한다.
"""

import hashlib
import json
from datetime import datetime, timedelta

from common import PRACTICE, key, parse_id, pick_choice, pick_int

sid = parse_id()
INPUT_DIR = PRACTICE / "chapter3" / "data" / "input"
FILES = ["airquality_seoul_2200.json", "airquality_seoul_current.json"]
WINDOW_MIN = 60
GRACE_BATCH = 15                                   # 배치 계층의 지연 허용(분)
GRACE_SPEED_BEFORE = pick_choice(sid, "q2-grace", [5, 8, 10, 12])  # 수정 전 설정(비교용)
LATE_PERIOD = pick_int(sid, "q2-period", 4, 7)     # 정렬 순번이 이 값의 배수인 이벤트가 72분 늦게 도착


def load_events():
    rows = []
    for name in FILES:
        body = json.loads((INPUT_DIR / name).read_text(encoding="utf-8"))["response"]["body"]
        for item in body["items"]:
            if item.get("pm10Value") in (None, "-", ""):
                continue
            rows.append({
                "station": item["stationName"],
                "event_time": datetime.strptime(item["dataTime"], "%Y-%m-%d %H:%M"),
                "pm10": int(item["pm10Value"]),
            })
    rows.sort(key=lambda r: (r["event_time"], r["station"]))
    for i, row in enumerate(rows):
        delay = 72 if (i + 1) % LATE_PERIOD == 0 else 3
        row["arrival_time"] = row["event_time"] + timedelta(minutes=delay)
    return rows


def window_of(t):
    return t.replace(minute=0, second=0, microsecond=0)


def aggregate(rows, grace_min):
    """공유 집계: 창 경계, 도착 마감, 건수, 평균의 정의를 한 곳에 둔다."""
    buckets = {}
    for row in rows:
        win = window_of(row["event_time"])
        if row["arrival_time"] >= win + timedelta(minutes=WINDOW_MIN + grace_min):
            continue
        buckets.setdefault(win, []).append(row["pm10"])
    return {w.strftime("%Y-%m-%d %H:%M"): {"count": len(v), "pm10_mean": round(sum(v) / len(v), 2)}
            for w, v in sorted(buckets.items())}


def aggregate_batch(rows):
    return aggregate(rows, GRACE_BATCH)


def aggregate_speed(rows):
    return aggregate(rows, GRACE_BATCH)


def sha(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()[:16]


events = load_events()
batch = aggregate_batch(events)
speed = aggregate_speed(events)
speed_before = aggregate(events, GRACE_SPEED_BEFORE)


def differences(left, right):
    windows = sorted(set(left) | set(right))
    empty = {"count": 0, "pm10_mean": 0.0}
    pairs = [(left.get(w, empty), right.get(w, empty)) for w in windows]
    return (
        sum(b != s for b, s in pairs),
        sum(b["count"] - s["count"] for b, s in pairs),
        max((abs(b["pm10_mean"] - s["pm10_mean"]) for b, s in pairs), default=0.0),
    )


n_diff_before, missing_events_before, max_mean_gap_before = differences(batch, speed_before)
n_diff_after, missing_events_after, max_mean_gap_after = differences(batch, speed)


def print_comparison(title, left, right):
    print(title)
    print(f"{'창':<18}{'배치 건수':>10}{'배치 평균':>11}{'스피드 건수':>12}{'스피드 평균':>12}")
    for win in sorted(set(left) | set(right)):
        b = left.get(win, {"count": 0, "pm10_mean": 0.0})
        s = right.get(win, {"count": 0, "pm10_mean": 0.0})
        print(f"{win:<18}{b['count']:>10}{b['pm10_mean']:>11.2f}{s['count']:>12}{s['pm10_mean']:>12.2f}")

print(f"이벤트 {len(events)}건, 창 길이 {WINDOW_MIN}분")
print(f"지연 주기 {LATE_PERIOD}, 수정 전 지연 허용 배치 {GRACE_BATCH}분 / 스피드 {GRACE_SPEED_BEFORE}분")
print(f"수정 후 지연 허용 양쪽 {GRACE_BATCH}분, 동일 집계 함수 사용")
print_comparison("[수정 전]", batch, speed_before)
print(f"어긋난 창 {n_diff_before}개, 빠진 이벤트 {missing_events_before}건, 최대 평균 차이 {max_mean_gap_before:.2f}")
print(f"수정 전 해시: 배치 {sha(batch)}, 스피드 {sha(speed_before)}, 일치 {int(sha(batch) == sha(speed_before))}")
print_comparison("[수정 후]", batch, speed)
print(f"어긋난 창 {n_diff_after}개, 빠진 이벤트 {missing_events_after}건, 최대 평균 차이 {max_mean_gap_after:.2f}")
print("두 계층 집계 종료")

key("n_diff_before", n_diff_before)
key("missing_events_before", missing_events_before)
key("max_mean_gap_before", max_mean_gap_before)
key("sha_batch", sha(batch))
key("sha_speed", sha(speed))
key("sha_equal", int(sha(batch) == sha(speed)))
