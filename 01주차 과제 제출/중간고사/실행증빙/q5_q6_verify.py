"""수정본과 독립적인 SQLite 질의로 문제 5/6을 대사한다. 제출 도구는 실행하지 않는다."""
from pathlib import Path
import csv
from datetime import datetime, timedelta, timezone
import hashlib
import json
import sqlite3
import subprocess
import sys

BASE = Path(__file__).resolve().parent.parent
E = BASE / "실행증빙"
SID = "202373020"
def sid_hash(salt):
    return int(hashlib.sha256(f"{SID}|{salt}".encode()).hexdigest()[:12], 16)

def execute_keys(n):
    result = subprocess.run([sys.executable, str(BASE / "exam" / f"q{n}_fixed.py"), "--id", SID],
                            cwd=BASE, capture_output=True, encoding="utf-8", check=True)
    expected_log = (E / f"q5_q6_q{n}_final.log").read_text(encoding="utf-8")
    assert result.stdout == expected_log, f"q{n} 재실행 stdout 불일치"
    return dict(line[6:].split("=", 1) for line in result.stdout.splitlines() if line.startswith("@@KEY "))

db = sqlite3.connect(":memory:")
db.row_factory = sqlite3.Row
db.execute("CREATE TABLE complaints(seq INTEGER, cid TEXT, day TEXT, region_raw TEXT, at TEXT, within_cutoff INTEGER)")
db.execute("CREATE TABLE mapping(name TEXT, cd TEXT)")
input_dir = BASE / "practice/chapter6/data/input"
cutoff_minutes = 16 * 60 + 10 * (sid_hash("q5-cutoff") % 22)
cutoff = f"{cutoff_minutes // 60:02d}:{cutoff_minutes % 60:02d}"
all_records = []
for file in sorted((input_dir / "complaints").glob("*.jsonl")):
    all_records += [json.loads(line) for line in file.read_text(encoding="utf-8").splitlines() if line.strip()]
for seq, r in enumerate(all_records):
    dt = datetime.fromisoformat(r["created_at"])
    in_scope = dt.hour * 60 + dt.minute < cutoff_minutes
    db.execute("INSERT INTO complaints VALUES(?,?,?,?,?,?)",
               (seq, r["complaint_id"], dt.date().isoformat(), r.get("region_raw"), r["created_at"], int(in_scope)))
with (input_dir / "lawd_cd_seoul.csv").open(encoding="utf-8", newline="") as f:
    for r in csv.DictReader(f):
        db.execute("INSERT INTO mapping VALUES(?,?)", (r["region_std"], r["lawd_cd"]))
db.executescript("""
CREATE VIEW classified AS
WITH scoped AS (
 SELECT *, ROW_NUMBER() OVER (PARTITION BY cid ORDER BY seq) AS nth FROM complaints WHERE within_cutoff=1
), normalized AS (
 SELECT *, CASE trim(coalesce(region_raw,'')) WHEN '강남' THEN '강남구' WHEN '마포' THEN '마포구'
   WHEN '관악' THEN '관악구' ELSE trim(coalesce(region_raw,'')) END AS normalized_name FROM scoped
)
SELECT normalized.*, mapping.cd, CASE WHEN nth>1 THEN 'dup_removed' WHEN normalized_name='' THEN 'missing'
 WHEN cd IS NULL THEN 'unmapped' ELSE 'mapped' END AS outcome
FROM normalized LEFT JOIN mapping ON normalized.normalized_name=mapping.name;
""")
outcomes = dict(db.execute("SELECT outcome,COUNT(*) FROM classified GROUP BY outcome"))
for name in ("mapped", "missing", "unmapped", "dup_removed"):
    outcomes.setdefault(name, 0)
physical = db.execute("SELECT COUNT(*) FROM classified").fetchone()[0]
groups = [dict(r) for r in db.execute("SELECT cd,COUNT(*) AS n FROM classified WHERE outcome='mapped' GROUP BY cd ORDER BY cd")]
raw_groups = db.execute("SELECT COUNT(DISTINCT region_raw) FROM classified WHERE coalesce(region_raw,'')<>''").fetchone()[0]
q5_expected = {"cutoff": cutoff, "physical": physical, **outcomes,
               "preserved": int(physical == sum(outcomes.values())), "n_groups_by_name": raw_groups,
               "n_groups_by_code": len(groups), "total_reported": sum(r["n"] for r in groups)}
q5_keys = execute_keys(5)
assert q5_keys == {k: str(v) for k, v in q5_expected.items()}
q5_daily = [dict(r) for r in db.execute("SELECT day,outcome,COUNT(*) AS n FROM classified GROUP BY day,outcome ORDER BY day,outcome")]
excluded = [dict(r) for r in db.execute("SELECT cid,region_raw,at FROM complaints WHERE within_cutoff=0 ORDER BY seq")]
duplicates = [dict(r) for r in db.execute("SELECT cid,at,nth,outcome FROM classified WHERE cid IN (SELECT cid FROM classified WHERE outcome='dup_removed') ORDER BY seq")]
full_view = db.execute("SELECT sql FROM sqlite_master WHERE name='classified'").fetchone()[0]
db.execute(full_view.replace("CREATE VIEW classified", "CREATE VIEW full_classified").replace("WHERE within_cutoff=1", ""))
full_day_outcomes = dict(db.execute("SELECT outcome,COUNT(*) FROM full_classified GROUP BY outcome"))

db.execute("CREATE TABLE features(cd TEXT,covers TEXT,known_at TEXT,epoch INTEGER,n INTEGER)")
for file in sorted((BASE / "practice/chapter7/data/input/ch6_daily").glob("*/daily_summary.json")):
    known = datetime.fromisoformat(file.parent.name + "T00:00:00+00:00") + timedelta(days=1)
    for r in json.loads(file.read_text(encoding="utf-8"))["by_region"]:
        db.execute("INSERT INTO features VALUES(?,?,?,?,?)",
                   (r["lawd_cd"],file.parent.name,known.isoformat(),int(known.timestamp()),int(r["count"])))
db.execute("CREATE TABLE samples(sample_id INTEGER,cd TEXT,as_of TEXT,epoch INTEGER)")
cds = ["11440","11620","11680"]
for i in range(12):
    cd = cds[sid_hash(f"q6-cd-{i}") % len(cds)]
    dt = datetime(2026,7,1 + sid_hash(f"q6-day-{i}") % 10,9,0,tzinfo=timezone.utc)
    db.execute("INSERT INTO samples VALUES(?,?,?,?)", (i,cd,dt.isoformat(),int(dt.timestamp())))
sql = """
SELECT s.*, f.covers, f.known_at, (s.epoch-f.epoch)/3600.0 AS age_hours, f.n,
 CASE WHEN f.epoch IS NULL THEN 'no_value' WHEN s.epoch-f.epoch>259200 THEN 'ttl' ELSE 'joined' END AS outcome,
 CASE WHEN (SELECT MAX(epoch) FROM features WHERE cd=s.cd)>s.epoch THEN 1 ELSE 0 END AS original_future
FROM samples s LEFT JOIN features f ON f.cd=s.cd AND f.epoch=(SELECT MAX(epoch) FROM features WHERE cd=s.cd AND epoch<=s.epoch)
ORDER BY s.epoch,s.cd,s.sample_id
"""
q6_samples = [dict(r) for r in db.execute(sql)]
q6_expected = {
    "n_samples": len(q6_samples), "n_joined": sum(r["outcome"]=="joined" for r in q6_samples),
    "n_dropped_no_value": sum(r["outcome"]=="no_value" for r in q6_samples),
    "n_dropped_ttl": sum(r["outcome"]=="ttl" for r in q6_samples),
    "n_leaked_future": sum(r["original_future"] for r in q6_samples),
    "sum_count": sum(r["n"] for r in q6_samples if r["outcome"]=="joined"),
}
q6_keys = execute_keys(6)
assert q6_keys == {k:str(v) for k,v in q6_expected.items()}
assert len(q6_samples) == sum(q6_expected[k] for k in ("n_joined","n_dropped_no_value","n_dropped_ttl"))
manifest = json.loads((E / "원본목록.json").read_text(encoding="utf-8"))
checked_files = []
for entry in manifest["files"]:
    p = entry["path"]
    if p in {"exam/q5.py","exam/q6.py","exam/common.py","exam/submit_exam.py"} or p.startswith(("practice/chapter6/","practice/chapter7/")):
        digest = hashlib.sha256((BASE/p).read_bytes()).hexdigest()
        assert digest == entry["sha256"], f"원본 변경: {p}"
        checked_files.append(p)
report = {"student_id": SID, "status": "PASS", "method": "수정본 재실행 stdout 일치 및 독립 SQLite 집계/시점조인 교차검증",
          "q5": {"keys":q5_expected,"groups":groups,"daily":q5_daily,"excluded_by_cutoff":excluded,"duplicate_detail":duplicates,
                 "full_day_outcomes":full_day_outcomes},
          "q6":{"keys":q6_expected,"sample_rows":q6_samples}, "unchanged_original_files": checked_files}
(E / "q5_q6_독립검증.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
sys.stdout.reconfigure(encoding="utf-8")
print(json.dumps(report,ensure_ascii=False,indent=2))
