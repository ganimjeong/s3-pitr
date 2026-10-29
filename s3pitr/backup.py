# Copyright 2026 Ajin Jeong.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""증분 백업. 원본 버킷에서 아직 카탈로그에 없는 버전만 금고 버킷으로 복사함."""

from __future__ import annotations

import dataclasses
import logging
from typing import TYPE_CHECKING, Final

from s3pitr import catalog, common

if TYPE_CHECKING:
    from mypy_boto3_s3 import client as s3_client

# CopyObject 한 번으로 복사할 수 있는 최대 크기. 넘으면 UploadPartCopy로 나눠야 함.
MAX_SINGLE_COPY_BYTES: Final = 5 * 1024**3

logger = logging.getLogger(__name__)


class Error(common.Error):
    """백업 예외."""


@dataclasses.dataclass
class BackupResult:
    """백업 한 번의 결과."""

    copied: int = 0
    delete_markers: int = 0
    skipped: int = 0


def vault_key(bucket: str, key: str, version_id: str) -> str:
    """금고 버킷 안의 위치. 같은 버전은 항상 같은 위치라 다시 복사해도 덮어쓸 뿐임."""
    return f'{common.VAULT_PREFIX}/{bucket}/{key}/{version_id}'


def run_backup(
    s3: s3_client.S3Client,
    backup_catalog: catalog.Catalog,
    source_bucket: str,
    vault_bucket: str,
    prefix: str = '',
) -> BackupResult:
    """원본 버킷의 새 버전과 새 삭제 표시를 금고와 카탈로그에 옮김.

    몇 번을 다시 돌려도 결과가 같음. 이미 카탈로그에 있는 버전은 건너뜀.
    """
    versioning = s3.get_bucket_versioning(Bucket=source_bucket)
    if versioning.get('Status') != 'Enabled':
        # 버전 관리가 꺼져 있으면 덮어쓴 이전 내용이 남지 않아 시점 복구를 할 수 없음.
        raise Error(f'원본 버킷의 버전 관리가 켜져 있지 않음: {source_bucket}')

    known = {entry.sort_key for entry in backup_catalog.entries(source_bucket)}
    result = BackupResult()
    paginator = s3.get_paginator('list_object_versions')
    for page in paginator.paginate(Bucket=source_bucket, Prefix=prefix):
        for version in page.get('Versions', []):
            entry = catalog.Entry(
                bucket=source_bucket,
                key=version['Key'],
                version_id=version['VersionId'],
                last_modified=common.to_iso(version['LastModified']),
                is_delete_marker=False,
                size=version['Size'],
            )
            if entry.sort_key in known:
                result.skipped += 1
                continue
            if _copy_and_record(s3, backup_catalog, entry, vault_bucket):
                result.copied += 1
            else:
                result.skipped += 1

        for marker in page.get('DeleteMarkers', []):
            entry = catalog.Entry(
                bucket=source_bucket,
                key=marker['Key'],
                version_id=marker['VersionId'],
                last_modified=common.to_iso(marker['LastModified']),
                is_delete_marker=True,
            )
            if entry.sort_key in known:
                result.skipped += 1
            elif backup_catalog.put(entry):
                result.delete_markers += 1
            else:
                result.skipped += 1

    logger.info(
        '백업 완료 %s: 복사 %d, 삭제 표시 %d, 건너뜀 %d',
        source_bucket,
        result.copied,
        result.delete_markers,
        result.skipped,
    )
    return result


def _copy_and_record(
    s3: s3_client.S3Client,
    backup_catalog: catalog.Catalog,
    entry: catalog.Entry,
    vault_bucket: str,
) -> bool:
    """버전 하나를 금고에 복사한 뒤 카탈로그에 기록함.

    순서는 복사가 먼저임. 기록을 먼저 하면 그 사이에 멈췄을 때 금고에 없는 백업이
    카탈로그에 남고, 복구할 때에야 드러남. 복사가 먼저면 멈춰도 다음 실행이 같은
    위치에 다시 복사하고 기록하므로 남는 건 덮어쓸 파일뿐임.
    """
    if entry.size > MAX_SINGLE_COPY_BYTES:
        raise Error(f'5GB를 넘는 객체는 아직 지원하지 않음: {entry.key} ({entry.size} bytes)')

    destination = vault_key(entry.bucket, entry.key, entry.version_id)
    response = s3.copy_object(
        CopySource={'Bucket': entry.bucket, 'Key': entry.key, 'VersionId': entry.version_id},
        Bucket=vault_bucket,
        Key=destination,
        # 복구 검증은 ETag가 아니라 이 값으로 함. 멀티파트로 올린 객체의 ETag는 내용의 MD5가 아님.
        ChecksumAlgorithm='SHA256',
    )
    checksum = response['CopyObjectResult'].get('ChecksumSHA256')
    if checksum is None:
        raise Error(f'S3가 체크섬을 돌려주지 않음: {entry.key}')
    recorded = dataclasses.replace(entry, checksum_sha256=checksum, vault_key=destination)
    return backup_catalog.put(recorded)
