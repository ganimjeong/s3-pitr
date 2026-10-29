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
"""catalog 모듈 단위 시험."""

from __future__ import annotations

import unittest

from s3pitr import catalog
from s3pitr.test import aws_case


def _entry(key: str = 'a.txt', version_id: str = 'v1') -> catalog.Entry:
    return catalog.Entry(
        bucket=aws_case.SOURCE,
        key=key,
        version_id=version_id,
        last_modified='2026-10-30T00:00:00.000000Z',
        is_delete_marker=False,
        size=5,
        checksum_sha256='abc=',
        vault_key='vault/source-bucket/a.txt/v1',
    )


class TestCatalog(aws_case.AwsTestCase):
    """카탈로그 기록과 조회 시험."""

    def test_put_returns_false_for_same_version(self) -> None:
        """같은 버전을 두 번 기록하면 두 번째는 False이고 항목은 하나임."""
        self.assertTrue(self.catalog.put(_entry()))
        self.assertFalse(self.catalog.put(_entry()))
        self.assertEqual(len(list(self.catalog.entries(aws_case.SOURCE))), 1)

    def test_entries_round_trip_all_fields(self) -> None:
        """기록한 값이 그대로 돌아옴. 숫자는 Decimal이 아니라 int임."""
        self.catalog.put(_entry())
        [entry] = self.catalog.entries(aws_case.SOURCE)
        self.assertEqual(entry, _entry())
        self.assertIsInstance(entry.size, int)

    def test_entries_paginates_past_one_page(self) -> None:
        """한 번의 Query 응답(1MB)을 넘어도 전부 돌려줌."""
        long_key = 'k' * 900
        for n in range(1200):
            self.catalog.put(_entry(key=f'{long_key}{n:04d}', version_id='v'))
        self.assertEqual(len(list(self.catalog.entries(aws_case.SOURCE))), 1200)

    def test_delete_marker_without_optional_fields(self) -> None:
        """체크섬과 금고 위치가 없는 삭제 표시도 기록하고 읽을 수 있음."""
        marker = catalog.Entry(
            bucket=aws_case.SOURCE,
            key='a.txt',
            version_id='m1',
            last_modified='2026-10-30T00:00:00.000000Z',
            is_delete_marker=True,
        )
        self.catalog.put(marker)
        self.assertEqual(list(self.catalog.entries(aws_case.SOURCE)), [marker])


if __name__ == '__main__':
    unittest.main()
