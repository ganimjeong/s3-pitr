# CHANGELOG

## 0.1.0 (개발 중)
이번 버전의 변경 사항:
* 추가: 저장소 기본 설정(Ruff, mypy, green, pre-commit, GitHub Actions).
* 추가: AWS 클라이언트 재시도 설정과 정렬 가능한 UTC 시각 문자열.
* 갱신: GitHub Actions(checkout, setup-python, upload-artifact)를 v7로 올림.
* 추가: 증분 백업. 원본 버킷에서 아직 백업하지 않은 버전만 금고 버킷으로 복사하고 SHA256 체크섬과 함께 DynamoDB 카탈로그에 기록함.
* 추가: 삭제 표시 기록, 같은 버전 중복 기록 방지(조건부 쓰기).
* 추가: 시험 환경 도구(버킷, 카탈로그 테이블 생성과 정리).
