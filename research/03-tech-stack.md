# 기술 스택

## 공개 레포에서 확인한 것 [공개]

| 레포 | 언어 | 도구 |
| --- | --- | --- |
| `bulk_restore` | Python 3.12 | boto3, Clumio Python SDK, Ruff, mypy, green, coverage, pre-commit, yamllint, CloudFormation, Lambda, Step Functions |
| `bulk_onboarding` | Python | Makefile, CloudFormation StackSet |
| `clumio-python-sdk` | Python | pydantic 모델, mypy, SonarCloud, 자동 릴리스 |
| `clumio-terraform-mcp` | Python 3.12 | uv, fastmcp, pytest |
| `terraform-provider-clumio` | Go | golangci-lint, goreleaser, mockery, dependabot(github-actions, gomod 주 1회) |
| `clumio-go-sdk` | Go | 봇이 API 정의로 생성 |

공고 문장 기준 언어는 Python, Go가 같이 나옴. 자동화 쪽은 Python이 중심이고 백엔드는 Go, Java, Python을 다 언급함.

## 이 레포의 선택

| 영역 | 선택 | 이유 |
| --- | --- | --- |
| 언어 | Python 3.12 | Automation 공고의 주 언어. `bulk_restore`의 `requires-python`과 같음 |
| AWS SDK | boto3 | 공고의 "Python으로 AWS 인프라를 다룸"과 같음 |
| 린트, 포맷 | Ruff | `bulk_restore`와 같은 규칙 묶음(`D`, `I`, `PL`, `S`, `W`, `UP`) |
| 타입 검사 | mypy (`disallow_untyped_defs`) | `bulk_restore`와 같음. boto3 타입은 `boto3-stubs` |
| 단위 시험 | unittest + green | `bulk_restore`와 같음 |
| 통합 시험 | pytest + moto 서버 (로컬), LocalStack (CI) | 픽스처로 환경을 만들고 지우는 일이 많아서 pytest가 맞음 [추정] |
| 의존성 고정 | requirements.txt `==` 고정 | `bulk_restore`와 같음 |
| 훅 | pre-commit, Clumio `pre-push-hooks` | Clumio 레포에서 그대로 씀 |
| CI | GitHub Actions | `bulk_restore`의 단계 순서(lint → mypy → format-check → test) 그대로 |
| 의존성 업데이트 | dependabot (pip, github-actions 주 1회), 반영은 사람이 직접 | 아래 dependabot 운영 절 참고 |
| 배포 | CloudFormation | `bulk_restore`가 CloudFormation 한 장으로 배포함 |

## dependabot 운영 [공개]

- `clumio-code`에서 `dependabot.yml`이 있는 레포는 `terraform-provider-clumio` 하나임. `bulk_restore`, `bulk_onboarding`, `clumio-python-sdk`, `clumio-go-sdk`, `terraform-clumio-gcp-template`에는 없음
- `terraform-provider-clumio`의 dependabot PR 9개 중 머지된 것은 0개. 5개는 열려 있고 4개는 머지 없이 닫힘 (2026-10-27 기준)
- main 이력(최근 100개)의 작성자는 전부 사람 계정임. 의존성 업데이트는 사람이 올리는 `Release 0.x.y` PR의 CHANGELOG에 "Updated dependencies."로 들어감
- 이 레포도 같은 방식으로 함. 봇 PR은 새 버전 알림으로 쓰고, 반영은 소유자 계정 커밋으로 하고, 반영한 뒤 봇 PR을 닫음

## 고르지 않은 것

- uv를 프로젝트 관리 도구로 쓰는 것: `clumio-terraform-mcp`는 uv를 쓰지만 `bulk_restore`는 pip와 requirements를 씀. 자동화 레포인 `bulk_restore`를 따름. 로컬에서 가상 환경과 Python 설치에만 uv를 씀
- gray 포맷터: `bulk_restore`의 pre-commit에 있지만 ruff format과 하는 일이 겹침
- Go: 첫 버전에서는 쓰지 않음. 확장 단계에서 체크섬 검증기를 Go로 만들지 고민 중

## 출처

- bulk_restore https://github.com/clumio-code/bulk_restore
- clumio-python-sdk https://github.com/clumio-code/clumio-python-sdk
- clumio-terraform-mcp https://github.com/clumio-code/clumio-terraform-mcp
- terraform-provider-clumio https://github.com/clumio-code/terraform-provider-clumio
