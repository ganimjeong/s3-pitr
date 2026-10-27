# 서울 공고 분석

조사 시점 서울 공고는 7건이고 전부 `Clumio - R&D` 소속임. 신입이 지원할 수 있는 건 아래 두 개.

## Software Engineer - Automation [공개]

- "신입이나 초년차 엔지니어에게 좋은 기회"라고 적혀 있음
- 하는 일
  - 시험 자동화 틀과 도구 설계
  - 시험을 돌릴 인프라(저장소, 컴퓨팅, 네트워크) 구성
  - 처음부터 끝까지 이어지는 통합 시험, 부하·스트레스 시험
  - 고객 환경을 흉내 내는 AWS 인프라를 Python으로 만들고 다룸 (EC2, RDS, DynamoDB, S3, Cognito, SQS, SNS, VPC, CloudFormation, Lambda, Kubernetes, Docker)
  - 대규모 환경을 만드는 데이터 생성 도구, REST API 라이브러리
  - Customer Success와 고객 문제 해결
- 필수: Python이나 Go 같은 객체지향 언어 기초, 컴퓨터공학 학사, 품질에 대한 열정, 영어
- 우대: 퍼블릭 클라우드, Docker·Kubernetes, 시험 자동화나 백엔드 경험
- 팀이 에이전트형 AI 코딩 도구를 쓰고, 고객용 AI 에이전트도 만들고 있다고 적혀 있음

## Software Engineer - Backend [공개]

- Senior, Principal 지도 아래 기능을 만들고 시험을 쓰고 출시 후 운영까지 함
- 필수: 자료구조, 알고리즘, 복잡도 기초. Go, Java, Python, C++, Rust 중 하나. 요구가 모호하면 질문하는 습관
- 우대: 객체 저장소, 데이터 집약 시스템, 백업·재해 복구 경험

## 예전 서울 QA 자동화 공고 [공개]

QE팀이 이미 만든 것으로 EC2, RDS, S3, Lambda, SQS용 AWS 인프라 라이브러리, REST API 라이브러리, 백업·복구 시험용 데이터 생성 도구를 꼽음. 지금 Automation 공고의 업무와 거의 같음.

## 공고 문장과 이 레포의 대응

| 공고 문장 | 이 레포에서 만드는 것 |
| --- | --- |
| data-generation tools to set up scale environments | `s3pitr.datagen`: 객체 수, 크기 분포, 접두어 깊이, 덮어쓰기·삭제 비율을 정해서 시험 데이터를 만듦. 같은 시드면 같은 결과 |
| automation to manipulate AWS infrastructure that simulates customer environments | `s3pitr.envkit`: 버전 관리 버킷, 금고 버킷, 카탈로그 테이블을 만들고 지움 |
| handle and recover from failures through reprocessing and retries | 카탈로그 조건부 쓰기로 같은 버전을 두 번 처리하지 않음. 중간에 끊긴 백업을 다시 돌리면 남은 것만 처리함 |
| end-to-end integration tests and load/stress tests | `e2e/`: 백업 → 데이터 변경 → 시점 복구 → 체크섬 비교. 부하 시험은 객체 수를 늘려 처리량을 잼 |
| REST API libraries | 확장 단계 |
| multi-cloud across GCP and Azure | 확장 단계: GCS로 복구 |

## 범위 밖

- 웹 화면: 공고에 요구가 없음
- Azure: GCP 하나만 확장함
- Kubernetes: 우대 사항이지만 이 레포의 문제와 맞지 않음. 억지로 넣지 않음

## 출처

- Software Engineer - Automation https://job-boards.greenhouse.io/commvault/jobs/5349236008
- Software Engineer - Backend https://job-boards.greenhouse.io/commvault/jobs/5349251008
- 예전 서울 QA 자동화 공고 https://dev-korea.com/jobs/clumio-software-engineer-qa-automation
