"""보관한 생성기 출력의 답 칸만 채운다. 원본 제출 생성기를 다시 실행하지 않는다."""
import json
from pathlib import Path

EVIDENCE = Path(__file__).resolve().parent
ROOT = EVIDENCE.parent
ORDER = [f"{n}-{j}" for n in range(1, 7) for j in range(1, 5)] + ["S-1", "S-2", "S-3", "AI"]


def build():
    answers = {}
    for name in ("답안_q1_q2.json", "답안_q3_q4.json", "답안_q5_q6.json", "답안_종합.json"):
        chunk = json.loads((EVIDENCE / name).read_text(encoding="utf-8"))
        assert not set(answers) & set(chunk), "중복 답안"
        answers.update(chunk)
    assert set(answers) == set(ORDER), "답안 문항 누락 또는 추가"
    template = (EVIDENCE / "제출생성기_원문.md.txt").read_text(encoding="utf-8")
    parts = template.split(">> 답:\n")
    assert len(parts) == len(ORDER) + 1
    output = parts[0]
    for code, rest in zip(ORDER, parts[1:]):
        answer = answers[code].strip()
        assert len(answer) > 40, code
        output += ">> 답:\n\n" + answer + "\n" + rest
    return output, answers


if __name__ == "__main__":
    output, answers = build()
    target = ROOT / "exam/submissions/중간고사_202373020.md"
    target.write_text(output, encoding="utf-8")
    print(f"Filled {len(answers)} answer fields; generator output/code preserved.")
