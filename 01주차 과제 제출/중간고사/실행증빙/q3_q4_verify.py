"""제출 파일을 수정하지 않고 실제 실행값을 독립 산술·입력 자료와 대조한다."""

import hashlib
import json
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EVIDENCE = ROOT / "실행증빙"


def key_values(stage):
    return dict(
        line.removeprefix("@@KEY ").split("=", 1)
        for line in (EVIDENCE / f"q3_q4_{stage}.log").read_text(encoding="utf-8").splitlines()
        if line.startswith("@@KEY ")
    )


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


q3 = key_values("q3_02_final_dedup")
q4 = key_values("q4_02_final_observability")
stream = [json.loads(line) for line in (ROOT / "practice/chapter4/data/input/ch4_alo_duplicate_stream.jsonl").read_text(encoding="utf-8").splitlines()]
source_ids = list(dict.fromkeys(row["event_id"] for row in stream))
n = len(source_ids)
commit, crash = int(q3["commit_every"]), int(q3["crash_at"])
last_committed = crash // commit * commit
expected_duplicate_count = crash - last_committed
next_committed = min(((crash + commit - 1) // commit) * commit, n)
expected_lost_b = next_committed - crash
assert int(q3["rows_raw"]) == n + expected_duplicate_count
assert int(q3["duplicates"]) == expected_duplicate_count
assert int(q3["rows_after_dedup"]) == n
assert int(q3["lost_rule_b"]) == expected_lost_b
ids_to_positions = {}
for row in stream:
    ids_to_positions.setdefault(row["event_id"], set()).add((row["partition"], row["offset"]))
assert all(len(v) == 1 for v in ids_to_positions.values())
assert len({next(iter(v)) for v in ids_to_positions.values()}) == n

# 14개 이벤트를 독립적으로 펼친 뒤, 앞 파일에 속하는 이벤트들만 조회해 심사선을 구한다.
flat = []
for batch_index, path in enumerate(sorted((ROOT / "practice/chapter5/data/input/stream").glob("*.json"))):
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            row["batch_index"] = batch_index
            row["file"] = path.name
            row["t"] = datetime.fromisoformat(row["event_time"])
            flat.append(row)
window, delay = int(q4["window_min"]), int(q4["delay_min"])
decisions, groups = [], Counter()
for row in flat:
    midnight = row["t"].replace(hour=0, minute=0, second=0, microsecond=0)
    bucket = int((row["t"] - midnight).total_seconds()) // (window * 60)
    start = midnight + timedelta(minutes=bucket * window)
    end = start + timedelta(minutes=window)
    preceding_times = [r["t"] for r in flat if r["batch_index"] < row["batch_index"]]
    wm = max(preceding_times) - timedelta(minutes=delay) if preceding_times else None
    accepted = wm is None or end > wm
    if accepted:
        groups[(start.isoformat(), row["district"])] += 1
    decisions.append({
        "event_id": row["event_id"], "file": row["file"],
        "event_time": row["t"].isoformat(), "window_end": end.isoformat(),
        "watermark": wm.isoformat() if wm else None,
        "decision": "수용" if accepted else "폐기",
    })
assert int(q4["accepted"]) == sum(groups.values())
assert int(q4["dropped"]) == sum(d["decision"] == "폐기" for d in decisions)
assert len(flat) == int(q4["accepted"]) + int(q4["dropped"])
assert int(q4["n_rows"]) == len(groups)
for event_id, key in [("LATE_OK", "late_ok"), ("LATE_DROP", "late_drop")]:
    assert q4[key] == next(d["decision"] for d in decisions if d["event_id"] == event_id)
for number in (3, 4):
    assert digest(ROOT / "exam" / f"q{number}.py") == digest(EVIDENCE / f"q3_q4_q{number}_00_original.source.py")
for stage in ("q3_00_original", "q3_01_id_validation", "q3_02_final_dedup", "q4_00_original", "q4_01_watermark", "q4_02_final_observability"):
    metadata = json.loads((EVIDENCE / f"q3_q4_{stage}.json").read_text(encoding="utf-8"))
    assert metadata["exit_code"] == 0
    assert metadata["source_sha256"] == digest(EVIDENCE / f"q3_q4_{stage}.source.py")
    assert metadata["stdout_sha256"] == digest(EVIDENCE / f"q3_q4_{stage}.log")

report = {
    "verified_at_kst": datetime.now(timezone(timedelta(hours=9))).isoformat(),
    "status": "PASS", "student_id": "202373020",
    "q3": {
        "keys": q3, "source_physical_rows": len(stream), "source_unique_events": n,
        "source_unique_kafka_positions": len({next(iter(v)) for v in ids_to_positions.values()}),
        "last_commit_a": last_committed, "next_commit_b": next_committed,
        "independent_duplicates": expected_duplicate_count, "independent_b_loss": expected_lost_b,
    },
    "q4": {"keys": q4, "event_decisions": decisions, "window_district_counts": [
        {"start": start, "district": district, "count": count}
        for (start, district), count in sorted(groups.items())
    ]},
    "originals_unchanged": True, "all_six_execution_logs_verified": True,
}
(EVIDENCE / "q3_q4_verification.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("PASS: Q3 commit arithmetic / Q4 independent per-event decisions / six logs / original hashes")
