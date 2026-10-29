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
"""명령줄 도구 단위 시험."""

from __future__ import annotations

import contextlib
import io
import unittest

from s3pitr import __main__ as cli
from s3pitr.test import aws_case


class TestMain(aws_case.AwsTestCase):
    """명령 인자와 종료 코드 시험."""

    def _run(self, *args: str) -> int:
        return cli.main(['--table', aws_case.TABLE, *args])

    def test_restore_rejects_time_without_timezone(self) -> None:
        """시간대 없는 시각은 어느 시각인지 몰라서 인자 단계에서 거부함."""
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            self._run('verify', '--source', 's', '--target', 't', '--at', '2026-10-30T09:00:00')

    def test_backup_restore_verify_round_trip(self) -> None:
        """백업, 복구, 검증이 모두 0으로 끝남."""
        self.put('a.txt', b'one')
        self.assertEqual(
            self._run('backup', '--source', aws_case.SOURCE, '--vault', aws_case.VAULT), 0
        )
        common_args = ['--source', aws_case.SOURCE, '--target', aws_case.TARGET]
        at = ['--at', '2100-01-01T00:00:00+00:00']
        self.assertEqual(self._run('restore', *common_args, '--vault', aws_case.VAULT, *at), 0)
        self.assertEqual(self._run('verify', *common_args, *at), 0)


if __name__ == '__main__':
    unittest.main()
