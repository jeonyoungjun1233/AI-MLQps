"""문제 1·2 원본 실행과 독립 집계로 수정본을 대조한다. 제출 파일을 만들지 않는다."""

import ast
import contextlib
import hashlib
import io
import json
import runpy
import sys
from datetime import timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXAM = ROOT / "exam"
sys.path.insert(0, str(EXAM))
sys.stdout.reconfigure(encoding="utf-8")
STUDENT_ID = "202373020"


def execute(name):
    sys.argv = [name, "--id", STUDENT_ID]
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        values = runpy.run_path(str(EXAM / name))
    keys = dict(line[6:].split("=", 1) for line in output.getvalue().splitlines() if line.startswith("@@KEY "))
    return values, keys, output.getvalue()


original1, before1, output1 = execute("q1.py")
fixed1, after1, fixed_output1 = execute("q1_fixed.py")
all_rows = original1["ITEMS"]
valid_rows = [row for row in all_rows if row.get("khaiValue") not in (None, "", "-")]
numbers = [int(row["khaiValue"]) for row in valid_rows]
maximum = max(numbers)
top_tied = sorted(row["stationName"] for row in valid_rows if int(row["khaiValue"]) == maximum)
first_page = original1["rows"]
first_values = [int(row["khaiValue"]) for row in first_page if row.get("khaiValue") not in (None, "", "-")]
expected1 = {
    "total_count": len(all_rows),
    "n_collected": len(all_rows),
    "complete": 1,
    "n_missing_khai": len(all_rows) - len(numbers),
    "mean_khai": round(sum(numbers) / len(numbers), 4),
    "max_khai_station": top_tied[0],
}
assert after1 == {k: str(v) for k, v in expected1.items()}, (after1, expected1)
assert fixed1["rows"] == all_rows
assert len({(r["stationName"], r["dataTime"]) for r in fixed1["rows"]}) == len(all_rows)
assert original1["PAGE_SIZE"] == fixed1["PAGE_SIZE"]

original2, before2, output2 = execute("q2.py")
fixed2, after2, fixed_output2 = execute("q2_fixed.py")
events = original2["events"]


def independent_reference(grace):
    result = {}
    for window in sorted({row["event_time"].replace(minute=0, second=0, microsecond=0) for row in events}):
        deadline = window + timedelta(hours=1, minutes=grace)
        accepted = [row["pm10"] for row in events if window <= row["event_time"] < window + timedelta(hours=1) and row["arrival_time"] < deadline]
        if accepted:
            result[window.strftime("%Y-%m-%d %H:%M")] = {"count": len(accepted), "pm10_mean": round(sum(accepted) / len(accepted), 2)}
    return result


reference_batch = independent_reference(original2["GRACE_BATCH"])
reference_before_speed = independent_reference(original2["GRACE_SPEED"])
assert original2["batch"] == reference_batch == fixed2["batch"] == fixed2["speed"]
assert original2["speed"] == reference_before_speed == fixed2["speed_before"]
windows = sorted(set(reference_batch) | set(reference_before_speed))
expected_diff = sum(reference_batch[w] != reference_before_speed[w] for w in windows)
expected_missing = sum(reference_batch[w]["count"] - reference_before_speed[w]["count"] for w in windows)
expected_gap = max(abs(reference_batch[w]["pm10_mean"] - reference_before_speed[w]["pm10_mean"]) for w in windows)
expected_hash = hashlib.sha256(json.dumps(reference_batch, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()[:16]
expected2 = {"n_diff_before": expected_diff, "missing_events_before": expected_missing, "max_mean_gap_before": round(expected_gap, 4), "sha_batch": expected_hash, "sha_speed": expected_hash, "sha_equal": 1}
assert after2 == {k: str(v) for k, v in expected2.items()}, (after2, expected2)


def sha_ast(name):
    return ast.dump(next(node for node in ast.parse((EXAM / name).read_text(encoding="utf-8")).body if isinstance(node, ast.FunctionDef) and node.name == "sha"))


assert sha_ast("q2.py") == sha_ast("q2_fixed.py")
report = {
    "student_id": STUDENT_ID,
    "verification": "PASS",
    "execution_mode": "교수자 저장 응답의 로컬 재계산; 실시간 API/Kafka 호출 없음",
    "q1": {
        "page_size": original1["PAGE_SIZE"],
        "first_page": {"n": len(first_page), "n_missing": len(first_page)-len(first_values), "n_valid": len(first_values), "sum": sum(first_values), "mean_zero_filled": sum(first_values)/len(first_page), "mean_valid_only": sum(first_values)/len(first_values)},
        "full_input": {"n": len(all_rows), "n_missing": len(all_rows)-len(numbers), "n_valid": len(numbers), "sum": sum(numbers), "mean_zero_filled": sum(numbers)/len(all_rows), "mean_valid_only": sum(numbers)/len(numbers), "mean_gap": sum(numbers)/len(numbers)-sum(numbers)/len(all_rows), "min_valid": min(numbers), "max_valid": maximum, "missing_stations": [row["stationName"] for row in all_rows if row.get("khaiValue") in (None, "", "-")], "top_tied": top_tied},
        "keys": expected1,
    },
    "q2": {"n_events": len(events), "window_min": original2["WINDOW_MIN"], "late_period": original2["LATE_PERIOD"], "grace_batch": original2["GRACE_BATCH"], "grace_speed_before": original2["GRACE_SPEED"], "batch": reference_batch, "speed_before": reference_before_speed, "speed_after": fixed2["speed"], "keys": expected2, "sha_function_unchanged": True},
    "checks": ["원본과 같은 학번", "q1 전체 건수/결측/유효 평균/최대 동점 정렬", "q1 측정소-시각 키 유일성", "q2 원본 스피드 결과 재현", "q2 창별 원자료 조건식 독립 재계산", "q2 필수 키 6개", "q2 sha 함수 AST 불변"],
    "code_sha256": {name: hashlib.sha256((EXAM/name).read_bytes()).hexdigest() for name in ["q1.py", "q2.py", "q1_fixed.py", "q2_fixed.py", "common.py"]},
}
(ROOT / "실행증빙" / "q1_q2_verification.json").write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
print(json.dumps(report, ensure_ascii=False, indent=2))
