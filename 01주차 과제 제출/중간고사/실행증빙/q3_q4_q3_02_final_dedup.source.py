"""
문제 3 (4주). 소비자 장애 뒤에 적재된 행 수
============================================
Kafka 소비자가 민원 이벤트 30건을 읽어 저장소에 적재하다가 도중에 멈췄고, 재시작해서 끝까지 읽었다.
이벤트 ID는 4주차 실습에서 실제 브로커가 남긴 처리 기록(ch4_alo_duplicate_stream.jsonl)의 30개 고유 ID다.
소비자 동작은 4주차 규칙대로 구현한 시뮬레이션이다(브로커를 띄우지 않는다).
학번마다 커밋 주기와 장애가 난 시점이 다르다.

소비자가 따르는 규칙은 둘 중 하나다.
  A. 처리한 뒤 커밋한다  (커밋 주기마다 지금까지 처리한 위치를 커밋)
  B. 읽은 직후 커밋한다  (한 묶음을 읽자마자 커밋하고 그 묶음을 처리)

팀의 보고: "A 규칙으로 운영했다. 적재 행 수가 원천 건수 이상이므로 유실이 없고, 전달 보장은 exactly-once다."

실행: python exam/q3.py --id 학번
수정본은 q3_fixed.py 로 저장해 같은 방식으로 실행한다.
"""

import json

from common import PRACTICE, key, parse_id, pick_choice, pick_int

sid = parse_id()
STREAM = PRACTICE / "chapter4" / "data" / "input" / "ch4_alo_duplicate_stream.jsonl"

ids = []
for line in STREAM.read_text(encoding="utf-8").splitlines():
    event_id = json.loads(line)["event_id"]
    if event_id not in ids:
        ids.append(event_id)
N = len(ids)                                              # 원천 이벤트 수 (30)

COMMIT_EVERY = pick_choice(sid, "q3-commit", [3, 4, 5, 6, 8])
_base = pick_int(sid, "q3-crash", 14, 24) // COMMIT_EVERY * COMMIT_EVERY
CRASH_AT = _base + 2 + pick_int(sid, "q3-rest", 0, COMMIT_EVERY - 3)   # 이 개수만큼 처리한 직후 장애
if CRASH_AT > N - 2:
    CRASH_AT -= COMMIT_EVERY


def run_rule_a():
    """A. 처리한 뒤 커밋. 장애 뒤에는 마지막 커밋 위치부터 다시 읽는다. 적재한 (오프셋, ID) 행을 돌려준다."""
    rows, committed = [], 0
    for off in range(CRASH_AT):                           # 장애 전까지
        rows.append((off, ids[off]))
        if (off + 1) % COMMIT_EVERY == 0:
            committed = off + 1
    for off in range(committed, N):                       # 재시작 뒤
        rows.append((off, ids[off]))
    return rows


def run_rule_b():
    """B. 읽은 직후 커밋. 장애 뒤에는 커밋된 위치부터 읽는다. 적재한 (오프셋, ID) 행을 돌려준다."""
    rows, processed, off, crashed = [], 0, 0, False
    while off < N:
        end = min(off + COMMIT_EVERY, N)
        committed = end                                   # 묶음을 읽자마자 커밋
        for o in range(off, end):
            if not crashed and processed == CRASH_AT:
                crashed = True
                break                                     # 장애: 이 묶음의 나머지는 처리되지 않았다
            rows.append((o, ids[o]))
            processed += 1
        off = committed                                   # 재시작은 커밋된 위치부터
    return rows


rows = run_rule_a()
source_ids = set(ids)
loaded_ids = {event_id for _, event_id in rows}
lost_a = source_ids - loaded_ids
unexpected_a = loaded_ids - source_ids
duplicates = len(rows) - len(loaded_ids)
# event_id를 유일 키로 삼아 처음 적재한 행만 유지한다.
dedup = {}
duplicate_offsets = []
for off, event_id in rows:
    if event_id in dedup:
        duplicate_offsets.append(off)
    else:
        dedup[event_id] = (off, event_id)
rows_after_dedup = len(dedup)
rows_b = run_rule_b()
loaded_ids_b = {event_id for _, event_id in rows_b}
lost_b_ids = source_ids - loaded_ids_b
lost_b_offsets = [off for off, event_id in enumerate(ids) if event_id in lost_b_ids]
# 입력 처리 기록에서 ID와 실제 Kafka 위치의 일대일 대응도 확인한다.
positions_by_id = {}
for line in STREAM.read_text(encoding="utf-8").splitlines():
    record = json.loads(line)
    position = (record["partition"], record["offset"])
    positions_by_id.setdefault(record["event_id"], set()).add(position)
assert all(len(positions) == 1 for positions in positions_by_id.values())
source_position = {event_id: next(iter(positions)) for event_id, positions in positions_by_id.items()}
positions_a = {source_position[event_id] for _, event_id in rows}
assert len(set(source_position.values())) == len(source_ids)
assert set(dedup) == source_ids and not lost_a and not unexpected_a
assert rows_after_dedup == len(loaded_ids) == len(positions_a)
print(f"원천 {N}건, 커밋 주기 {COMMIT_EVERY}, 장애 시점 {CRASH_AT}건 처리 직후")
print(f"A 규칙 적재 행 수 {len(rows)}행")
print(f"ID 대사: 원천 {len(source_ids)}개, 적재 고유 {len(loaded_ids)}개, 유실 {len(lost_a)}건, 미지 ID {len(unexpected_a)}개")
print(f"A 규칙: 중복 {duplicates}행; 처리 후 커밋은 at-least-once이며 exactly-once 전달이 아님")
print(f"A 중복 재처리 위치(시뮬레이션 오프셋): {duplicate_offsets}")
print(f"event_id 중복 제거 후 {rows_after_dedup}행, 입력의 (파티션, 오프셋)으로 제거 후 {len(positions_a)}행")
print(f"B 규칙: 적재 {len(rows_b)}행, 고유 {len(loaded_ids_b)}개, 유실 {len(lost_b_ids)}건")
print(f"B 미처리 위치(시뮬레이션 오프셋): {lost_b_offsets}")
key("commit_every", COMMIT_EVERY)
key("crash_at", CRASH_AT)
key("rows_raw", len(rows))
key("duplicates", duplicates)
key("rows_after_dedup", rows_after_dedup)
key("lost_rule_b", len(lost_b_ids))
