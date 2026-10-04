# 05주차 LMS 제출 안내

## LMS에 제출할 것

1. `practice/chapter5/data/output/ch5_late_event_report.json`을 **내용 수정 없이 그대로 첨부**합니다.
2. `LMS_붙여넣기.txt`의 세 답안을 LMS 본문/답안 입력란에 붙여 넣습니다(각 문항 3문장).
3. 답안 입력란이 없으면 `05주차_과제답안.pdf`를 JSON과 함께 첨부합니다. PDF는 필수 JSON을 대체하지 않습니다.
4. 제출 버튼을 누른 뒤 파일명·첨부 목록·제출 완료 상태를 확인합니다.

강의 PDF 9쪽은 **수업일 포함 7일 이내** 제출을 요구합니다. 실제 수업일과 LMS에 표시된 마감 시각·허용 형식은 별도로 확인해야 합니다. 이 작업은 제출 파일 준비와 GitHub 업로드이며, LMS 제출은 아직 하지 않았습니다.

## 보관용 파일

- `05주차_서술형_답안.txt`, `05주차_과제답안.pdf`: 같은 내용의 답안.
- `강의내용_상세해설.md`: 강의 전체의 핵심 개념과 실제 실행 결과 해설.
- `practice/chapter5/data/output/ch5_window_counts.jsonl`: micro-batch별 집계 원본.
- `practice/chapter5/data/output/ch5_sliding_demo.json`: 전체 강남구 이벤트의 정적 sliding 비교 결과.
- `실행증빙`: 실행 로그, 검증 결과, 원본 코드·산출물 해시, 체크포인트 watermark, 환경 정보와 재실행 도구.

강의에서 필수 업로드로 지정한 것은 `ch5_late_event_report.json` 한 개입니다. 보관용 코드·로그·보조 산출물까지 전부 LMS에 첨부할 필요는 없습니다.

## 실행의 성격과 환경

교수자 `run_chapter5.py`와 실습 코드를 변경 없이 복사해 실행했습니다. 민원 내용은 코드가 생성하는 2026-07-07 시각의 고정된 가상 입력 14건입니다. 실제 Spark Structured Streaming 엔진에서 파일을 순차 투입하고 수용·폐기를 측정한 결과이며, 교수자 예시 JSON 복사나 실시간 API 조회 결과가 아닙니다.

Python 3.13.15, PySpark 4.1.2, Java 17을 사용했습니다. Windows의 경로 문제는 영문 임시 경로 별칭으로, Hadoop 네이티브 파일 누락은 별도 Windows 라이브러리로 해결했습니다. 실행 설정만 조정했고 watermark·창·입력·판정 코드는 수정하지 않았습니다. Windows 네이티브 파일은 공식 ASF 바이너리가 아닌 별도 배포본이며 URL·커밋·SHA-256은 `실행증빙/Windows_의존성출처.json`에 기록했습니다.

## 검증 및 재실행

프로젝트 최상위에서 저장된 결과만 대사하려면 다음 명령을 실행합니다(표준 라이브러리만 필요).

```powershell
python "05주차 과제 제출란/실행증빙/검증.py"
```

실제 Spark 실습을 임시 폴더에서 다시 실행하고 제출본과 비교하려면 다음 명령을 실행합니다.

```powershell
python "05주차 과제 제출란/실행증빙/재실행.py"
```

이 PC에서는 준비한 `tmp/ch5-venv`와 Java·Hadoop 실행 환경을 이용합니다. 다른 PC에서는 Python 3.13 환경에 `pyspark==4.1.2`를 설치하고 Java 17의 `JAVA_HOME`을 설정해야 하며 Windows는 Hadoop 네이티브 환경도 필요합니다. 재실행 도구는 최초 제출 JSON을 덮어쓰지 않고 별도 임시 폴더에서 실행해 생성 시각과 동등한 행의 출력 순서를 제외한 결과를 비교합니다.

원본 `practice/chapter5/run_chapter5.py`를 제출 폴더에서 직접 실행하면 입력 디렉터리·체크포인트·산출물이 초기화되므로, 결과 보존에는 위 재실행 도구를 사용하세요. 새 실행의 생성 시각은 바뀌지만 이벤트 시각은 고정값입니다.

## 참고

- 과제 기준: `02_강의PDF/05주차_강의자료.pdf`, 전체 9쪽 검토, 9쪽 9절.
- Windows Hadoop 환경 참고: [Apache Hadoop WindowsProblems](https://cwiki.apache.org/confluence/spaces/HADOOP2/pages/120730292/WindowsProblems).
