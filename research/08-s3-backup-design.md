# S3 백업 설계에 필요한 사실

## S3 동작 [공개]

- 버전 관리를 켠 버킷은 덮어쓸 때마다 새 버전 ID가 생기고, 삭제하면 지우지 않고 삭제 표시(delete marker)를 남김
- `ListObjectVersions`는 키 순서로, 같은 키 안에서는 최신 버전부터 돌려줌. 한 번에 최대 1,000개라 페이지를 넘겨야 함
- `CopyObject`는 한 번에 5GB까지. 더 크면 `UploadPartCopy`로 나눠서 복사해야 함
- `CopyObject`에 `ChecksumAlgorithm`을 주면 S3가 복사한 객체의 체크섬을 계산해서 저장함. 지원 알고리즘: CRC32, CRC32C, CRC64NVME, SHA1, SHA256
- 2024년 말부터 S3는 새로 올리는 객체에 기본으로 CRC 체크섬을 붙임
- Object Lock 규정 준수(compliance) 모드는 보존 기간 동안 루트 계정도 지우지 못함. 버전 관리가 켜진 버킷에서만 씀
- ETag는 멀티파트 업로드면 내용의 MD5가 아니라서 내용 비교에 쓸 수 없음

## 변경분을 찾는 세 가지 방법 [공개]

| 방법 | 지연 | 비용 | 정확성 |
| --- | --- | --- | --- |
| `ListObjectVersions` 전체 비교 | 백업 주기만큼 | 객체 수에 비례하는 LIST 요청 | 실행 시점 상태를 정확히 봄 |
| S3 이벤트 알림 → SQS | 거의 실시간 | 변경 수에 비례 | 이벤트가 늦거나 중복될 수 있어서 멱등 처리 필요 |
| S3 Inventory | 하루 또는 일주일 | 가장 쌈 | 보고서 생성 시점 기준 |

## 이 레포의 결정

- 첫 버전은 `ListObjectVersions` 비교. 가장 단순하고, 다른 두 방식의 정답지로 쓸 수 있음
- 이벤트 방식은 확장 단계. 이벤트 중복을 카탈로그의 조건부 쓰기로 막는 구조라서 첫 버전의 카탈로그 설계를 그대로 씀
- 복구 검증은 ETag가 아니라 SHA256 체크섬으로 함
- 금고 버킷은 같은 계정의 별도 버킷 + Object Lock으로 대신함. 실제로는 별도 계정이어야 한다는 점을 설계 문서에 적음

## 출처

- 버전 관리 https://docs.aws.amazon.com/AmazonS3/latest/userguide/Versioning.html
- ListObjectVersions https://docs.aws.amazon.com/AmazonS3/latest/API/API_ListObjectVersions.html
- CopyObject https://docs.aws.amazon.com/AmazonS3/latest/API/API_CopyObject.html
- 체크섬 https://docs.aws.amazon.com/AmazonS3/latest/userguide/checking-object-integrity.html
- Object Lock https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lock.html
- 이벤트 알림 https://docs.aws.amazon.com/AmazonS3/latest/userguide/EventNotifications.html
- S3 Inventory https://docs.aws.amazon.com/AmazonS3/latest/userguide/storage-inventory.html
