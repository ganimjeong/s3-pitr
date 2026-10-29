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

"""moto로 가짜 AWS를 띄우는 단위 시험 기반 클래스."""

from __future__ import annotations

import os
import unittest
from typing import Final
from unittest import mock

import moto

from s3pitr import catalog, common, envkit

SOURCE: Final = 'source-bucket'
VAULT: Final = 'vault-bucket'
TARGET: Final = 'restore-bucket'
TABLE: Final = 's3pitr-catalog'


class AwsTestCase(unittest.TestCase):
    """시험마다 빈 가짜 AWS 계정에서 버킷 3개와 카탈로그 테이블을 만들어 둠."""

    def setUp(self) -> None:
        # 실제 자격 증명이 있는 컴퓨터에서도 진짜 계정으로 요청이 나가지 않게 덮어씀.
        env = mock.patch.dict(
            os.environ,
            {
                'AWS_ACCESS_KEY_ID': 'testing',
                'AWS_SECRET_ACCESS_KEY': 'testing',
                'AWS_DEFAULT_REGION': 'us-east-1',
            },
        )
        env.start()
        self.addCleanup(env.stop)
        aws = moto.mock_aws()
        aws.start()
        self.addCleanup(aws.stop)

        self.s3 = common.s3()
        envkit.create_bucket(self.s3, SOURCE, versioned=True)
        envkit.create_bucket(self.s3, VAULT, versioned=True)
        envkit.create_bucket(self.s3, TARGET)
        self.catalog = catalog.Catalog(envkit.create_catalog_table(common.dynamodb(), TABLE))

    def put(self, key: str, body: bytes) -> str:
        """원본 버킷에 객체를 올리고 버전 ID를 돌려줌."""
        return self.s3.put_object(Bucket=SOURCE, Key=key, Body=body)['VersionId']

    def vault_keys(self) -> list[str]:
        """금고 버킷의 키 목록."""
        response = self.s3.list_objects_v2(Bucket=VAULT)
        return sorted(item['Key'] for item in response.get('Contents', []))
