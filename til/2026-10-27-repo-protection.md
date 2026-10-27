# 첫 푸시와 저장소 보호 설정 회고

뼈대를 main에 올리고 서명, 머지 방식, main 보호 규칙을 건 작업. 그 과정에서 dependabot을 끄게 됨.

## 한 줄 요약

"모든 커밋은 내 계정으로"라는 규칙은 내가 만드는 커밋만 보면 지켜지는 것처럼 보이지만, 봇이 만드는 PR과 GitHub이 만드는 머지 커밋까지 봐야 실제로 지켜짐.

## 1. 서명은 했는데 Verified가 안 될 뻔함

- 이슈: 커밋은 SSH 키로 서명해 뒀지만 GitHub 계정에는 서명용 키가 등록돼 있지 않았음. 인증용 키와 서명용 키는 GitHub에서 따로 등록함
- 원인 찾기: `gh` 토큰에 `admin:ssh_signing_key` 권한이 없어서 등록 API가 404를 돌려줌
- 해결: 권한을 받은 뒤 같은 키를 서명용으로 등록하고 나서 푸시함. GitHub은 푸시한 시점에 서명을 검증해서 기록하므로, 키 등록 전에 올리면 나중에 등록해도 Unverified로 남을 수 있음
- 확인: 커밋 7개가 전부 작성자 `ganimjeong`, `verified=true`인지 API로 봄
- 로컬에서 `git log --show-signature`가 `allowedSignersFile` 오류를 냄. SSH 서명은 GPG와 달리 "누구의 키인지"를 로컬 파일로 알려 줘야 검증함. 레포 안 `.git/allowed_signers`에 내 이메일과 공개 키를 적어서 해결함
- 배운 점: 서명은 만드는 것과 검증되는 것이 다른 단계다. 검증할 쪽(GitHub, 로컬)에 키가 먼저 있어야 한다

## 2. dependabot PR을 머지하면 작성자가 봇이 됨

- 이슈: 첫 푸시 직후 dependabot이 Actions 버전 업데이트 PR 3개를 열었음
- 판단: squash merge하면 main 커밋 작성자는 PR 작성자인 `dependabot[bot]`이 됨. 이 레포는 모든 커밋을 내 계정으로만 남기기로 했으므로 규칙과 충돌함. Clumio의 `clumio-python-sdk`는 dependabot을 쓰지만, 이건 회사 규칙이 아니라 이 레포만의 제약이라 이 레포의 규칙을 따름
- 결정
  - `dependabot.yml`을 지우고 열린 PR은 이유를 남기고 닫음
  - 같은 업데이트(checkout, setup-python, upload-artifact를 v7로)는 이 PR에서 직접 함
  - 취약점 알림은 커밋을 만들지 않으므로 계속 켜 둠. 알림이 오면 직접 PR을 올림
- 재발 방지: CONTRIBUTING 그라운드 룰에 "봇 PR을 머지하지 않고 직접 커밋함"을 넣음
- 배운 점: 이력의 작성자는 내가 친 `git commit`만으로 정해지지 않는다. 자동화 도구가 커밋을 만드는 경로를 먼저 다 적어 본다

## 3. main 보호 규칙

- 결정
  - 머지는 squash만 허용함. 커밋 제목은 PR 제목, 본문은 PR 본문으로 씀. main 이력이 PR 하나당 커밋 하나가 되고 끝에 `(#번호)`가 붙음
  - 규칙: 삭제 금지, 강제 푸시 금지, 선형 이력, 서명 필수, PR 필수, CI 통과 필수, 리뷰 스레드 해결 필수
  - 승인 인원은 0으로 둠. 혼자 하는 레포에서 1로 두면 내 PR을 내가 승인할 수 없어서 머지가 막힘. 대신 PR마다 셀프 리뷰 댓글로 고른 방법과 버린 방법을 남김
- 순서: 첫 커밋들을 main에 올린 다음에 규칙을 걸었음. 먼저 걸면 main이 비어 있는 상태에서 PR을 만들 대상 브랜치가 없음
- 배운 점: 보호 규칙은 "무엇을 막을까"보다 "막은 뒤에도 일이 되는가"를 같이 봐야 한다

## 4. pre-commit의 ruff 훅이 legacy alias로 나옴

- 이슈: `pre-commit run --all-files` 결과에 `ruff (legacy alias)`가 찍힘. 통과는 했음
- 원인 찾기: `bulk_restore`는 ruff-pre-commit v0.14.0에서 `id: ruff`를 씀. 이후 버전에서 훅 id가 `ruff-check`로 바뀌고 `ruff`는 옛 이름으로만 남음
- 해결: `id: ruff-check`로 바꿈
- 배운 점: 회사 설정을 복사할 때는 그 설정이 쓰는 도구 버전도 같이 본다. 나는 더 새 버전을 쓰고 있어서 이름이 바뀐 걸 그대로 가져올 뻔했음
