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

"""백업 카탈로그. 어떤 객체 버전을 언제 금고로 옮겼는지 DynamoDB에 남김."""

from __future__ import annotations

import dataclasses
import logging
from collections.abc import Iterator
from typing import TYPE_CHECKING, Any, Final

from boto3.dynamodb import conditions
from botocore import exceptions

from s3pitr import common

if TYPE_CHECKING:
    from mypy_boto3_dynamodb import service_resource

PARTITION_KEY: Final = 'bucket'
SORT_KEY: Final = 'object_version'
# 키와 버전 ID 사이 구분자. S3 버전 ID에는 나오지 않는 문자라 정렬 키가 겹치지 않음.
SEPARATOR: Final = '\x00'

logger = logging.getLogger(__name__)


class Error(common.Error):
    """카탈로그 예외."""


@dataclasses.dataclass(frozen=True)
class Entry:
    """원본 버킷의 객체 버전 하나 또는 삭제 표시 하나."""

    bucket: str
    key: str
    version_id: str
    # common.to_iso 형식. 문자열 비교가 곧 시간 비교가 되게 함.
    last_modified: str
    is_delete_marker: bool
    size: int = 0
    checksum_sha256: str | None = None
    vault_key: str | None = None

    @property
    def sort_key(self) -> str:
        """카탈로그 정렬 키."""
        return f'{self.key}{SEPARATOR}{self.version_id}'

    def to_item(self) -> dict[str, Any]:
        """DynamoDB 항목으로 바꿈. 값이 없는 속성은 넣지 않음."""
        item: dict[str, Any] = {
            PARTITION_KEY: self.bucket,
            SORT_KEY: self.sort_key,
            'key': self.key,
            'version_id': self.version_id,
            'last_modified': self.last_modified,
            'is_delete_marker': self.is_delete_marker,
            'size': self.size,
        }
        if self.checksum_sha256 is not None:
            item['checksum_sha256'] = self.checksum_sha256
        if self.vault_key is not None:
            item['vault_key'] = self.vault_key
        return item

    @classmethod
    def from_item(cls, item: dict[str, Any]) -> Entry:
        """DynamoDB 항목을 Entry로 되돌림. 숫자는 Decimal로 오므로 int로 바꿈."""
        return cls(
            bucket=str(item[PARTITION_KEY]),
            key=str(item['key']),
            version_id=str(item['version_id']),
            last_modified=str(item['last_modified']),
            is_delete_marker=bool(item['is_delete_marker']),
            size=int(item.get('size', 0)),
            checksum_sha256=item.get('checksum_sha256'),
            vault_key=item.get('vault_key'),
        )


class Catalog:
    """백업 카탈로그 테이블 하나를 감쌈."""

    def __init__(self, table: service_resource.Table) -> None:
        self._table = table

    def put(self, entry: Entry) -> bool:
        """처음 기록했으면 True, 이미 같은 버전이 있으면 False를 돌려줌.

        같은 백업을 두 번 돌리거나 두 실행이 겹쳐도 한 버전은 한 번만 기록됨.
        """
        try:
            self._table.put_item(
                Item=entry.to_item(),
                ConditionExpression='attribute_not_exists(#sk)',
                ExpressionAttributeNames={'#sk': SORT_KEY},
            )
        except exceptions.ClientError as error:
            if error.response['Error']['Code'] == 'ConditionalCheckFailedException':
                return False
            raise
        return True

    def entries(self, bucket: str) -> Iterator[Entry]:
        """원본 버킷 하나의 항목을 전부 돌려줌.

        방금 쓴 항목을 놓치면 같은 버전을 다시 복사하므로 강한 일관성 읽기를 씀.
        """
        kwargs: dict[str, Any] = {
            'KeyConditionExpression': conditions.Key(PARTITION_KEY).eq(bucket),
            'ConsistentRead': True,
        }
        while True:
            response = self._table.query(**kwargs)
            for item in response.get('Items', []):
                yield Entry.from_item(item)
            last_key = response.get('LastEvaluatedKey')
            if not last_key:
                return
            kwargs['ExclusiveStartKey'] = last_key
