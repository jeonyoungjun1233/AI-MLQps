"""
문제 4 (5주). 늦게 도착한 이벤트는 집계에 들어갔는가
=====================================================
구 단위 민원 이벤트를 시간 창으로 세는 스트리밍 집계다. 이벤트 14건이 파일 3개(batch1~3)로 나뉘어
차례로 도착한다. 자료는 5주차 실습의 실제 입력이다. 이 중 2건(LATE_OK, LATE_DROP)은 발생 시각보다
한참 늦게 도착한다. 학번마다 창 길이와 watermark 지연 허용 시간이 다르다.

적용 규칙(5주차): 파일 하나를 처리할 때 쓰는 watermark는 "그 파일 직전까지 관측한 최대 이벤트 시각 - 지연 허용"이다.
이벤트가 속한 창의 끝이 그 watermark 이하이면 폐기하고, 아니면 집계에 넣는다.

운영 보고: "이벤트 14건이 도착했고 모두 정상 집계되었다."

실행: python exam/q4.py --id 학번
수정본은 q4_fixed.py 로 저장해 같은 방식으로 실행한다.
"""

import json
from collections import defaultdict
from datetime import datetime, timedelta

from common import PRACTICE, key, parse_id, pick_choice

sid = parse_id()
STREAM_DIR = PRACTICE / "chapter5" / "data" / "input" / "stream"
FMT = "%Y-%m-%d %H:%M:%S"
WINDOW_MIN = pick_choice(sid, "q4-window", [5, 10])
DELAY_MIN = pick_choice(sid, "q4-delay", [2, 3, 4, 5, 6, 8, 12, 29, 30, 35])


def load_batches():
    batches = []
    for path in sorted(STREAM_DIR.glob("*.json")):
        rows = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                row = json.loads(line)
                row["t"] = datetime.strptime(row["event_time"], FMT)
                rows.append(row)
        batches.append((path.name, rows))
    return batches


def window_of(t):
    start = t.replace(minute=(t.minute // WINDOW_MIN) * WINDOW_MIN, second=0, microsecond=0)
    return start, start + timedelta(minutes=WINDOW_MIN)


batches = load_batches()
delay = timedelta(minutes=DELAY_MIN)
counts = defaultdict(int)
max_seen = None
dropped = 0
late_events = {}
received = sum(len(rows) for _, rows in batches)

print(f"창 {WINDOW_MIN}분, 지연 허용 {DELAY_MIN}분")
for name, rows in batches:
    # 이 파일에는 직전 파일까지의 최대 시각에서 구한 watermark만 적용한다.
    watermark = None if max_seen is None else max_seen - delay
    batch_accepted = batch_dropped = 0
    for r in rows:
        w_start, w_end = window_of(r["t"])
        is_dropped = watermark is not None and w_end <= watermark
        decision = "폐기" if is_dropped else "수용"
        if is_dropped:
            dropped += 1
            batch_dropped += 1
        else:
            counts[(w_start, r["district"])] += 1
            batch_accepted += 1
        if r["event_id"] in ("LATE_OK", "LATE_DROP"):
            late_events[r["event_id"]] = {
                "file": name, "event_time": r["t"],
                "window_start": w_start, "window_end": w_end,
                "watermark": watermark, "decision": decision,
            }
    batch_max = max(r["t"] for r in rows)
    max_seen = batch_max if max_seen is None else max(max_seen, batch_max)
    watermark_text = "없음" if watermark is None else watermark.strftime("%H:%M")
    print(f"{name}: 도착 {len(rows)}건, 수용 {batch_accepted}건, 폐기 {batch_dropped}건, 적용 watermark {watermark_text}, 폐기 누적 {dropped}")
    print(f"  처리 후 최대 이벤트 시각 {max_seen:%H:%M}, 다음 watermark {max_seen - delay:%H:%M}")

accepted = sum(counts.values())
assert received == accepted + dropped
print(f"집계 완료: 도착 {received}건 = 수용 {accepted}건 + 폐기 {dropped}건, 창-구 {len(counts)}행")
for event_id in ("LATE_OK", "LATE_DROP"):
    trace = late_events[event_id]
    watermark_text = "없음" if trace["watermark"] is None else trace["watermark"].strftime("%H:%M")
    print(f"{event_id}: {trace['file']}, 발생 {trace['event_time']:%H:%M}, 창 {trace['window_start']:%H:%M}-{trace['window_end']:%H:%M}, watermark {watermark_text}, {trace['decision']}")
print("창 시작 | 창 끝 | 구 | 건수")
for (start, district), count in sorted(counts.items()):
    print(f"{start:%H:%M} | {start + timedelta(minutes=WINDOW_MIN):%H:%M} | {district} | {count}")
key("window_min", WINDOW_MIN)
key("delay_min", DELAY_MIN)
key("accepted", accepted)
key("dropped", dropped)
key("n_rows", len(counts))
key("late_ok", late_events["LATE_OK"]["decision"])
key("late_drop", late_events["LATE_DROP"]["decision"])
