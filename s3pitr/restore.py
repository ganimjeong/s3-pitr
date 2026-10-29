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

"""시점 복구. 카탈로그에서 그 시각의 상태를 골라 빈 버킷에 되살림."""

from __future__ import annotations

import collections
import dataclasses
import datetime
import logging
from collections.abc import Iterable
from typing import TYPE_CHECKING

from s3pitr import catalog, common

if TYPE_CHECKING:
    from mypy_boto3_s3 import client as s3_client

logger = logging.getLogger(__name__)


class Error(common.Error):
    """복구 예외."""


class AmbiguousRestorePointError(Error):
    """같은 초에 생긴 기록 중 무엇이 나중인지 알 수 없는 키가 있음."""

    def __init__(self, keys: list[str]) -> None:
        super().__init__(f'같은 초에 생긴 기록의 순서를 알 수 없는 키 {len(keys)}개: {keys[:5]}')
        self.keys = keys


@dataclasses.dataclass(frozen=True)
class RestorePlan:
    """복구 시각과 그 시각에 있던 객체들. 키마다 되살릴 버전 하나."""

    at: str
    objects: dict[str, catalog.Entry]


def plan_restore(
    entries: Iterable[catalog.Entry],
    at: datetime.datetime,
    prefix: str = '',
) -> RestorePlan:
    """그 시각에 원본 버킷에 있던 객체를 고름.

    키마다 그 시각 이전의 마지막 기록을 찾음. 마지막 기록이 삭제 표시면 그 시각에는
    없던 객체라 뺌. S3 LastModified는 초 단위이고, boto3는 버전과 삭제 표시를 따로
    나눠 돌려줘서 같은 초 안의 순서를 알 수 없음. 그런 키가 있으면 추측하지 않고 멈춤.
    """
    point = common.to_iso(at)
    latest: dict[str, list[catalog.Entry]] = collections.defaultdict(list)
    for entry in entries:
        if not entry.key.startswith(prefix) or entry.last_modified > point:
            continue
        current = latest[entry.key]
        if not current or entry.last_modified > current[0].last_modified:
            latest[entry.key] = [entry]
        elif entry.last_modified == current[0].last_modified:
            current.append(entry)

    ambiguous = sorted(key for key, tied in latest.items() if len(tied) > 1)
    if ambiguous:
        raise AmbiguousRestorePointError(ambiguous)

    objects = {key: tied[0] for key, tied in latest.items() if not tied[0].is_delete_marker}
    return RestorePlan(at=point, objects=objects)


def run_restore(
    s3: s3_client.S3Client,
    plan: RestorePlan,
    vault_bucket: str,
    target_bucket: str,
    source_bucket: str,
) -> int:
    """계획한 객체를 금고에서 대상 버킷으로 복사하고 복사한 개수를 돌려줌."""
    if target_bucket == source_bucket:
        # 원본에 덮어쓰면 복구가 잘못됐을 때 되돌릴 곳이 없음. 원본에는 읽기만 함.
        raise Error('원본 버킷으로는 복구하지 않음. 빈 버킷을 따로 정해야 함')
    if s3.list_objects_v2(Bucket=target_bucket, MaxKeys=1).get('KeyCount', 0):
        # 원래 있던 객체와 복구한 객체가 섞이면 검증에서 남는 객체를 구분할 수 없음.
        raise Error(f'대상 버킷이 비어 있지 않음: {target_bucket}')

    for key, entry in sorted(plan.objects.items()):
        if entry.vault_key is None:
            raise Error(f'금고 위치가 없는 기록: {key} {entry.version_id}')
        s3.copy_object(
            CopySource={'Bucket': vault_bucket, 'Key': entry.vault_key},
            Bucket=target_bucket,
            Key=key,
            ChecksumAlgorithm='SHA256',
        )
    logger.info(
        '복구 완료 %s → %s: %d개 (%s 기준)',
        source_bucket,
        target_bucket,
        len(plan.objects),
        plan.at,
    )
    return len(plan.objects)
