# Commvault, Clumio

## Commvault [공개]

- 나스닥 상장(CVLT). 채용 공고 첫 문단에서 스스로를 "AI 시대의 지속적인 복구(continuous recovery)" 회사라고 소개함
  > returning critical data, applications, identities, and AI systems to a clean, trusted state
- 백업보다 복구, 그리고 "깨끗하고 믿을 수 있는 상태로 되돌리기"를 앞에 둠. 이 레포도 백업보다 복구와 복구 검증을 중심에 둔 이유임
- 2026 회계연도(2026-03 마감) 매출 11.8억 달러(19% 증가), SaaS ARR 4억 달러(42% 증가). SaaS가 가장 빨리 크는 사업임
- 인수: Clumio(2024-10-01, 자산 인수), Appranix(클라우드 앱 복구), Satori Cyber(2025-08-28, 데이터·AI 보안)
- 공개 레포: Python SDK(`cvpysdk`), Terraform 공급자, Helm 차트, MCP 서버 2개(`commvault-mcp-server`, `commvault-k8s-devops-mcp`)

## Clumio [공개]

- 2017년 설립한 AWS 전용 SaaS 데이터 보호 회사. 인수 후 표기는 "Clumio, a Commvault Company"
- 보호 대상: S3, DynamoDB, EC2·EBS, RDS, Apache Iceberg
- 공고가 내세우는 수치: AWS 기본 백업 대비 복구 최대 10배 빠름, S3 비용 약 절반, 훨씬 큰 데이터 규모
- 플랫폼은 S3와 DynamoDB 위에 있고, 실패는 재처리와 재시도로 견디면서 정확성을 지킴
- 지금 GCP, Azure로 넓히는 중. `terraform-clumio-gcp-template`이 조사 시점에 가장 최근에 고쳐진 레포였음

## Clumio 구조 [공개, 2차 자료]

- Lambda 기반의 상태 없는 처리 파이프라인. 버킷 변경을 이벤트로 계속 잡아서 운영 워크로드를 건드리지 않음 (Commvault 블로그)
- 백업 데이터와 메타데이터는 고객 계정이 아닌 Clumio 쪽 별도 계정에 암호화해서 둠 (공기 차단)
- `bulk_restore` 레포의 구조: Step Functions 상태 기계가 Lambda를 부르고, 대량 처리는 분산 Map으로 나눔. 오래 걸리는 복구는 Lambda가 예외를 던지고 상태 기계의 Retry가 다시 부름

## 서울 조직 [공개]

- 공고의 부서 이름은 `Clumio - R&D`, 근무지 Seoul
- 하이브리드 근무, 한국어 불필요, 영어 업무 능력 필수, 비자 지원 없음
- 공개 레포 커밋 작성자에 한국 이름이 많음. 서울 팀원이 공개 레포를 직접 관리하는 것으로 보임 [추정]

## 이 레포에 반영한 것

- 복구와 복구 검증을 가장 앞에 둠
- 실패해도 결과가 맞아야 한다는 요구를 설계와 시험의 기준으로 씀
- 레포 이름, 문서에 회사 상표(Clumio, Commvault, Backtrack, SecureVault)를 제품 이름처럼 쓰지 않음. 조사 문서에서 출처로만 씀

## 출처

- Software Engineer - Automation https://job-boards.greenhouse.io/commvault/jobs/5349236008
- Commvault 10-K (FY2025) https://www.sec.gov/Archives/edgar/data/1169561/000116956125000034/cvlt-20250331.htm
- Commvault FY26 실적 https://www.storagenewsletter.com/2026/05/05/commvault-fiscal-4q26-and-fy26-financial-results/
- Commvault의 S3 보호 설명 https://www.commvault.com/blogs/protecting-your-amazon-s3-data-with-clumio-a-comprehensive-solution
- clumio-code GitHub https://github.com/clumio-code
- Commvault GitHub https://github.com/Commvault
