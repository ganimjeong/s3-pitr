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
"""common 모듈 단위 시험."""

from __future__ import annotations

import datetime
import unittest

from s3pitr import common


class TestIsoTimestamps(unittest.TestCase):
    """카탈로그 정렬 키용 시각 문자열 시험."""

    def test_to_iso_keeps_sort_order_equal_to_time_order(self) -> None:
        """문자열 정렬 결과가 시간 순서와 같음."""
        base = datetime.datetime(2026, 10, 27, 9, 0, tzinfo=datetime.UTC)
        times = [base + datetime.timedelta(microseconds=n) for n in (1, 10, 100_000, 999_999)]
        times += [base + datetime.timedelta(days=n) for n in (1, 40, 400)]
        self.assertEqual(sorted(common.to_iso(t) for t in times), [common.to_iso(t) for t in times])

    def test_to_iso_converts_other_timezones_to_utc(self) -> None:
        """서울 시각을 넣어도 UTC 문자열이 나옴."""
        seoul = datetime.timezone(datetime.timedelta(hours=9))
        value = datetime.datetime(2026, 10, 27, 18, 0, tzinfo=seoul)
        self.assertEqual(common.to_iso(value), '2026-10-27T09:00:00.000000Z')

    def test_to_iso_rejects_naive_datetime(self) -> None:
        """시간대가 없으면 어느 시각인지 알 수 없어서 거부함."""
        with self.assertRaises(common.Error):
            common.to_iso(datetime.datetime(2026, 10, 27))

    def test_from_iso_round_trips(self) -> None:
        """to_iso와 from_iso를 거쳐도 같은 시각임."""
        value = datetime.datetime(2026, 1, 2, 3, 4, 5, 678901, tzinfo=datetime.UTC)
        self.assertEqual(common.from_iso(common.to_iso(value)), value)


class TestClientConfig(unittest.TestCase):
    """boto3 재시도 설정 시험."""

    def test_client_config_uses_adaptive_retries(self) -> None:
        """스로틀링 때 요청 속도를 낮추는 adaptive 모드를 씀."""
        # retries는 Config가 생성자 인자로 동적으로 만드는 속성이라 스텁에 없음.
        retries = getattr(common.client_config(), 'retries')
        self.assertEqual(retries, {'mode': 'adaptive', 'max_attempts': common.MAX_ATTEMPTS})


if __name__ == '__main__':
    unittest.main()
