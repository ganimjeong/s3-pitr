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

"""시험과 시연에 쓰는 버킷, 카탈로그 테이블을 만들고 지움."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, cast

from s3pitr import catalog

if TYPE_CHECKING:
    from mypy_boto3_dynamodb import service_resource
    from mypy_boto3_s3 import client as s3_client
    from mypy_boto3_s3 import literals as s3_literals
    from mypy_boto3_s3 import type_defs as s3_type_defs

logger = logging.getLogger(__name__)


def create_bucket(s3: s3_client.S3Client, name: str, *, versioned: bool = False) -> None:
    """버킷을 만듦. us-east-1은 LocationConstraint를 주면 오히려 거부하므로 리전에 따라 나눔."""
    region = s3.meta.region_name
    if region == 'us-east-1':
        s3.create_bucket(Bucket=name)
    else:
        # 스텁은 리전 이름을 Literal로만 받음. 클라이언트 리전은 실행 시점에야 알 수 있음.
        constraint = cast('s3_literals.BucketLocationConstraintType', region)
        s3.create_bucket(Bucket=name, CreateBucketConfiguration={'LocationConstraint': constraint})
    if versioned:
        s3.put_bucket_versioning(Bucket=name, VersioningConfiguration={'Status': 'Enabled'})
    logger.info('버킷 생성: %s (버전 관리 %s)', name, versioned)


def create_catalog_table(
    dynamodb: service_resource.DynamoDBServiceResource,
    name: str,
) -> service_resource.Table:
    """카탈로그 테이블을 만들고 쓸 수 있을 때까지 기다림."""
    table = dynamodb.create_table(
        TableName=name,
        KeySchema=[
            {'AttributeName': catalog.PARTITION_KEY, 'KeyType': 'HASH'},
            {'AttributeName': catalog.SORT_KEY, 'KeyType': 'RANGE'},
        ],
        AttributeDefinitions=[
            {'AttributeName': catalog.PARTITION_KEY, 'AttributeType': 'S'},
            {'AttributeName': catalog.SORT_KEY, 'AttributeType': 'S'},
        ],
        BillingMode='PAY_PER_REQUEST',
    )
    table.wait_until_exists()
    logger.info('카탈로그 테이블 생성: %s', name)
    return table


def empty_bucket(s3: s3_client.S3Client, name: str) -> None:
    """버전과 삭제 표시까지 전부 지움. 시험 정리용."""
    paginator = s3.get_paginator('list_object_versions')
    for page in paginator.paginate(Bucket=name):
        targets: list[s3_type_defs.ObjectIdentifierTypeDef] = [
            {'Key': item['Key'], 'VersionId': item['VersionId']}
            for item in page.get('Versions', []) + page.get('DeleteMarkers', [])
        ]
        if targets:
            s3.delete_objects(Bucket=name, Delete={'Objects': targets, 'Quiet': True})
