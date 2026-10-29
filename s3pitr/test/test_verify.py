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
"""verify 모듈 단위 시험."""

from __future__ import annotations

import datetime
import unittest

from s3pitr import backup, restore, verify
from s3pitr.test import aws_case

LATER = datetime.datetime(2100, 1, 1, tzinfo=datetime.UTC)


class TestVerifyRestore(aws_case.AwsTestCase):
    """복구 검증 시험."""

    def setUp(self) -> None:
        super().setUp()
        self.put('a.txt', b'one')
        self.put('b.txt', b'two')
        backup.run_backup(self.s3, self.catalog, aws_case.SOURCE, aws_case.VAULT)
        self.plan = restore.plan_restore(self.catalog.entries(aws_case.SOURCE), LATER)
        restore.run_restore(self.s3, self.plan, aws_case.VAULT, aws_case.TARGET, aws_case.SOURCE)

    def test_verify_restore_passes_for_exact_restore(self) -> None:
        """그대로 복구했으면 전부 일치함."""
        report = verify.verify_restore(self.s3, self.plan, aws_case.TARGET)
        self.assertTrue(report.ok)
        self.assertEqual(report.matched, ['a.txt', 'b.txt'])

    def test_verify_restore_catches_changed_content(self) -> None:
        """복구 뒤 내용이 바뀌면 체크섬이 달라서 불일치로 잡음."""
        self.s3.put_object(Bucket=aws_case.TARGET, Key='a.txt', Body=b'tampered')
        report = verify.verify_restore(self.s3, self.plan, aws_case.TARGET)
        self.assertEqual((report.ok, report.mismatched), (False, ['a.txt']))

    def test_verify_restore_catches_missing_and_unexpected(self) -> None:
        """빠진 객체와 계획에 없는 객체를 둘 다 실패로 봄."""
        self.s3.delete_object(Bucket=aws_case.TARGET, Key='b.txt')
        self.s3.put_object(Bucket=aws_case.TARGET, Key='extra.txt', Body=b'x')
        report = verify.verify_restore(self.s3, self.plan, aws_case.TARGET)
        self.assertEqual((report.missing, report.unexpected), (['b.txt'], ['extra.txt']))
        self.assertFalse(report.ok)


if __name__ == '__main__':
    unittest.main()
