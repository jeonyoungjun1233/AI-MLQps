# 6주차 과제 완성본

실제 Airflow 3.3.0 / Python 3.13.16 / Ubuntu 실행 및 입력 대조 검증을 완료했다. 실습은 고정 JSONL 배치 처리이며 외부 API를 호출하지 않았다.

## LMS에 제출할 것

1. [ch6_batch_run_report.json](practice/chapter6/data/output/ch6_batch_run_report.json)을 **이름·내용 변경 없이 그대로** 첨부한다.
2. [06주차_서술형답안.txt](06주차_서술형답안.txt)의 1~3번 답안을 LMS 본문에 붙여 넣는다. 파일 제출 방식이면 [06주차_과제답안.pdf](06주차_과제답안.pdf)를 함께 첨부한다. TXT와 PDF는 같은 답안이므로 중복 제출할 필요 없다.
3. 첨부 파일과 본문을 확인하고 최종 제출 버튼을 누른 뒤 제출 완료 상태를 확인한다.

기한은 **수업일 포함 7일 이내**다. 실습 데이터 날짜(7월 1~3일)는 수업일이나 제출 마감일이 아니다. 실제 수업일과 LMS 마감 시각은 확인되지 않았다. **LMS 업로드와 최종 제출은 아직 하지 않았다.** 전체 폴더·실행 로그·ZIP은 필수 제출물이 아니다.

## 확인한 결과

- 7월 1일: physical=20, valid=20, mapped=18, missing=1, unmapped=1, dup_removed=0, gate=PASS, preservation_ok=true.
- 일별 사흘 실행 성공, 7월 1일 재실행 해시 일치, 입력 없는 7월 4일 validate_input 실패와 후속 upstream_failed 확인.
- 주간 롤업 성공: 60 = 54 + 2 + 3 + 1, preservation_ok=true. 실제 포함 날짜는 7월 1~3일이다.
- [GitHub 실제 실행](https://github.com/jeonyoungjun1233/AI-MLQps/actions/runs/38114810747) 성공 및 CH6_RUN_PASS 확인.

## 구성과 재현

- `practice/chapter6/`: 원본 실행기·DAG, 고정 입력, 실제 일별·주간 산출물과 제출 JSON.
- `실행증빙/`: 실제 실행 로그, 설치 버전, 공식 constraints, 실행 주소, 검증 코드와 결과.
- [입력 출처](입력_출처.md): 누락 매핑 CSV 보완 및 PDF와 상세 원고의 표 번호 차이 설명.
- [실행 설명](실행증빙/실행설명.md): 실제 실행 범위 및 재실행 방법.

교수자 저장소는 변경하지 않았다. 제출용 JSON은 Actions에서 생성한 파일을 바이트 그대로 가져왔다. 답안은 이 파일의 실제 값으로 작성했다.
