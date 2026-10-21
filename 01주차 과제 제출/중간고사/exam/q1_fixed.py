"""
문제 1 (1주 + 2주). 공공 API 대기질 수집
=========================================
서울 대기질 API(측정소 40곳)에서 통합대기환경지수(khaiValue)를 모아 평균과 최고 측정소를 보고한다.
자료는 2주차 실습의 실제 응답(airquality_seoul_2200.json)이다. 시험용으로 두 가지를 학번에 따라 바꿨다.
  - 한 페이지에 담기는 건수(numOfRows)가 학번마다 다르다 (응답이 여러 페이지로 나뉜다)
  - 학번마다 몇 곳의 khaiValue를 측정 실패('-')로 바꿨다 (원자료에도 '-'가 1곳 있다)

보고서의 문장: "응답 코드가 정상이고 수집이 완료되었다. 통합대기환경지수 평균은 ○○이다."

실행: python exam/q1.py --id 학번
수정본은 q1_fixed.py 로 저장해 같은 방식으로 실행한다.
"""

import json

from common import PRACTICE, key, parse_id, pick_int, pick_subset

sid = parse_id()
SRC = PRACTICE / "chapter2" / "data" / "input" / "airquality_seoul_2200.json"
ITEMS = json.loads(SRC.read_text(encoding="utf-8"))["response"]["body"]["items"]

PAGE_SIZE = pick_int(sid, "q1-page", 12, 28)
for i in pick_subset(sid, "q1-miss", len(ITEMS), pick_int(sid, "q1-nmiss", 2, 6)):
    ITEMS[i]["khaiValue"] = "-"


def fetch_page(page_no: int) -> dict:
    """API 한 페이지를 돌려준다. 실제 API와 같은 header/body 두 계층이다."""
    start = (page_no - 1) * PAGE_SIZE
    return {
        "header": {"resultCode": "00", "resultMsg": "NORMAL_CODE"},
        "body": {
            "totalCount": len(ITEMS), "pageNo": page_no, "numOfRows": PAGE_SIZE,
            "items": ITEMS[start:start + PAGE_SIZE],
        },
    }


resp = fetch_page(1)
header, body = resp["header"], resp["body"]
if header["resultCode"] != "00":
    raise SystemExit(f"API 오류: {header['resultMsg']}")

rows = list(body["items"])
total_count = body["totalCount"]
page_no = 1
while len(rows) < total_count:
    page_no += 1
    resp = fetch_page(page_no)
    page_header, page_body = resp["header"], resp["body"]
    if page_header["resultCode"] != "00":
        raise SystemExit(f"API 오류: {page_header['resultMsg']}")
    if page_body["totalCount"] != total_count:
        raise SystemExit("수집 중 전체 건수가 바뀌었습니다")
    if not page_body["items"]:
        raise SystemExit("전체 건수에 도달하기 전에 빈 페이지를 받았습니다")
    rows.extend(page_body["items"])
complete = len(rows) == total_count
if not complete:
    raise SystemExit(f"수집 건수 불일치: {len(rows)} / {total_count}")
valid_rows = [r for r in rows if r.get("khaiValue") not in (None, "", "-")]
n_missing = len(rows) - len(valid_rows)
values = [int(r["khaiValue"]) for r in valid_rows]
if not values:
    raise SystemExit("유효한 통합대기환경지수가 없습니다")
mean = sum(values) / len(values)
zero_filled_mean = sum(values) / len(rows)
top = sorted(valid_rows, key=lambda r: (-int(r["khaiValue"]), r["stationName"]))[0]

print(f"응답 코드 {header['resultCode']} ({header['resultMsg']})")
print(f"페이지 크기 {PAGE_SIZE}건, 요청 페이지 {page_no}개")
print(f"수집 {len(rows)}건 / 전체 {total_count}건 -- 수집 완료")
print(f"결측 {n_missing}건, 유효값 {len(values)}건, 유효값 합계 {sum(values)}")
print(f"결측을 0으로 채운 평균 {zero_filled_mean:.4f}, 유효값 평균 {mean:.4f}, 차이 {mean - zero_filled_mean:.4f}")
print(f"통합대기환경지수 평균 {mean:.2f}, 최고 {top['stationName']} ({top['khaiValue']})")
key("total_count", body["totalCount"])
key("n_collected", len(rows))
key("complete", int(complete))
key("n_missing_khai", n_missing)
key("mean_khai", float(mean))
key("max_khai_station", top["stationName"])
