"""시험 정의와 입력에서 독립 계산한 뒤 수정본의 실제 @@KEY 출력과 비교한다.

수정본/원본 모듈을 import하지 않는다. 제출 생성기를 실행하거나 답안을 덮어쓰지 않는다.
"""
import argparse
import csv
import hashlib
import json
import os
import platform
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "practice"
EVIDENCE = ROOT / "실행증빙"


def digest(value):
    return hashlib.sha256(value).hexdigest()


def seed(sid, salt):
    return int(digest(f"{sid}|{salt}".encode())[:12], 16)


def choose(sid, salt, values):
    return values[seed(sid, salt) % len(values)]


def integer(sid, salt, low, high):
    return low + seed(sid, salt) % (high - low + 1)


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def lines(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def calculate(sid):
    expected, detail = {}, {}
    items = read_json(DATA / "chapter2/data/input/airquality_seoul_2200.json")["response"]["body"]["items"]
    page_size = integer(sid, "q1-page", 12, 28)
    injected = sorted(range(len(items)), key=lambda i: seed(sid, f"q1-miss:{i}"))[:integer(sid, "q1-nmiss", 2, 6)]
    for index in injected:
        items[index]["khaiValue"] = "-"
    valid = [r for r in items if r["khaiValue"] != "-"]
    total = sum(int(r["khaiValue"]) for r in valid)
    top = min(valid, key=lambda r: (-int(r["khaiValue"]), r["stationName"]))
    expected[1] = dict(total_count=len(items), n_collected=len(items), complete=1,
                       n_missing_khai=len(items)-len(valid), mean_khai=total/len(valid),
                       max_khai_station=top["stationName"])
    first = items[:page_size]
    detail[1] = dict(page_size=page_size, injected_indices=sorted(injected),
                     first_count=len(first), first_missing=sum(r["khaiValue"]=="-" for r in first),
                     first_zero_mean=sum(int(r["khaiValue"]) for r in first if r["khaiValue"]!="-")/len(first),
                     full_zero_mean=total/len(items), full_valid_mean=total/len(valid), sum_valid=total,
                     missing_stations=[r["stationName"] for r in items if r["khaiValue"]=="-"],
                     max_station=top["stationName"], max_value=int(top["khaiValue"]))

    events = []
    for file in ["airquality_seoul_2200.json", "airquality_seoul_current.json"]:
        for row in read_json(DATA / "chapter3/data/input" / file)["response"]["body"]["items"]:
            if row.get("pm10Value") not in (None, "-", ""):
                events.append((row["dataTime"], row["stationName"], int(row["pm10Value"])))
    events.sort()
    period = integer(sid, "q2-period", 4, 7)
    grace = choose(sid, "q2-grace", [5, 8, 10, 12])
    buckets, old_buckets = defaultdict(list), defaultdict(list)
    for index, (time, station, value) in enumerate(events, 1):
        event = datetime.strptime(time, "%Y-%m-%d %H:%M")
        window = event.replace(minute=0, second=0, microsecond=0)
        arrival = event + timedelta(minutes=72 if index % period == 0 else 3)
        label = window.strftime("%Y-%m-%d %H:%M")
        if arrival < window + timedelta(minutes=75):
            buckets[label].append(value)
        if arrival < window + timedelta(minutes=60 + grace):
            old_buckets[label].append(value)
    def aggregate(groups):
        return {k: {"count":len(v), "pm10_mean":round(sum(v)/len(v),2)} for k,v in sorted(groups.items())}
    batch, old = aggregate(buckets), aggregate(old_buckets)
    windows = sorted(set(batch) | set(old))
    fallback = {"count":0, "pm10_mean":0.0}
    sha_batch = digest(json.dumps(batch, sort_keys=True, ensure_ascii=False).encode())[:16]
    sha_old = digest(json.dumps(old, sort_keys=True, ensure_ascii=False).encode())[:16]
    expected[2] = dict(n_diff_before=sum(batch.get(w, fallback)!=old.get(w, fallback) for w in windows),
                       missing_events_before=sum(batch.get(w, fallback)["count"]-old.get(w,fallback)["count"] for w in windows),
                       max_mean_gap_before=max(abs(batch.get(w,fallback)["pm10_mean"]-old.get(w,fallback)["pm10_mean"]) for w in windows),
                       sha_batch=sha_batch, sha_speed=sha_batch, sha_equal=1)
    detail[2] = dict(late_period=period, old_grace=grace, fixed_grace=15, batch=batch, old_speed=old, old_sha=sha_old)

    stream = lines(DATA / "chapter4/data/input/ch4_alo_duplicate_stream.jsonl")
    ids = list(dict.fromkeys(r["event_id"] for r in stream))
    every = choose(sid, "q3-commit", [3,4,5,6,8])
    crash = integer(sid,"q3-crash",14,24)//every*every + 2 + integer(sid,"q3-rest",0,every-3)
    if crash > len(ids)-2:
        crash -= every
    duplicates = crash % every
    lost = min((crash//every+1)*every,len(ids))-crash
    expected[3] = dict(commit_every=every,crash_at=crash,rows_raw=len(ids)+duplicates,
                       duplicates=duplicates,rows_after_dedup=len(ids),lost_rule_b=lost)
    detail[3] = dict(source_ids=len(ids), last_commit_a=crash//every*every,
                     resume_b=min((crash//every+1)*every,len(ids)),
                     duplicate_ids=ids[crash//every*every:crash], lost_ids=ids[crash:crash+lost],
                     source_event_ids=len(set(r["event_id"] for r in stream)),
                     source_partition_offsets=len(set((r["partition"],r["offset"]) for r in stream)))

    window = choose(sid,"q4-window",[5,10])
    delay = choose(sid,"q4-delay",[2,3,4,5,6,8,12,29,30,35])
    past = []
    accepted_rows, dropped_rows, batch_details = [], [], []
    for path in sorted((DATA / "chapter5/data/input/stream").glob("*.json")):
        rows = lines(path)
        watermark = max(past)-timedelta(minutes=delay) if past else None
        decisions = []
        for row in rows:
            time = datetime.fromisoformat(row["event_time"])
            start = time.replace(minute=time.minute//window*window,second=0,microsecond=0)
            end = start+timedelta(minutes=window)
            accepted = watermark is None or end > watermark
            record = dict(id=row["event_id"], district=row["district"], start=start.isoformat(),
                          end=end.isoformat(), accepted=accepted)
            (accepted_rows if accepted else dropped_rows).append(record)
            decisions.append(record)
        past.extend(datetime.fromisoformat(r["event_time"]) for r in rows)
        batch_details.append(dict(file=path.name,watermark=watermark.isoformat() if watermark else None, decisions=decisions))
    decisions = {r["id"]:r["accepted"] for r in accepted_rows+dropped_rows}
    expected[4] = dict(window_min=window,delay_min=delay,accepted=len(accepted_rows),dropped=len(dropped_rows),
                       n_rows=len(set((r["start"],r["district"]) for r in accepted_rows)),
                       late_ok="수용" if decisions["LATE_OK"] else "폐기",late_drop="수용" if decisions["LATE_DROP"] else "폐기")
    detail[4] = batch_details

    cutoff_minutes = 960 + 10*integer(sid,"q5-cutoff",0,21)
    cutoff = f"{cutoff_minutes//60:02}:{cutoff_minutes%60:02}"
    all_records = []
    for path in sorted((DATA / "chapter6/data/input/complaints").glob("*.jsonl")):
        all_records.extend(lines(path))
    records = [r for r in all_records if r["created_at"][11:16] < cutoff]
    mapping = {r["region_std"]:r["lawd_cd"] for r in csv.DictReader((DATA / "chapter6/data/input/lawd_cd_seoul.csv").open(encoding="utf-8"))}
    aliases = {"강남":"강남구","마포":"마포구","관악":"관악구"}
    # 입력 식별자 이름을 명시적으로 확인한다.
    id_key = "complaint_id"
    first_records = {}
    for row in records:
        first_records.setdefault(row[id_key],row)
    by_code, categories = Counter(), Counter()
    classified = []
    for row in first_records.values():
        region = (row.get("region_raw") or "").strip()
        standard = aliases.get(region,region)
        category = "missing" if not standard else "mapped" if standard in mapping else "unmapped"
        categories[category]+=1
        if category == "mapped":
            by_code[mapping[standard]]+=1
        classified.append(dict(id=row[id_key],category=category,raw=row.get("region_raw"),created_at=row["created_at"]))
    raw_groups = Counter(r.get("region_raw") for r in records if r.get("region_raw"))
    dup = len(records)-len(first_records)
    expected[5] = dict(cutoff=cutoff,physical=len(records),dup_removed=dup,mapped=categories["mapped"],
                       missing=categories["missing"],unmapped=categories["unmapped"],
                       preserved=int(len(records)==dup+sum(categories.values())),
                       n_groups_by_name=len(raw_groups),n_groups_by_code=len(by_code),total_reported=sum(by_code.values()))
    detail[5] = dict(raw_groups=dict(raw_groups),by_code=dict(by_code),classified=classified,
                     excluded=[r for r in all_records if r["created_at"][11:16] >= cutoff],
                     duplicate_ids=[key for key,n in Counter(r[id_key] for r in records).items() if n>1])

    features = defaultdict(list)
    for path in sorted((DATA / "chapter7/data/input/ch6_daily").glob("*/daily_summary.json")):
        timestamp = datetime.fromisoformat(path.parent.name+"T00:00:00+00:00")+timedelta(days=1)
        for row in read_json(path)["by_region"]:
            features[row["lawd_cd"]].append((timestamp,int(row["count"])))
    sample_details=[]
    for i in range(12):
        cd=choose(sid,f"q6-cd-{i}",["11440","11620","11680"])
        time=datetime(2026,7,1+integer(sid,f"q6-day-{i}",0,9),9,tzinfo=timezone.utc)
        latest=max(features[cd])
        eligible=[r for r in features[cd] if r[0]<=time]
        selected=max(eligible) if eligible else None
        status="no_value" if selected is None else "ttl" if time-selected[0]>timedelta(days=3) else "joined"
        sample_details.append(dict(index=i,cd=cd,as_of=time.isoformat(),status=status,
                                   known_at=selected[0].isoformat() if selected else None,
                                   age_hours=(time-selected[0]).total_seconds()/3600 if selected else None,
                                   count=selected[1] if selected and status=="joined" else None,
                                   original_count=latest[1],future_leak=latest[0]>time))
    counts=Counter(r["status"] for r in sample_details)
    expected[6]=dict(n_samples=12,n_joined=counts["joined"],n_dropped_no_value=counts["no_value"],
                     n_dropped_ttl=counts["ttl"],n_leaked_future=sum(r["future_leak"] for r in sample_details),
                     sum_count=sum(r["count"] for r in sample_details if r["status"]=="joined"))
    detail[6]=sorted(sample_details,key=lambda r:(r["as_of"],r["cd"],r["index"]))
    return expected,detail


def parse_keys(stdout):
    result={}
    for line in stdout.splitlines():
        if line.startswith("@@KEY "):
            name,value=line[6:].split("=",1)
            assert name not in result, f"duplicate key: {name}"
            result[name]=value
    return result


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--calculate-only",action="store_true")
    ap.add_argument("--id",default="202373020")
    args=ap.parse_args()
    expected,detail=calculate(args.id)
    report={"student_id":args.id,"python":platform.python_version(),"platform":platform.platform(),
            "expected":expected,"detail":detail,"checks":[]}
    manifest=read_json(EVIDENCE/"원본목록.json")
    for entry in manifest["files"]:
        assert digest((ROOT/entry["path"]).read_bytes())==entry["sha256"],entry["path"]
    report["original_files_verified"]=len(manifest["files"])
    if not args.calculate_only:
        env={**os.environ,"PYTHONIOENCODING":"utf-8"}
        for n,reference in expected.items():
            proc=subprocess.run([sys.executable,str(ROOT/"exam"/f"q{n}_fixed.py"),"--id",args.id],
                                cwd=ROOT,capture_output=True,text=True,encoding="utf-8",env=env,timeout=60)
            assert proc.returncode==0,(n,proc.stderr)
            assert not proc.stderr,(n,proc.stderr)
            actual=parse_keys(proc.stdout)
            for name,value in reference.items():
                assert name in actual,(n,"missing",name)
                if isinstance(value,(int,float)):
                    assert abs(float(actual[name])-round(value,4))<0.00001,(n,name,actual[name],value)
                else:
                    assert actual[name]==value,(n,name,actual[name],value)
            report["checks"].append({"question":n,"required_keys_verified":len(reference),"exit_code":0})
            if args.id=="202373020":
                (EVIDENCE/f"최종_q{n}_fixed.stdout.txt").write_text(proc.stdout,encoding="utf-8")
        report["status"]="PASS"
    else:
        report["status"]="CALCULATED_ONLY"
    path=EVIDENCE/("독립계산.json" if args.calculate_only else "독립검증결과.json")
    path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"status":report["status"],"expected":expected},ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
