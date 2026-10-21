"""문제 5/6의 실제 실행 stdout, stderr, 종료 코드와 실행 코드 해시를 기록한다."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone, timedelta

BASE = Path(__file__).resolve().parent.parent
EVIDENCE = BASE / "실행증빙"
filename, label = sys.argv[1:3]
if filename not in {"q5.py", "q5_fixed.py", "q6.py", "q6_fixed.py"}:
    raise ValueError(filename)
path = BASE / "exam" / filename
cmd = [sys.executable, str(path), "--id", "202373020"]
result = subprocess.run(cmd, cwd=BASE, capture_output=True, encoding="utf-8")
stem = f"q5_q6_{label}"
(EVIDENCE / f"{stem}.log").write_text(result.stdout, encoding="utf-8")
(EVIDENCE / f"{stem}.stderr.log").write_text(result.stderr, encoding="utf-8")
(EVIDENCE / f"{stem}.source.txt").write_bytes(path.read_bytes())
metadata = {
    "student_id": "202373020", "command": cmd, "cwd": str(BASE),
    "executed_at_kst": datetime.now(timezone(timedelta(hours=9))).isoformat(),
    "python": sys.version, "returncode": result.returncode,
    "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    "stdout_sha256": hashlib.sha256(result.stdout.encode("utf-8")).hexdigest(),
    "input_kind": "교수자 제공 파일의 학번별 재계산; 외부 API/브로커/Feast 실행 없음",
}
(EVIDENCE / f"{stem}.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
sys.stdout.reconfigure(encoding="utf-8")
print(result.stdout, end="")
print(f"[실행 기록] {stem}, returncode={result.returncode}")
if result.stderr:
    print(result.stderr, file=sys.stderr)
raise SystemExit(result.returncode)
