# 조사 자료

레포의 기술 스택, 구조, 규칙을 정할 때 참고한 공개 자료를 정리한 폴더임.
Commvault, Clumio 내부 문서는 볼 수 없으므로 채용 공고, 공시, 회사가 공개한 GitHub 레포를 근거로 삼음.
특히 `clumio-code/bulk_restore`는 2026년 10월에도 커밋이 올라오는 Python 레포라서 설정 파일을 거의 그대로 따라감.

| 파일                                         | 내용                                           |
| -------------------------------------------- | ---------------------------------------------- |
| [01-company.md](01-company.md)               | Commvault, Clumio 회사와 제품, 서울 조직       |
| [02-job-postings.md](02-job-postings.md)     | 서울 공고 분석과 이 레포가 다룰 범위           |
| [03-tech-stack.md](03-tech-stack.md)         | 공개 레포와 공고의 기술 스택, 이 레포의 선택   |
| [04-code-style.md](04-code-style.md)         | Ruff, mypy, Google 스타일, 주석과 독스트링     |
| [05-git-workflow.md](05-git-workflow.md)     | 티켓, 브랜치, 커밋, PR, 서명, 머지             |
| [06-testing.md](06-testing.md)               | 단위 시험, 통합 시험, 실패 주입, 커버리지      |
| [07-release.md](07-release.md)               | VERSION 파일, CHANGELOG, 태그                  |
| [08-s3-backup-design.md](08-s3-backup-design.md) | S3 버전 관리, 체크섬, Object Lock, 증분 방식 비교 |

## 표기

- [공개] 출처에 직접 나온 내용
- [추정] 공개 자료가 없어서 일반적인 관행으로 채운 내용

조사 시점은 2026년 10월 27일임. 채용 공고와 레포는 수시로 바뀌므로 오래된 내용이 섞여 있을 수 있음.
