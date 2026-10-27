# 코드 스타일

`bulk_restore`의 `pyproject.toml`, `common.py`, `test_common.py`를 읽고 정리함.

## 도구 설정 [공개]

- Ruff: `line-length = 100`, `indent-width = 4`, `target-version = 'py312'`
- 포맷: `quote-style = 'single'`. Black과 달리 홑따옴표
- 린트 규칙: `select = ['D', 'I', 'PL', 'S', 'W', 'UP']`
  - D: 독스트링(pydocstyle, Google 규칙)
  - I: import 정렬
  - PL: pylint 규칙
  - S: 보안(bandit)
  - W: 경고
  - UP: 최신 문법으로 바꾸기
- 끄는 규칙: `D101`, `D102`, `D104`, `D107`, `D410`, `D411`
- 시험 파일은 독스트링 규칙 제외(`'*/test/test_*.py' = ['D']`)
- mypy: `disallow_untyped_defs = true`, `ignore_missing_imports = true`, `follow_imports = 'silent'`
- 모든 파일 맨 위에 Apache 2.0 저작권 머리말

## 코드에서 보이는 관습 [공개]

- 모든 모듈이 `from __future__ import annotations`로 시작함
- 이름이 아니라 모듈을 import함. `from clumioapi.models import aws_environment` 처럼. Google Python 스타일 가이드 규칙
- 상수는 대문자에 `Final` 타입: `MAX_RETRY: Final = 5`
- 타입 별칭은 `if TYPE_CHECKING:` 안에 두고 이름 끝에 `TypeDef`를 붙임: `EventsTypeDef = dict[str, Any]`
- 콜백 타입은 `Protocol`로 정의함
- 모듈마다 `class Error(Exception)`을 두고 구체 예외가 상속함
- 로거는 `logger = logging.getLogger(__name__)`
- Lambda 진입점은 `lambda_handler(events, context) -> dict`, 반환은 `{status, msg, ...}`
- 결정에 대한 주석을 길게 씀. 예: 재시도 대상에서 500을 뺀 이유를 세 줄로 설명함
  ```python
  # Retry only on transient signals. 500 is excluded because Clumio's restore
  # endpoints sometimes return 500 for request-shape errors; retrying buries
  # the underlying error body inside a RetryError.
  ```
- 시험은 MagicMock만 쓰지 않고 실제 응답 모델 객체를 만들어서 넣음

## 이 레포의 규칙

- 위 설정과 관습을 그대로 따름
- 머리말의 저작권자는 본인 이름으로 씀
- 주석과 독스트링은 한국어 음슴체로 씀. 무엇을 하는지보다 왜 그렇게 했는지를 적음
- 독스트링 첫 줄은 마침표로 끝냄(Ruff `D415`)
- 시험 파일은 `S101`(assert), `PLR2004`(매직 넘버)도 끔. 시험에서는 기대값을 숫자로 바로 쓰는 게 더 읽기 쉬움

## 출처

- bulk_restore pyproject.toml https://github.com/clumio-code/bulk_restore/blob/main/pyproject.toml
- bulk_restore common.py https://github.com/clumio-code/bulk_restore/blob/main/code/common.py
- Google Python Style Guide https://google.github.io/styleguide/pyguide.html
