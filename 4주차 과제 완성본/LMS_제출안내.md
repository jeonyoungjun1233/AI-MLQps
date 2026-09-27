# 4주차 과제 완성본

LMS의 4주차 과제 한 건에 아래 JSON 두 개를 **함께 첨부**하고, `LMS_붙여넣기.txt`의 세 문항 답안을 본문/답안 입력란에 붙여 넣으세요.

1. `practice/chapter4/data/output/ch4_delivery_report.json`
2. `practice/chapter4/data/output/ch4_dedup_report.json`

답안 입력란이 없으면 `04주차_과제답안.pdf`를 두 JSON과 함께 첨부하세요. PDF는 서술형 답안용이며 필수 JSON을 대체하지 않습니다. 소스 코드·SQLite·실행 로그는 증빙 보관용이고 강의에서 요구한 필수 첨부 파일은 아닙니다.

강의 PDF 5쪽: 수업일 포함 7일 이내 제출. 실제 수업일, LMS 마감 시각·허용 확장자는 LMS에서 확인해야 합니다. 파일 첨부 후 제출 버튼을 누르고 제출 완료 화면과 첨부 목록을 확인하세요. 이 폴더를 만들고 GitHub에 올린 것은 LMS 제출 완료를 뜻하지 않습니다. LMS 제출은 아직 하지 않았습니다.

## 실행 및 출처

- 강의 PDF 전체 5쪽을 확인했습니다. 과제 조건은 5쪽 7절입니다.
- Kafka 전달 보고서는 이번 PC의 실제 Kafka 3.9.1 + ZooKeeper에서 교수자 원본 Python 코드를 실행해 생성했습니다. 민원 내용은 교수자 코드가 만든 가상 데이터이며, 브로커 전달·장애·재수신은 실제 실행입니다.
- Docker/WSL 미설치로 Windows용 Java 17에서 브로커를 직접 기동했습니다. 강의 Docker의 Confluent 7.5.0과 실행 환경이 다릅니다. 클라이언트는 kafka-python 3.0.7입니다.
- 중복 제거 보고서는 교수자 제공 `data/input/ch4_alo_duplicate_stream.jsonl` 스냅샷을 SQLite에 실제 적재해 새로 생성했습니다. 이번 Kafka C 처리 파일을 연결한 결과나 외부 API 실시간 데이터는 아닙니다.
- PDF 4쪽의 `cd ../chapter5` 대신 실제 저장소의 `practice/chapter4/run_dedup.py`를 사용합니다. `run_chapter4.py`는 두 실습을 순서대로 모두 실행하므로 중복 제거를 별도로 다시 실행할 필요는 없습니다.
- Windows에서 원본 실행기의 토픽 삭제가 파일 잠금으로 실패하여 `실행증빙/Windows_Kafka_실행.py`로 시나리오마다 신규 토픽을 만들었습니다. 원본 생산·소비·커밋·장애·집계 코드는 그대로 실행했습니다. 보고서의 `scenario_topics`는 실제 토픽 목록이며 `topic`은 시나리오 공통 이름 패턴입니다. 이 메타데이터 추가와 초기화 방식 변경 외에 산출 수치는 수정하지 않았습니다.
- 원본 코드·입력과 복사본의 SHA-256, 처리 기록 대사, SQLite 지문, 재실행 결과는 `실행증빙`에 있습니다.

## 결과 검증 재실행

프로젝트 최상위에서 실행:

```powershell
python "4주차 과제 완성본/실행증빙/재실행.py"
```

표준 라이브러리만 사용합니다. 제출본을 바꾸지 않고 Kafka 저장 기록을 대사하고, 임시 폴더에서 SQLite 실습을 재실행합니다. 새 Kafka 실험이나 API 호출은 하지 않습니다.

Kafka 실험을 새로 실행하려면 별도 작업 복사본과 실습 전용 localhost:9092 브로커를 준비한 뒤 requirements를 설치합니다(이번 실행은 kafka-python==3.0.7). Windows에서는 `실행증빙/Windows_Kafka_실행.py`를 실행하면 매번 새 토픽을 생성하며, 브로커 기동 자체는 별도로 해야 합니다. Linux/Docker의 교수자 원본 경로는 `practice/chapter4/run_chapter4.py`입니다. 원본 실행기는 `public.complaint.received.v1` 토픽과 g-baseline/g-amo/g-alo 그룹을 초기화하므로 다른 데이터가 있는 브로커에는 실행하지 마세요. 제출 폴더에서 직접 실행하면 JSON·기록·DB가 덮어써집니다.

초기 연결 실패는 Windows localhost의 IPv6 연결과 IPv4 전용 리스너 불일치로 확인했습니다. 양쪽 주소로 연결 가능한 리스너로 조정하고 실행했습니다. Java·Kafka 다운로드와 가상환경은 최상위 tmp에만 두며 Git에 포함하지 않습니다.

환경 참고: https://kafka.apache.org/39/getting-started/quickstart/
