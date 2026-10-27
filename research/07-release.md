# 버전과 릴리스

## 공개된 내용 [공개]

- `bulk_restore`는 레포 최상위 `VERSION` 파일이 버전의 유일한 원천임
  - `make build`가 zip 이름(`clumio_bulk_restore-${VERSION}.zip`), zip 안의 `version.txt`, CloudFormation 템플릿의 `__BULK_RESTORE_VERSION__` 자리표시자에 버전을 넣음
  - 버전이 바뀌면 S3 키가 바뀌어서 CloudFormation이 Lambda 코드를 다시 가져옴. Lambda 설명만 바뀌면 다시 가져오지 않기 때문임
  - 템플릿에 버전을 직접 쓰지 말라고 문서에 적혀 있음
- `terraform-provider-clumio` CHANGELOG 형식
  ```
  ## 0.24.2
  This update contains the following changes:
  * Added `terraform import` support for `clumio_gcp_connection`.
  * Fixed an apply failure in `clumio_policy` when ...
  ```
  `Added`, `Fixed`, `Updated`, `Removed`로 시작하는 과거형 문장
- 릴리스 PR 제목은 `Release 0.24.2`
- `clumio-python-sdk` 릴리스 PR은 본문을 새 기능, 폐기 예정으로 나눠서 씀

## 이 레포의 규칙

- `VERSION` 파일 하나로 버전을 관리함. `pyproject.toml`도 이 파일을 읽음
- CHANGELOG는 위 형식을 한국어로 씀
  ```
  ## 0.1.0
  이번 버전의 변경 사항:
  * 추가: ...
  * 수정: ...
  ```
- 동작이 바뀌는 PR은 같은 PR에서 CHANGELOG를 고침
- 릴리스 PR 제목은 `PITR-<번호>: 0.1.0 릴리스`, 태그는 `v0.1.0`, 태그에도 서명함

## 출처

- bulk_restore CLAUDE.md의 Versioning 절 https://github.com/clumio-code/bulk_restore
- terraform-provider-clumio CHANGELOG https://github.com/clumio-code/terraform-provider-clumio/blob/main/CHANGELOG.md
