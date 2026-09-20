"""교수자 원본 코드를 별도 경로에서 재실행하고 제출 JSON의 정적 값과 비교한다."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
CH = ROOT / 'practice/chapter3'
EV = ROOT / '실행증빙'
RUN = EV / '재실행결과/practice/chapter3'

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    original = CH / 'data/output/ch3_compose_plan.json'
    before = digest(original)
    proof = json.loads((EV / '검증결과.json').read_text(encoding='utf-8'))
    for name, expected in proof['SHA256'].items():
        if digest(ROOT / name) != expected:
            raise RuntimeError(f'보관 파일 해시 불일치: {name}')
    for name in ['docker-compose.yml', 'code/3-1-compose-plan.py', 'code/requirements.txt']:
        target = RUN / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(CH / name, target)
    proc = subprocess.run([sys.executable, 'code/3-1-compose-plan.py'], cwd=RUN,
        env={**os.environ, 'PYTHONIOENCODING': 'utf-8'}, capture_output=True, text=True, encoding='utf-8')
    (EV / '재실행결과/실행로그.txt').write_text(
        f'명령: {sys.executable} code/3-1-compose-plan.py\n작업 폴더: {RUN}\n종료 코드: {proc.returncode}\n{proc.stdout}{proc.stderr}', encoding='utf-8')
    if proc.returncode:
        print(proc.stderr)
        return proc.returncode
    old = json.loads(original.read_text(encoding='utf-8'))
    new = json.loads((RUN / 'data/output/ch3_compose_plan.json').read_text(encoding='utf-8'))
    same = {k: old[k] == new[k] for k in ['services', 'host_ports', 'security_checks']}
    result = {'결과': 'PASS' if all(same.values()) and digest(original) == before else 'FAIL',
              '정적값일치': same, '제출_JSON_변경없음': digest(original) == before,
              '제출_JSON_SHA256': before, '재실행_compose_path': new['compose_path'],
              '재실행_generated_at': new['generated_at'],
              '설명': '별도 경로에서 새로 실행했으므로 compose_path와 generated_at은 비교 대상에서 제외함'}
    (EV / '재실행결과/검증결과.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['결과'] == 'PASS' else 1

if __name__ == '__main__':
    raise SystemExit(main())
