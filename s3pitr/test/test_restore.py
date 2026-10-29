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
"""restore 모듈 단위 시험."""

from __future__ import annotations

import datetime
import unittest

import freezegun

from s3pitr import backup, catalog, restore
from s3pitr.test import aws_case

UTC = datetime.UTC
T1 = datetime.datetime(2026, 10, 30, 1, 0, tzinfo=UTC)
T2 = datetime.datetime(2026, 10, 30, 2, 0, tzinfo=UTC)
T3 = datetime.datetime(2026, 10, 30, 3, 0, tzinfo=UTC)


def _entry(key: str, at: str, version_id: str, *, deleted: bool = False) -> catalog.Entry:
    return catalog.Entry(
        bucket=aws_case.SOURCE,
        key=key,
        version_id=version_id,
        last_modified=at,
        is_delete_marker=deleted,
        vault_key=None if deleted else f'vault/{key}/{version_id}',
    )


class TestPlanRestore(unittest.TestCase):
    """복구 계획(순수 함수) 시험."""

    def test_plan_restore_picks_last_version_before_the_point(self) -> None:
        """그 시각 이전의 마지막 버전을 고르고 그 뒤 버전은 무시함."""
        entries = [
            _entry('a', '2026-10-30T01:00:00.000000Z', 'v1'),
            _entry('a', '2026-10-30T02:00:00.000000Z', 'v2'),
            _entry('a', '2026-10-30T03:00:00.000000Z', 'v3'),
        ]
        plan = restore.plan_restore(entries, T2)
        self.assertEqual(plan.objects['a'].version_id, 'v2')

    def test_plan_restore_includes_versions_exactly_at_the_point(self) -> None:
        """복구 시각과 같은 초에 생긴 버전도 그 시각의 상태에 들어감."""
        plan = restore.plan_restore([_entry('a', '2026-10-30T02:00:00.000000Z', 'v2')], T2)
        self.assertIn('a', plan.objects)

    def test_plan_restore_drops_keys_deleted_before_the_point(self) -> None:
        """마지막 기록이 삭제 표시면 그 시각에는 없던 객체라 뺌."""
        entries = [
            _entry('a', '2026-10-30T01:00:00.000000Z', 'v1'),
            _entry('a', '2026-10-30T02:00:00.000000Z', 'm1', deleted=True),
        ]
        self.assertEqual(restore.plan_restore(entries, T2).objects, {})
        self.assertEqual(restore.plan_restore(entries, T1).objects['a'].version_id, 'v1')

    def test_plan_restore_ignores_keys_created_after_the_point(self) -> None:
        """그 시각 뒤에 처음 생긴 키는 계획에 없음."""
        plan = restore.plan_restore([_entry('b', '2026-10-30T03:00:00.000000Z', 'v1')], T2)
        self.assertEqual(plan.objects, {})

    def test_plan_restore_refuses_same_second_ties(self) -> None:
        """같은 초의 덮어쓰기와 삭제는 순서를 알 수 없으니 추측하지 않고 멈춤."""
        entries = [
            _entry('a', '2026-10-30T02:00:00.000000Z', 'v2'),
            _entry('a', '2026-10-30T02:00:00.000000Z', 'm1', deleted=True),
        ]
        with self.assertRaises(restore.AmbiguousRestorePointError) as raised:
            restore.plan_restore(entries, T2)
        self.assertEqual(raised.exception.keys, ['a'])

    def test_plan_restore_allows_ties_that_a_later_record_settles(self) -> None:
        """같은 초의 기록이 있어도 그 뒤 기록이 있으면 순서가 상관없음."""
        entries = [
            _entry('a', '2026-10-30T02:00:00.000000Z', 'v2'),
            _entry('a', '2026-10-30T02:00:00.000000Z', 'm1', deleted=True),
            _entry('a', '2026-10-30T03:00:00.000000Z', 'v3'),
        ]
        self.assertEqual(restore.plan_restore(entries, T3).objects['a'].version_id, 'v3')

    def test_plan_restore_filters_by_prefix(self) -> None:
        """접두어가 다른 키는 계획에 넣지 않음."""
        entries = [
            _entry('logs/a', '2026-10-30T01:00:00.000000Z', 'v1'),
            _entry('data/b', '2026-10-30T01:00:00.000000Z', 'v1'),
        ]
        self.assertEqual(list(restore.plan_restore(entries, T1, 'data/').objects), ['data/b'])


class TestRunRestore(aws_case.AwsTestCase):
    """실제 백업 기록으로 복구하는 시험."""

    def setUp(self) -> None:
        super().setUp()
        with freezegun.freeze_time(T1):
            self.put('keep.txt', b'keep')
            self.put('changed.txt', b'old')
            self.put('deleted.txt', b'bye')
        with freezegun.freeze_time(T2):
            self.put('changed.txt', b'new')
            self.s3.delete_object(Bucket=aws_case.SOURCE, Key='deleted.txt')
            self.put('created.txt', b'later')
        backup.run_backup(self.s3, self.catalog, aws_case.SOURCE, aws_case.VAULT)

    def _restore(self, at: datetime.datetime) -> dict[str, bytes]:
        plan = restore.plan_restore(self.catalog.entries(aws_case.SOURCE), at)
        restore.run_restore(self.s3, plan, aws_case.VAULT, aws_case.TARGET, aws_case.SOURCE)
        listed = self.s3.list_objects_v2(Bucket=aws_case.TARGET).get('Contents', [])
        return {
            item['Key']: self.s3.get_object(Bucket=aws_case.TARGET, Key=item['Key'])['Body'].read()
            for item in listed
        }

    def test_run_restore_rebuilds_state_at_t1(self) -> None:
        """T1에는 지운 파일이 있고, 바뀐 파일은 옛 내용이고, 나중에 만든 파일은 없음."""
        self.assertEqual(
            self._restore(T1),
            {'keep.txt': b'keep', 'changed.txt': b'old', 'deleted.txt': b'bye'},
        )

    def test_run_restore_rebuilds_state_at_t2(self) -> None:
        """T2에는 지운 파일이 없고, 바뀐 파일은 새 내용이고, 새 파일이 있음."""
        self.assertEqual(
            self._restore(T2),
            {'keep.txt': b'keep', 'changed.txt': b'new', 'created.txt': b'later'},
        )

    def test_run_restore_refuses_source_bucket_as_target(self) -> None:
        """원본에는 읽기만 하므로 원본으로 복구하지 않음."""
        plan = restore.plan_restore(self.catalog.entries(aws_case.SOURCE), T1)
        with self.assertRaises(restore.Error):
            restore.run_restore(self.s3, plan, aws_case.VAULT, aws_case.SOURCE, aws_case.SOURCE)

    def test_run_restore_refuses_non_empty_target(self) -> None:
        """대상에 다른 객체가 있으면 섞이므로 시작하지 않음."""
        self.s3.put_object(Bucket=aws_case.TARGET, Key='other', Body=b'x')
        plan = restore.plan_restore(self.catalog.entries(aws_case.SOURCE), T1)
        with self.assertRaises(restore.Error):
            restore.run_restore(self.s3, plan, aws_case.VAULT, aws_case.TARGET, aws_case.SOURCE)


if __name__ == '__main__':
    unittest.main()
