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
"""backup 모듈 단위 시험. 실패를 일부러 넣어 다시 돌려도 결과가 같은지 봄."""

from __future__ import annotations

import base64
import hashlib
import unittest
from typing import Any
from unittest import mock

from botocore import awsrequest, compat

from s3pitr import backup, catalog
from s3pitr.test import aws_case


def _sha256(body: bytes) -> str:
    return base64.b64encode(hashlib.sha256(body).digest()).decode()


class _Body:
    """botocore가 응답 본문을 읽을 때 쓰는 stream()만 흉내 냄."""

    def __init__(self, data: bytes) -> None:
        self._data = data

    def stream(self, **_: Any) -> Any:
        yield self._data


class TestRunBackup(aws_case.AwsTestCase):
    """증분 백업 시험."""

    def _backup(self) -> backup.BackupResult:
        return backup.run_backup(self.s3, self.catalog, aws_case.SOURCE, aws_case.VAULT)

    def test_run_backup_copies_every_version_and_records_checksums(self) -> None:
        """덮어쓴 이전 버전까지 전부 금고로 가고 체크섬이 내용과 같음."""
        v1 = self.put('a.txt', b'one')
        v2 = self.put('a.txt', b'two')
        result = self._backup()

        self.assertEqual(result.copied, 2)
        self.assertEqual(
            self.vault_keys(),
            sorted([backup.vault_key(aws_case.SOURCE, 'a.txt', v) for v in (v1, v2)]),
        )
        checksums = {e.version_id: e.checksum_sha256 for e in self.catalog.entries(aws_case.SOURCE)}
        self.assertEqual(checksums, {v1: _sha256(b'one'), v2: _sha256(b'two')})

    def test_run_backup_records_delete_markers_without_copying(self) -> None:
        """삭제 표시는 복사할 내용이 없으니 카탈로그에만 남음."""
        self.put('a.txt', b'one')
        self.s3.delete_object(Bucket=aws_case.SOURCE, Key='a.txt')
        result = self._backup()

        self.assertEqual((result.copied, result.delete_markers), (1, 1))
        markers = [e for e in self.catalog.entries(aws_case.SOURCE) if e.is_delete_marker]
        self.assertEqual(len(markers), 1)
        self.assertIsNone(markers[0].vault_key)

    def test_run_backup_twice_copies_nothing_the_second_time(self) -> None:
        """두 번째 실행은 새 버전이 없으므로 복사도 기록도 하지 않음."""
        self.put('a.txt', b'one')
        self.s3.delete_object(Bucket=aws_case.SOURCE, Key='a.txt')
        self._backup()
        with mock.patch.object(self.s3, 'copy_object', wraps=self.s3.copy_object) as copy:
            result = self._backup()
        copy.assert_not_called()
        self.assertEqual((result.copied, result.delete_markers, result.skipped), (0, 0, 2))

    def test_run_backup_only_copies_new_versions(self) -> None:
        """지난 백업 뒤에 생긴 버전만 복사함."""
        self.put('a.txt', b'one')
        self._backup()
        self.put('a.txt', b'two')
        self.put('b.txt', b'three')
        result = self._backup()
        self.assertEqual((result.copied, result.skipped), (2, 1))

    def test_run_backup_resumes_after_crash_between_copy_and_record(self) -> None:
        """복사 직후 기록 전에 멈춰도 다시 돌리면 빠짐도 겹침도 없음."""
        for n in range(5):
            self.put(f'k{n}', f'body{n}'.encode())
        real_put = self.catalog.put
        calls = {'n': 0}

        def crash_on_third(entry: catalog.Entry) -> bool:
            calls['n'] += 1
            if calls['n'] == 3:
                raise RuntimeError('기록 직전에 프로세스가 죽은 상황')
            return real_put(entry)

        with (
            mock.patch.object(self.catalog, 'put', side_effect=crash_on_third),
            self.assertRaises(RuntimeError),
        ):
            self._backup()
        # 세 번째 객체는 금고에 복사됐지만 카탈로그에는 없는 상태임.
        self.assertEqual(len(self.vault_keys()), 3)
        self.assertEqual(len(list(self.catalog.entries(aws_case.SOURCE))), 2)

        result = self._backup()
        self.assertEqual((result.copied, result.skipped), (3, 2))
        self.assertEqual(len(self.vault_keys()), 5)
        self.assertEqual(len(list(self.catalog.entries(aws_case.SOURCE))), 5)

    def test_run_backup_never_records_a_version_missing_from_vault(self) -> None:
        """복사 도중에 멈춰도 카탈로그의 모든 항목은 금고에 실제 파일이 있음."""
        for n in range(5):
            self.put(f'k{n}', f'body{n}'.encode())
        real_copy = self.s3.copy_object
        calls = {'n': 0}

        def crash_on_third(**kwargs: Any) -> Any:
            calls['n'] += 1
            if calls['n'] == 3:
                raise RuntimeError('복사 중에 프로세스가 죽은 상황')
            return real_copy(**kwargs)

        with (
            mock.patch.object(self.s3, 'copy_object', side_effect=crash_on_third),
            self.assertRaises(RuntimeError),
        ):
            self._backup()
        vault = set(self.vault_keys())
        for entry in self.catalog.entries(aws_case.SOURCE):
            self.assertIn(entry.vault_key, vault)

        self._backup()
        self.assertEqual(len(list(self.catalog.entries(aws_case.SOURCE))), 5)

    def test_run_backup_survives_throttling(self) -> None:
        """CopyObject가 SlowDown(503)을 두 번 받아도 botocore 재시도로 끝까지 감."""
        self.put('a.txt', b'one')
        attempts = {'n': 0}

        def throttle_twice(request: awsrequest.AWSPreparedRequest, **_: Any) -> Any:
            attempts['n'] += 1
            if attempts['n'] > 2:
                return None
            body = b'<Error><Code>SlowDown</Code><Message>Please reduce</Message></Error>'
            return awsrequest.AWSResponse(request.url, 503, compat.HTTPHeaders(), _Body(body))

        # moto도 before-send에서 응답을 만들기 때문에 그보다 먼저 불리게 register_first를 씀.
        self.s3.meta.events.register_first('before-send.s3.CopyObject', throttle_twice)
        with mock.patch('time.sleep'):
            result = self._backup()
        self.assertEqual(result.copied, 1)
        self.assertEqual(attempts['n'], 3)

    def test_run_backup_rejects_unversioned_source(self) -> None:
        """버전 관리가 꺼진 버킷은 덮어쓴 내용이 남지 않으니 시작하지 않음."""
        with self.assertRaises(backup.Error):
            backup.run_backup(self.s3, self.catalog, aws_case.TARGET, aws_case.VAULT)

    def test_run_backup_rejects_objects_over_single_copy_limit(self) -> None:
        """5GB를 넘는 객체는 조용히 건너뛰지 않고 멈춤."""
        self.put('big.bin', b'x')
        with (
            mock.patch.object(backup, 'MAX_SINGLE_COPY_BYTES', 0),
            self.assertRaises(backup.Error),
        ):
            self._backup()


if __name__ == '__main__':
    unittest.main()
