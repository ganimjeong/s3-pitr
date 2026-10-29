# S3 Point-in-Time Restore

> [!IMPORTANT]
> 개인 학습 프로젝트이며 Commvault, Clumio와 관계없음.
> Copyright 2026 Ajin Jeong. Apache License 2.0으로 배포함. 전문은 [LICENSE](LICENSE) 참고.

S3 버킷을 증분 백업하고 원하는 시점의 상태로 복구하는 도구, 그리고 그 복구가 맞는지 대규모로 확인하는 시험 자동화.

## 무엇을 하나

- 백업: 버전 관리가 켜진 원본 버킷에서 아직 백업하지 않은 버전만 금고 버킷으로 복사하고, 무엇을 언제 복사했는지 DynamoDB 카탈로그에 남김
- 시점 복구: 시각을 주면 그 시각에 원본 버킷에 있었던 객체만 골라 대상 버킷에 되살림. 그 뒤에 지워진 객체도 돌아오고, 그 뒤에 생긴 객체는 빠짐
- 검증: 복구한 객체의 SHA256 체크섬을 백업 당시 값과 비교함
- 시험 데이터 생성: 객체 수, 크기 분포, 덮어쓰기와 삭제 비율을 정해서 시험용 버킷을 채움

## 구조

```
s3pitr/
  common.py     AWS 클라이언트 재시도 설정, 시각 문자열, 공통 예외
  catalog.py    DynamoDB 백업 카탈로그. 조건부 쓰기로 같은 버전을 한 번만 기록
  backup.py     증분 백업. 새 버전만 금고로 복사하고 체크섬과 함께 기록
  envkit.py     시험용 버킷, 카탈로그 테이블 만들기와 정리
  restore.py    시점 복구. 그 시각의 상태를 골라 빈 버킷에 되살림
  verify.py     복구 검증. SHA256 비교, 빠진 객체와 남는 객체 찾기
  __main__.py   명령줄 도구
  test/         단위 시험 (unittest + green)
e2e/            통합 시험 (pytest, moto 서버)
research/       구조와 규칙을 정할 때 참고한 자료
til/            만들면서 배운 것과 시행착오 회고
```

## 시작하기

Python 3.12가 필요함.

```sh
python3.12 -m venv .venv
source .venv/bin/activate
make install-dev
pre-commit install -t pre-commit -t pre-push
```

## 쓰는 법

카탈로그 테이블과 버킷은 미리 있어야 함. 원본 버킷은 버전 관리가 켜져 있어야 함.

```sh
# 새 버전만 금고로 복사
python -m s3pitr --table s3pitr-catalog backup --source my-data --vault my-vault

# 그 시각의 상태를 빈 버킷에 되살리고 검증. 검증이 실패하면 종료 코드 1
python -m s3pitr --table s3pitr-catalog restore \
  --source my-data --vault my-vault --target my-restore --at 2026-10-30T09:00:00+09:00

# 복구한 버킷을 다시 검증만
python -m s3pitr --table s3pitr-catalog verify \
  --source my-data --target my-restore --at 2026-10-30T09:00:00+09:00
```

- 시각에는 시간대를 꼭 붙임. 없으면 거부함
- 복구는 원본이 아닌 빈 버킷으로만 함
- 같은 초에 덮어쓰기와 삭제가 겹친 키가 있으면 순서를 알 수 없어서 멈춤. 1초 앞이나 뒤 시각으로 다시 하면 됨
- 5GB가 넘는 객체는 아직 지원하지 않음

## 자주 쓰는 명령

| 명령                | 설명                                       |
| ------------------- | ------------------------------------------ |
| `make test`         | 단위 시험과 커버리지 보고서                |
| `make e2e`          | 통합 시험                                  |
| `make lint`         | Ruff 린트                                  |
| `make format`       | Ruff 포맷                                  |
| `make format-check` | 포맷 검사만                                |
| `make mypy`         | 타입 검사                                  |
| `make clean`        | 빌드 결과 지우기                           |

## 문서

- [기여 가이드](CONTRIBUTING.md)
- [조사 자료](research/README.md)
- [회고](til/README.md)
