# 티켓, 브랜치, 커밋, PR

## 공개된 내용 [공개]

- 커밋 제목은 지라 티켓 키로 시작함
  ```
  CQ-7893: use backuprecord keypair when target account and region matched ... (#72)
  CQ-7188: Add retry for HTTP request. (#69)
  CESC-3162: Add DDB restore customzation to DDB bulk restore (#73)
  NOJIRA: remake the fix the AwsTag key. (#63)
  ```
  - 티켓이 없으면 `NOJIRA:`
  - 끝의 `(#72)`는 squash merge 때 GitHub이 붙임. main 이력이 PR 하나당 커밋 하나임
  - 마침표는 붙인 것과 안 붙인 것이 섞여 있음
- 브랜치는 `user/<이름>/<티켓>/main` 형식: `user/meher/CQ-7893/main`, `user/dahye/CLUMIO-73378/main`
- `pre-push-hooks`의 `check-branch-for-push`로 `^user/.*`, `^team/.*`, `^revert-[0-9]+-user/.*`가 아닌 브랜치는 푸시를 막음. 훅 주석에 내부 티켓(`CENG-1675`)이 남아 있음
- 릴리스 커밋은 `Release 0.24.2`
- PR 본문은 머리말 없이 바로 목록으로 씀
  ```
  - README claimed Python 3.6 while setup.py requires 3.9 or higher.
  - Corrected the version and pointed readers at requirements.txt.
  ```
- PR 템플릿 파일은 공개 레포 어디에도 없음
- `terraform-provider-clumio`의 CONTRIBUTING은 모든 커밋에 서명을 요구함
- 커밋 언어는 영어

## 공개되지 않은 내용 [추정]

- 리뷰 승인 인원, 코멘트 규칙
- 사내 레포의 브랜치 보호 설정

## 이 레포의 규칙

- 티켓: GitHub 이슈. 저장소 설정의 Autolink references로 `PITR-<번호>`를 이슈 링크로 바꿈. 지라 티켓 키와 PR 번호가 따로 노는 Clumio 이력과 같은 모양이 됨
- 커밋: `PITR-<번호>: <한국어 음슴체 요약>`. 마침표 없이 씀. 본문에는 왜 바꿨는지를 음슴체로 씀
- 티켓이 없는 자잘한 수정은 `NOTICKET:`
- 브랜치: `user/ajin/PITR-<번호>/main`
- 머지: squash merge만 허용. PR 제목이 main 커밋이 됨
- 서명: SSH 키로 모든 커밋과 태그에 서명함
- 보호: main 직접 푸시 금지(훅 + GitHub 규칙), CI 통과 필수
- 커밋 언어는 한국어로 함. Clumio는 영어지만, 이 레포는 조사, 회고와 같은 언어로 이력을 읽을 수 있게 함

자세한 규칙은 [CONTRIBUTING.md](../CONTRIBUTING.md) 참고.

## 출처

- bulk_restore 커밋 이력 https://github.com/clumio-code/bulk_restore/commits/main
- bulk_restore .pre-commit-config.yaml https://github.com/clumio-code/bulk_restore/blob/main/.pre-commit-config.yaml
- pre-push-hooks https://github.com/clumio-code/pre-push-hooks
- terraform-provider-clumio CONTRIBUTING https://github.com/clumio-code/terraform-provider-clumio/blob/main/CONTRIBUTING.md
- GitHub Autolink references https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/managing-repository-settings/configuring-autolinks-to-reference-external-resources
