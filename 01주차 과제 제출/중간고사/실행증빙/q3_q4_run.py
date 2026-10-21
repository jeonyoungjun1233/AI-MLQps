"""문제 3/4의 원본, 단계별 수정본 실행을 UTF-8 증빙으로 저장한다."""

import argparse
import hashlib
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
parser = argparse.ArgumentParser()
parser.add_argument("script", choices=["q3.py", "q4.py", "q3_fixed.py", "q4_fixed.py"])
parser.add_argument("stage")
args = parser.parse_args()
source = ROOT / "exam" / args.script
started = datetime.now(timezone(timedelta(hours=9))).isoformat()
result = subprocess.run(
    [sys.executable, str(source), "--id", "202373020"],
    cwd=ROOT, capture_output=True, encoding="utf-8", check=False,
)
stem = ROOT / "실행증빙" / ("q3_q4_" + args.stage)
stem.with_suffix(".log").write_bytes(result.stdout.encode("utf-8"))
stem.with_suffix(".stderr.log").write_bytes(result.stderr.encode("utf-8"))
stem.with_suffix(".source.py").write_bytes(source.read_bytes())
metadata = {
    "started_at_kst": started,
    "python": sys.version,
    "command": [sys.executable, str(source), "--id", "202373020"],
    "execution_kind": "provided-input simulation; no Kafka/Spark service or external API request",
    "stage": args.stage,
    "exit_code": result.returncode,
    "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
    "stdout_sha256": hashlib.sha256(result.stdout.encode("utf-8")).hexdigest(),
}
stem.with_suffix(".json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
sys.stdout.reconfigure(encoding="utf-8")
print(result.stdout, end="")
if result.stderr:
    print(result.stderr, file=sys.stderr, end="")
sys.exit(result.returncode)
