# 기술 스택 정리

Clumio 서울 Automation, Backend 공고와 `clumio-code` 공개 레포를 기준으로 고름. 근거 자료는 [research/03-tech-stack.md](../research/03-tech-stack.md).

## 언어

### Python 3.12

- 이점: boto3로 AWS를 바로 다룸. 시험 자동화 도구가 가장 많음
- 선택 이유: Automation 공고의 주 언어이고 `bulk_restore`의 `requires-python = '>=3.12'`과 같음
- 로컬에는 3.15가 깔려 있었지만 3.12로 맞춤. Lambda에서 돌릴 코드라 Lambda가 지원하는 런타임 버전에 맞춰야 하고, 회사 레포와 같은 버전에서 같은 린트 결과가 나와야 비교가 됨

## AWS

### boto3 + botocore 재시도 설정

- 이점: 재시도, 백오프, 스로틀링 대응이 SDK 안에 있음
- 선택 이유: 공고의 "Python으로 AWS 인프라를 다룸"과 같음
- 재시도는 `adaptive` 모드 하나로만 함. 자세한 이유는 [초기 세팅 회고](2026-10-27-initial-setup.md)

### DynamoDB (카탈로그)

- 이점: 조건부 쓰기로 같은 버전을 두 번 기록하지 않게 막을 수 있음. 정렬 키로 시점 조회를 할 수 있음
- 선택 이유: 공고가 "S3와 DynamoDB 위에 만든 플랫폼"이라고 씀

## 품질

### Ruff

- 이점: 린트와 포맷을 한 도구로 함. 빠름
- 선택 이유: `bulk_restore`와 같은 규칙 묶음(`D`, `I`, `PL`, `S`, `W`, `UP`)과 홑따옴표 포맷을 그대로 씀

### mypy (disallow_untyped_defs)

- 이점: 타입 없는 함수를 막음. boto3 응답 타입 실수를 빌드 전에 잡음
- 선택 이유: `bulk_restore`와 같음. boto3 타입은 `boto3-stubs`로 받고 버전을 boto3와 맞춤

## 시험

### unittest + green (단위 시험)

- 이점: 표준 라이브러리라 의존성이 적음. green은 병렬 실행, 커버리지, JUnit 보고서를 같이 해 줌
- 선택 이유: `bulk_restore`와 같음

### pytest + moto 서버 (통합 시험)

- 이점: 픽스처로 버킷, 테이블을 만들고 지우는 일을 시험마다 반복하지 않아도 됨
- 선택 이유: 로컬에 Docker가 없어서 LocalStack을 못 띄움. moto는 Python 프로세스 안에서 서버로 뜨기 때문에 Docker 없이 같은 엔드포인트 방식으로 시험할 수 있음. CI도 moto 서버로 함. LocalStack은 2026-03부터 무료 이미지도 인증 토큰이 필요해짐

## 개발 환경

### pre-commit + Clumio pre-push-hooks

- 이점: 커밋 전에 린트, 포맷, 큰 파일을 막고 푸시 전에 브랜치 이름을 검사함
- 선택 이유: `bulk_restore`의 훅 구성을 그대로 씀. 브랜치 훅은 Clumio 공개 레포에서 바로 가져옴

### GitHub Actions

- 단계: lint → mypy → format-check → test. `bulk_restore`와 같은 순서
- 시험 보고서는 실패해도 아티팩트로 올려서 CI 화면에서 바로 받음
