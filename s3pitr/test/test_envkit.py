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
"""envkit 모듈 단위 시험."""

from __future__ import annotations

import unittest

import boto3

from s3pitr import common, envkit
from s3pitr.test import aws_case


class TestEnvkit(aws_case.AwsTestCase):
    """시험 환경 도구 시험."""

    def test_create_bucket_outside_us_east_1_sets_location(self) -> None:
        """us-east-1이 아닌 리전에서는 LocationConstraint를 붙여서 만듦."""
        seoul = boto3.client('s3', region_name='ap-northeast-2', config=common.client_config())
        envkit.create_bucket(seoul, 'seoul-bucket')
        location = seoul.get_bucket_location(Bucket='seoul-bucket')['LocationConstraint']
        self.assertEqual(location, 'ap-northeast-2')

    def test_empty_bucket_removes_versions_and_delete_markers(self) -> None:
        """버전 관리 버킷에서 이전 버전과 삭제 표시까지 남김없이 지움."""
        self.put('a.txt', b'one')
        self.put('a.txt', b'two')
        self.s3.delete_object(Bucket=aws_case.SOURCE, Key='a.txt')
        envkit.empty_bucket(self.s3, aws_case.SOURCE)
        response = self.s3.list_object_versions(Bucket=aws_case.SOURCE)
        self.assertEqual(response.get('Versions', []) + response.get('DeleteMarkers', []), [])


if __name__ == '__main__':
    unittest.main()
