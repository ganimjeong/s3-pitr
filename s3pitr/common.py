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

"""백업, 복구, 검증이 같이 쓰는 상수와 AWS 클라이언트 설정."""

from __future__ import annotations

import datetime
import logging
from typing import TYPE_CHECKING, Final

import boto3
from botocore import config

if TYPE_CHECKING:
    from mypy_boto3_dynamodb import service_resource as dynamodb_resource
    from mypy_boto3_s3 import client as s3_client

ISO_8601_FORMAT: Final = '%Y-%m-%dT%H:%M:%S.%fZ'
MAX_ATTEMPTS: Final = 8
# 백업본이 저장되는 키 앞부분. 원본 버킷 이름을 그대로 넣어서 여러 버킷을 한 금고에 모음.
VAULT_PREFIX: Final = 'vault'

logger = logging.getLogger(__name__)


class Error(Exception):
    """이 패키지의 기본 예외."""


def client_config() -> config.Config:
    """모든 boto3 클라이언트가 쓰는 재시도 설정을 만듦.

    재시도는 botocore에만 맡기고 그 위에 직접 재시도를 또 감싸지 않음.
    두 겹으로 감싸면 시도 횟수가 곱해져서 스로틀링 때 요청이 오히려 늘어남.
    adaptive 모드는 429, SlowDown 응답을 보면 클라이언트 쪽 요청 속도도 같이 낮춤.
    """
    return config.Config(
        retries={'mode': 'adaptive', 'max_attempts': MAX_ATTEMPTS},
        connect_timeout=5,
        read_timeout=60,
    )


def s3() -> s3_client.S3Client:
    """S3 클라이언트를 만듦. 엔드포인트는 AWS_ENDPOINT_URL 환경 변수를 boto3가 직접 읽음."""
    return boto3.client('s3', config=client_config())


def dynamodb() -> dynamodb_resource.DynamoDBServiceResource:
    """DynamoDB 리소스를 만듦."""
    return boto3.resource('dynamodb', config=client_config())


def to_iso(value: datetime.datetime) -> str:
    """UTC 시각을 카탈로그 정렬 키에 쓰는 고정 길이 문자열로 바꿈.

    문자열 정렬 순서와 시간 순서가 같아야 해서 마이크로초까지 자리를 고정함.
    """
    if value.tzinfo is None:
        raise Error(f'시간대가 없는 시각은 받지 않음: {value!r}')
    return value.astimezone(datetime.UTC).strftime(ISO_8601_FORMAT)


def from_iso(value: str) -> datetime.datetime:
    """to_iso로 만든 문자열을 UTC 시각으로 되돌림."""
    return datetime.datetime.strptime(value, ISO_8601_FORMAT).replace(tzinfo=datetime.UTC)
