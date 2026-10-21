"""완성 제출물을 덮어쓰지 않고 원본/수정본 실행·답안 형식·원본 해시를 검증한다."""
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
EVIDENCE = Path(__file__).resolve().parent
ROOT = EVIDENCE.parent
SUBMISSION = ROOT / "exam/submissions/중간고사_202373020_전영준.md"


def load_module(name, filename):
    spec = importlib.util.spec_from_file_location(name, EVIDENCE / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    before_hash = sha(SUBMISSION)
    verifier = load_module("independent_check", "독립검증.py")
    expected, _ = verifier.calculate("202373020")
    answer_builder = load_module("answer_builder", "답안채우기.py")
    assembled, answers = answer_builder.build()
    text = SUBMISSION.read_text(encoding="utf-8")
    assert text == assembled, "생성기 답 칸과 사용자 요청 소감을 반영한 내용과 불일치"
    assert text.startswith("# 중간고사 제출 -- 202373020 전영준\n")
    assert len(re.findall(r"^>> 답:$", text, re.M)) == 28
    assert len(re.findall(r"^```", text, re.M)) == 36, "출력12개+코드6개 fence"
    assert "\ufffd" not in text, "인코딩 대체문자"
    assert not any(word in text for word in ["Traceback (most recent call last)", "[오류 종료 코드", "수정본이 없어"])
    source = json.loads((EVIDENCE / "원본목록.json").read_text(encoding="utf-8"))
    for entry in source["files"]:
        assert sha(ROOT / entry["path"]) == entry["sha256"], entry["path"]
    runs = []
    env = {**os.environ, "PYTHONIOENCODING":"utf-8"}
    for n in range(1, 7):
        segment = text.split(f"## 문제 {n} ", 1)[1].split("### 답안", 1)[0]
        captured = re.findall(r"```text\n(.*?)\n```", segment, re.S)
        embedded = re.findall(r"```python\n(.*?)\n```", segment, re.S)
        assert len(captured)==2 and len(embedded)==1,n
        assert embedded[0] == (ROOT / "exam" / f"q{n}_fixed.py").read_text(encoding="utf-8").rstrip(), n
        original_hash = sha(ROOT / "exam" / f"q{n}.py")[:16]
        assert f"(해시 {original_hash})" in segment,n
        for index, suffix in enumerate(("", "_fixed")):
            script=ROOT / "exam" / f"q{n}{suffix}.py"
            proc=subprocess.run([sys.executable,str(script),"--id","202373020"],cwd=ROOT / "exam",
                                env=env,capture_output=True,text=True,encoding="utf-8",timeout=60)
            assert proc.returncode==0 and not proc.stderr,(script.name,proc.stderr)
            assert proc.stdout.rstrip()==captured[index],f"실제 출력과 제출 파일 불일치 {script.name}"
            if suffix:
                actual=verifier.parse_keys(proc.stdout)
                for name,value in expected[n].items():
                    assert name in actual,(n,name)
                    if isinstance(value,(int,float)):
                        assert abs(float(actual[name])-round(value,4))<0.00001,(n,name)
                    else:
                        assert actual[name]==value,(n,name)
            runs.append({"script":script.name,"exit_code":proc.returncode,"stdout_matches_submission":True,
                         "script_sha256":sha(script),"stdout_sha256":hashlib.sha256(proc.stdout.encode()).hexdigest()})
    assert sha(SUBMISSION)==before_hash,"검증이 제출물을 변경함"
    report={"checked_at_kst":datetime.now(timezone(timedelta(hours=9))).isoformat(),"status":"PASS",
            "student_id":"202373020","name":"전영준","source_commit":source["commit"],
            "original_files_unchanged":len(source["files"]),"answer_fields_filled":len(answers),
            "required_keys_verified":sum(len(v) for v in expected.values()),"runs":runs,
            "submission_sha256":before_hash,"submission_unchanged_by_verification":True,
            "generator_output_and_code_unchanged":True,"reflection_added_by_user_request":True,
            "network_api_calls":0,"lms_submitted":False}
    (EVIDENCE / "최종검증결과.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print("PASS: 원본 35개 불변, 12개 실제 실행 출력 일치, 수정 코드 전문 일치, 필수 KEY 41개, 답 칸 28개.")
    print(f"제출 파일 SHA-256: {before_hash}")


if __name__=="__main__":
    main()
