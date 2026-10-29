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

"""복구 검증. 대상 버킷의 객체가 계획과 정확히 같은지 체크섬으로 확인함."""

from __future__ import annotations

import dataclasses
import logging
from typing import TYPE_CHECKING

from s3pitr import restore

if TYPE_CHECKING:
    from mypy_boto3_s3 import client as s3_client

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class VerifyReport:
    """검증 결과. 키 목록은 정렬해서 담음."""

    matched: list[str] = dataclasses.field(default_factory=list)
    mismatched: list[str] = dataclasses.field(default_factory=list)
    missing: list[str] = dataclasses.field(default_factory=list)
    unexpected: list[str] = dataclasses.field(default_factory=list)

    @property
    def ok(self) -> bool:
        """계획과 대상 버킷이 정확히 같으면 True."""
        return not (self.mismatched or self.missing or self.unexpected)


def verify_restore(
    s3: s3_client.S3Client,
    plan: restore.RestorePlan,
    target_bucket: str,
) -> VerifyReport:
    """대상 버킷을 계획과 비교함.

    내용 비교는 ETag가 아니라 SHA256으로 함. 멀티파트로 올린 객체의 ETag는 내용의
    MD5가 아님. 있어야 할 객체가 빠진 것뿐 아니라 없어야 할 객체가 남은 것도 실패로 봄.
    """
    present: set[str] = set()
    paginator = s3.get_paginator('list_objects_v2')
    for page in paginator.paginate(Bucket=target_bucket):
        present.update(item['Key'] for item in page.get('Contents', []))

    report = VerifyReport(unexpected=sorted(present - plan.objects.keys()))
    for key, entry in sorted(plan.objects.items()):
        if key not in present:
            report.missing.append(key)
            continue
        head = s3.head_object(Bucket=target_bucket, Key=key, ChecksumMode='ENABLED')
        if head.get('ChecksumSHA256') == entry.checksum_sha256:
            report.matched.append(key)
        else:
            report.mismatched.append(key)

    logger.info(
        '검증 %s: 일치 %d, 불일치 %d, 빠짐 %d, 남음 %d',
        target_bucket,
        len(report.matched),
        len(report.mismatched),
        len(report.missing),
        len(report.unexpected),
    )
    return report
