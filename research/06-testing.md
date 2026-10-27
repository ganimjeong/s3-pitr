# 시험

## 공개된 내용 [공개]

- `bulk_restore` 단위 시험
  - `unittest.TestCase` + `unittest.mock`, 실행은 `green`
  - `make test`가 JUnit XML, 커버리지 XML, HTML 보고서를 `build/test_reports/py/`에 만듦
  - 시험 이름은 `test_<함수>_<기대 동작>`: `test_get_total_list_paginates_via_links_next`
  - 시험 독스트링에 기대 동작을 한 문장으로 씀
  - SDK 응답 모델을 실제로 만들어서 `side_effect`로 넣음
- CI 단계: lint → mypy → format-check → test
- Automation 공고: 통합 시험, 부하·스트레스 시험, 시험 실행 인프라 구성, 데이터 생성 도구
- `terraform-provider-clumio`: 새 리소스에는 인수 시험(acceptance test)이 필수

## 공개되지 않은 내용 [추정]

- Clumio 사내 통합 시험 도구와 환경
- 커버리지 기준

## 이 레포의 규칙

- 단위 시험: `s3pitr/test/test_<모듈>.py`, unittest + green. 바깥 서비스는 moto로 흉내 냄
- 통합 시험: `e2e/`, pytest
  - `AWS_ENDPOINT_URL`이 있으면 그 엔드포인트(CI의 LocalStack)를 씀
  - 없으면 moto 서버를 시험 안에서 띄움. 로컬에 Docker가 없어도 돌아감
  - 시나리오: 데이터 생성 → 백업 → 덮어쓰기·삭제 → 다시 백업 → 시점 복구 → 체크섬 비교
- 실패 주입: 같은 버전 두 번 처리, 중간 중단 후 재실행, 스로틀링 응답
- 시험이 처음부터 다 통과하면 의심함. 지키려는 보장을 하나씩 일부러 깨서 시험이 잡는지 확인함
- 커버리지는 분기 기준으로 잼

## 출처

- bulk_restore Makefile https://github.com/clumio-code/bulk_restore/blob/main/Makefile
- bulk_restore test_common.py https://github.com/clumio-code/bulk_restore/blob/main/code/test/test_common.py
- moto 서버 모드 https://docs.getmoto.org/en/latest/docs/server_mode.html
- LocalStack GitHub Actions https://docs.localstack.cloud/user-guide/ci/github-actions/
