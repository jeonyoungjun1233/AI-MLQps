# 10주차 MLQps (202373020 전영준 과제)

10주차 실습과 제출 자료를 한 폴더에 모았다. 교수자 원본 실행기·앱·Dockerfile·입력은 변경하지 않았다.

## LMS 제출

1. [ch10_deploy_report.json](practice/chapter10/data/output/ch10_deploy_report.json)을 이름·내용 변경 없이 그대로 첨부한다.
2. [10주차 과제 답안 PDF](10주차_과제답안.pdf)를 함께 첨부한다. 본문 입력 방식이면 [서술형 TXT](10주차_서술형답안.txt)의 1~3번을 붙여 넣는다. 각 답안은 3문장이다.
3. 첨부 파일과 답안을 확인하고 최종 제출 후 LMS의 제출 완료 상태를 확인한다.

**수업일 포함 7일 이내** 제출한다. 실제 수업일·LMS 마감 시각은 확인하지 않았으며, **LMS 업로드·제출은 아직 하지 않았다.** GitHub 푸시는 LMS 제출을 대신하지 않는다. 코드·로그·MLflow 압축 파일은 보관용이며 LMS 필수 첨부 대상은 아니다.

## 실행과 확인 자료

실제 실행은 **CH10_RUN_PASS**로 완료됐으며 pytest 4개와 체크리스트 8항목이 통과했다. 호스트·컨테이너 예측은 모두 6.0, 잘못된 입력 응답은 모두 422였다. model_source는 각각 registry-alias와 local-dir이며 이미지 내부 앱 바이트는 원본과 일치했다.

- [실제 GitHub Actions 실행](https://github.com/jeonyoungjun1233/AI-MLQps/actions/runs/41944634886): Linux 호스트 HTTP와 실제 Docker 컨테이너 HTTP 호출을 모두 수행하는 전체 실습.
- `practice/chapter10/data/output/`: 수정하지 않은 실행 보고서·체크리스트·bootstrap 요약·shadow 로그.
- `실행증빙/run.log`, `GitHub실행.json`: 원본 실행 출력과 실행 식별 정보.
- `실행증빙/이미지검증.json`, `image_app.py`, `image_export_info.json`: 실제 이미지에서 꺼낸 파일과 바이트 대조.
- `실행증빙/원본대조.json`: 교수자 코드·입력 8개와 개인 작업본의 SHA-256 일치 확인.
- [실행 설명과 재현 방법](실행증빙/실행설명.md), [독립 검증 결과](실행증빙/검증결과.json).

여기서 호스트는 GitHub runner의 Linux 호스트를 뜻한다. 입력은 고정 피처 스냅샷이며 외부 민원 API의 실시간 수집이 아니다. 학생의 실행 전 예측은 별도로 제공되지 않았으므로 수행한 것으로 기록하지 않았다.
