# 02주차 과제 제출

202373020 전영준 · AI 데이터개발과 MLOps

## 제출할 것

1. [ch2_eda_summary.json](practice/chapter2/data/output/ch2_eda_summary.json)을 LMS에 그대로 첨부한다.
2. [ch2_drift_result.json](practice/chapter2/data/output/ch2_drift_result.json)을 LMS에 그대로 첨부한다.
3. [02주차_서술형_답안.txt](02주차_서술형_답안.txt)의 두 답안을 LMS 본문에 붙여 넣는다. 각각 2문장·3문장이다.

JSON은 교수자 실습 코드가 생성한 파일을 수정 없이 보관했다. ZIP이나 추가 PDF는 필수 제출물이 아니다. 제출 기한은 수업일 포함 7일 이내이며, 실제 마감과 LMS 제출 완료 상태는 아직 확인하지 않았다.

## 실제 실행 결과

| 항목 | 결과 |
|---|---|
| 입력 출처 | 교수자가 제공한 실제 에어코리아 응답 스냅샷 |
| 기준 이벤트 시각 | 2026-06-28 22:00 KST |
| 비교 이벤트 시각 | 2026-06-28 23:00 KST |
| 기준/비교 PM10 표본 수 | 40 / 40 |
| PM10 평균 | 20.025 → 20.775 ㎍/㎥ |
| PM10 측정값 결측 | 기준 0개 |
| PM10 등급 결측 | 기준 1개 (`pm10_grade_counts`의 `nan` 항목) |
| KS 통계량 | 0.175 |
| p_value | 0.5786001416508443 |
| alpha | 0.05 |
| drift_detected | false |

`p_value < alpha`일 때만 true가 된다. 이번 false는 귀무가설을 기각하지 못했다는 뜻이며, 분포가 같다는 증명은 아니다. `baseline_n=40`처럼 작은 표본은 실제 차이를 감지할 검정력이 부족할 수 있다.

강의 PDF의 평균 20.0은 반올림한 설명이고, 원본 코드의 실제 출력은 20.025이다. 제출 JSON의 실제 계산값을 유지했다. 측정 시각은 응답의 `dataTime`, 재실행 시각은 [검증결과.json](실행증빙/검증결과.json)에 각각 기록했다.

## 실행 증빙과 재현

[EDA 로그](실행증빙/2-1-parse-api.log) · [KS 검정 로그](실행증빙/2-2-drift-visualize.log) · [분포와 분위수 비교](practice/chapter2/data/output/ch2_drift_visual.txt) · [원본 해시](실행증빙/교수자_원본_해시.json) · [검증 결과](실행증빙/검증결과.json)

저장소 루트에서 다음을 실행한다. Python 3.10 이상이 필요하다.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r "01주차 과제 제출/02주차/practice/chapter2/code/requirements.txt"
.\.venv\Scripts\python.exe "01주차 과제 제출/02주차/실행증빙/재실행.py"
```

macOS/Linux에서는 `.venv/Scripts/python.exe` 대신 `.venv/bin/python`을 사용한다. 실행 당시 Python·패키지 버전은 검증 결과와 [requirements.lock.txt](실행증빙/requirements.lock.txt)에 보관했다. 설치 이후 재계산에는 API 키나 네트워크가 필요하지 않다.

재실행은 복사한 교수자 코드 2개를 그대로 실행한다. 입력·소스 SHA-256, 측정소 중복, 입력별 이벤트 시각, 필드별 결측, PM10·PM2.5 요약, 표본 수와 평균, 별도로 계산한 경험적 누적분포의 KS 통계량, SciPy p-value, 엄격한 `< alpha` 판정 규칙을 검증한다. 제출 JSON과 답안은 재계산 결과에 맞춰 갱신된다.

## API 설정 확인 상태

이번 점검에서 `02_강의저장소/mlops_public/.env.example`의 두 인증 설정은 안내용 값이었다. 작업 폴더의 다른 `.env` 파일과 프로세스·Windows 사용자/시스템 환경변수에서도 실제 값을 찾지 못했다. 따라서 이번 작업의 실시간 API 요청 횟수는 0이며, 스냅샷 실행을 실시간 호출 성공으로 보고하지 않았다. 이전 1주차 증빙의 HTTP 403 결과는 과거 호출 기록이다.

인증키 저장 위치가 확인되면 기존 파일을 지정해 연결을 검증할 수 있다. 키 값은 새 파일이나 Git에 기록하지 않는다.

```powershell
python "01주차 과제 제출/02주차/실행증빙/API_연결확인.py" --env-file "실제 키가 저장된 기존 파일의 경로"
```

환경변수 `DATA_GO_KR_API_KEY`, `LAW_OPEN_API_OC`도 지원한다. [API_호출확인.json](실행증빙/API_호출확인.json)에 인증값과 인증값이 포함된 요청 URL을 제외한 결과만 저장한다. 에어코리아 성공 시 실제 응답은 별도 `airquality_seoul_live.json`으로 보관하며, 제출물은 자동 변경하지 않는다.

02주차 필수 실습은 에어코리아 데이터만 사용한다. 법령 API는 별도 연결 확인 대상으로 두었으며, [공식 목록 조회 안내](https://open.law.go.kr/LSO/openApi/guideResult.do)에 따라 `OC`, `target=law`, `type=JSON`으로 개인정보 보호법을 검색한다. 법률 해석이나 조문 답변을 생성하는 작업은 아니다.

## 강의 확인 범위

[02주차 강의 PDF](../../02_강의PDF/02주차_강의자료.pdf)의 전체 10쪽을 읽고 유입 패턴, 중복·지연·결측·스키마 변경, 이벤트 시간과 처리 시간, 워터마크, 데이터/개념 드리프트, KS 검정의 해석과 표본 크기, 실습 2.1~2.2, 마지막 과제 조건을 확인했다.

근거: PDF 7쪽의 스냅샷 기본값과 실시간 옵션, 8쪽의 실습 판정 절차, 9쪽의 제출 파일 2개와 문항별 3문장 이내 조건. 코드·입력 출처는 [교수자 저장소의 해당 커밋](https://github.com/LeeSeogMin/mlops_public/tree/9b6618ca6efa5ca22f45301b824e62140519c204/practice/chapter2)이며, 교수자가 미리 생성한 출력 파일은 복사하지 않았다.
