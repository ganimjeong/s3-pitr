# 기여 가이드

## 티켓

- 작업은 GitHub 이슈로 시작함. 이슈 번호가 티켓 번호임
- 커밋과 PR에 `PITR-12`라고 쓰면 이슈 12번 링크로 바뀜(저장소 Autolink 설정)
- 이슈 제목도 커밋 요약과 같은 말투로 씀

## 브랜치

- `main`이 배포 버전임. develop, release 브랜치를 따로 두지 않음
- 브랜치 이름은 `user/<이름>/PITR-<번호>/main`. 예: `user/ajin/PITR-12/main`
- `main`에는 직접 푸시하지 못함. pre-push 훅과 GitHub 규칙이 둘 다 막음

## 커밋 메시지

```
PITR-<번호>: <요약>

<본문: 왜 바꿨는지>
```

- 요약은 한국어 음슴체로 짧게, 마침표 없이 씀
- 본문에는 무엇을 했는지보다 왜 했는지를 씀. 고른 방법과 버린 방법이 있으면 같이 적음
- 티켓이 없는 자잘한 수정은 `NOTICKET: README 오타 수정`
- 되돌리기는 GitHub 기본 형식(`Revert "..."`)을 그대로 씀
- 모든 커밋과 태그에 서명함(SSH 키)

예시

```
PITR-7: 이미 백업한 버전은 다시 복사하지 않음
PITR-9: 복구 대상 버킷이 비어 있지 않으면 시작 전에 멈춤
NOTICKET: 시험 이름 오타 수정
```

## PR

- PR 하나에 목적 하나. 변경량은 400줄 안쪽을 권장함
- PR 제목은 커밋 메시지 형식과 같음. squash merge라서 PR 제목이 그대로 `main` 커밋이 됨
- 본문은 머리말 없이 바로 `- ` 목록으로 씀. 무엇을 왜 바꿨는지, 어떻게 확인했는지
- CI(lint, mypy, format-check, test)가 통과해야 머지함
- 동작이 바뀌면 같은 PR에서 CHANGELOG와 시험을 같이 고침

## 코드 작성

`bulk_restore`의 설정을 그대로 따름. 근거는 [research/04-code-style.md](research/04-code-style.md).

- 파일 맨 위에 Apache 2.0 머리말, 그다음 모듈 독스트링
- 모든 모듈은 `from __future__ import annotations`로 시작함
- 이름이 아니라 모듈을 import함 (`from s3pitr import common`)
- 상수는 대문자와 `Final` 타입
- 모듈 예외는 `common.Error`를 상속함
- `print` 대신 `logger = logging.getLogger(__name__)`
- 주석과 독스트링은 음슴체. 무엇을 하는지보다 왜 그렇게 했는지를 적음

## 그라운드 룰

1. 재시도는 botocore 설정(`common.client_config`)에만 맡김. 그 위에 재시도 루프를 또 감싸지 않음. 시도 횟수가 곱해짐
2. 백업과 복구는 몇 번을 다시 돌려도 결과가 같아야 함. 카탈로그 쓰기는 조건부 쓰기로 함
3. 객체 내용 비교에 ETag를 쓰지 않음. 멀티파트 업로드면 MD5가 아님. SHA256 체크섬을 씀
4. 시각은 항상 시간대가 있는 UTC로 다룸. 시간대 없는 `datetime`은 받지 않음
5. 원본 버킷에는 읽기만 함. 복구는 항상 다른 버킷으로 함
6. 시험이 처음부터 다 통과하면 지키려는 보장을 하나 일부러 깨고 시험이 실패하는지 봄

## 시험

- 단위 시험: `s3pitr/test/test_<모듈>.py`. 이름은 `test_<함수>_<기대 동작>`, 독스트링에 기대 동작 한 문장
- 통합 시험: `e2e/`. `AWS_ENDPOINT_URL`이 없으면 moto 서버를 직접 띄움
