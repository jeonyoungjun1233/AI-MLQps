# 02주차 과제 제출

202373020 전영준 · AI 데이터개발과 MLOps

## LMS에 제출할 것

1. [ch2_eda_summary.json](practice/chapter2/data/output/ch2_eda_summary.json)을 그대로 첨부한다.
2. [ch2_drift_result.json](practice/chapter2/data/output/ch2_drift_result.json)을 그대로 첨부한다.
3. [02주차_서술형_답안.txt](02주차_서술형_답안.txt)의 두 답안을 본문에 입력한다. 각각 2문장·3문장이다.

두 JSON은 교수자 원본 실습 코드의 생성 결과를 수정 없이 보관했다. 제출 기한은 수업일 포함 7일 이내이며, LMS의 실제 마감 확인과 업로드는 아직 하지 않았다. GitHub 푸시는 LMS 제출을 대신하지 않는다.

## 실제 API를 활용한 최종 결과

2026-09-13 22:24 KST에 사용자가 제공한 키로 에어코리아 API를 호출했다. HTTP 200, `resultCode=00`, 서울 측정소 40개 응답을 받았으며 전체 조회 건수도 40개로 누락이 없었다. 응답 본문은 [airquality_seoul_live.json](practice/chapter2/data/input/airquality_seoul_live.json)에 그대로 저장했다.

| 항목 | 결과 |
|---|---|
| EDA 입력 | 이번 실시간 호출로 수집한 실제 응답 |
| 기준 입력 | 교수자 제공 2026-06-28 22:00 KST 스냅샷 |
| 현재 입력 | 실시간 응답의 2026-09-13 22:00 KST 측정값 |
| 두 이벤트 시각의 간격 | 77일 |
| 기준/현재 PM10 표본 수 | 40 / 40 |
| PM10 평균 | 20.025 → 42.35 ㎍/㎥ |
| 현재 PM10 최소/최대/중앙값 | 34 / 50 / 42 ㎍/㎥ |
| 현재 PM2.5 평균 | 27.45 ㎍/㎥ |
| 현재 측정값 결측 | 6개 측정 필드 모두 0개 |
| 현재 PM10 등급 | 2등급 40개, 결측 0개 |
| KS 통계량 | 1.0 |
| p_value | 1.860340365603627e-23 |
| alpha | 0.05 |
| drift_detected | true |

판정 규칙은 `p_value < alpha`이다. 이번 p_value는 0.05보다 작으므로 true이며, 해당 검정에서 두 시점의 PM10 분포가 같다는 귀무가설을 기각한다. 과제 2번은 false의 잘못된 해석을 설명하는 문항이므로, 이번 실제 결과를 false라고 바꾸지 않고 false인 경우의 해석을 가정하여 답했다.

이번 비교는 77일 간격이다. 강의 예시의 한 시간 간격 비교와 구분하며, 검정 결과만으로 변화의 원인이 장애·계절성·정책 중 무엇인지 확정하지 않는다. 예전 스냅샷끼리의 p_value=0.5786, false 결과는 이전 실행 기록이며 최종 제출값은 위의 true이다.

## 실행 증빙과 재현

[API 호출 확인](실행증빙/API_호출확인.json) · [EDA 로그](실행증빙/2-1-parse-api.log) · [KS 로그](실행증빙/2-2-drift-visualize.log) · [분포·분위수 비교](practice/chapter2/data/output/ch2_drift_visual.txt) · [검증 결과](실행증빙/검증결과.json) · [교수자 원본 해시](실행증빙/교수자_원본_해시.json)

실시간 **수집**과 저장 응답의 **재계산**을 구분했다. 제출 JSON의 `source=file:airquality_seoul_live.json`은 이번 API 응답을 저장한 후 원본 실습 코드로 읽었다는 뜻이다. 수집 시각·HTTP/API 상태·원본 응답 SHA-256은 호출 증빙에, 측정 시각은 응답 `dataTime`과 제출 JSON에 기록했다.

저장소 루트에서 Python 3.10 이상으로 실행한다.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r "01주차 과제 제출/02주차/practice/chapter2/code/requirements.txt"
.\.venv\Scripts\python.exe "01주차 과제 제출/02주차/실행증빙/재실행.py"
```

[실행설정.json](실행증빙/실행설정.json)에 최종 실시간 응답 파일을 지정했으므로 위 명령은 최종 제출물을 재현한다. 설치 이후 재계산에는 키나 네트워크가 필요하지 않으며, API를 새로 호출하지 않는다. macOS/Linux에서는 `.venv/Scripts/python.exe`를 `.venv/bin/python`으로 바꾼다. 실행 환경 버전은 검증 결과와 [requirements.lock.txt](실행증빙/requirements.lock.txt)에 보관했다.

검증 항목은 원본·입력·산출물 해시, API 수집 성공과 응답 해시의 일치, 측정소 중복·시각, 필드별 결측, PM10·PM2.5 요약, 표본 수·평균, 독립적으로 계산한 경험적 누적분포의 KS 통계량, SciPy p-value, `< alpha` 규칙이다. 이번처럼 두 표본이 완전히 분리되고 크기가 같은 경우의 정확 p-value `2 / C(80,40)`도 추가 대조했다. 모두 통과했다.

## API 키 처리와 법령 API 결과

사용자가 채팅으로 제공한 두 인증값은 호출 프로세스의 메모리/환경변수로만 전달했다. 키를 `.env.example`, 소스, JSON, 로그, Git에 새로 기록하지 않았다. 인증값이 포함된 요청 URL과 원시 예외 메시지도 저장하지 않았다.

국가법령정보 API에도 실제 요청을 보냈지만, HTTP 200 응답 본문은 `사용자 정보 검증에 실패하였습니다.`였고 서버 IP주소 및 도메인주소 등록을 요구했다. 정상 법령 검색으로 처리하지 않았다. 이 등록 설정은 미완료이며, 에어코리아만 사용하는 02주차 필수 제출물에는 영향을 주지 않는다.

향후 별도로 법령 API 등록을 해결한 뒤 `LAW_OPEN_API_OC` 환경변수가 있는 세션에서 아래 명령으로 법령 연결만 재확인할 수 있다.

```powershell
python "01주차 과제 제출/02주차/실행증빙/API_연결확인.py" --service law
```

연결 확인 도구는 기존 설정 파일의 `--env-file` 지정도 지원한다. [공식 법령 목록 조회 안내](https://open.law.go.kr/LSO/openApi/guideResult.do)에 따라 `OC`, `target=law`, `type=JSON`을 사용한다. 이 작업에서 법률 해석이나 조문 답변을 생성하지 않았다.

## 강의 확인 범위

[02주차 강의 PDF](../../02_강의PDF/02주차_강의자료.pdf) 전체 10쪽을 읽고 유입 패턴, 중복·지연·결측·스키마 변경, 이벤트 시간과 처리 시간, 워터마크, 데이터/개념 드리프트, KS 해석과 표본 크기, 실습 2.1~2.2 및 마지막 과제 조건을 확인했다.

근거: PDF 7쪽의 스냅샷·실시간 옵션, 8쪽의 판정 절차, 9쪽의 JSON 2개와 문항별 3문장 이내 조건. 원본 코드·기준 데이터는 [교수자 저장소](https://github.com/LeeSeogMin/mlops_public/tree/9b6618ca6efa5ca22f45301b824e62140519c204/practice/chapter2)에서 복사했고 교수자 저장소 자체는 수정하지 않았다.
