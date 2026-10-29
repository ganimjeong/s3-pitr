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
"""명령줄 도구로 백업, 변경, 다시 백업, 시점 복구, 검증까지 한 번에 돌림."""

from __future__ import annotations

import datetime
import random
import time

from s3pitr import __main__ as cli
from s3pitr import common, envkit

OBJECTS = 200
OVERWRITES = 50
DELETES = 30


def _wait_next_second() -> datetime.datetime:
    """S3 LastModified는 초 단위라서 단계 사이에 초가 바뀌게 기다림. 경계 시각을 돌려줌."""
    time.sleep(1.1)
    boundary = datetime.datetime.now(datetime.UTC)
    time.sleep(1.1)
    return boundary


def test_round_trip_restores_each_point_exactly(names: dict[str, str]) -> None:
    s3 = common.s3()
    rng = random.Random(20261030)  # noqa: S311  시험 데이터용 난수라 보안과 무관함
    keys = [f'data/{n // 50:02d}/obj-{n:04d}.bin' for n in range(OBJECTS)]
    for key in keys:
        s3.put_object(Bucket=names['source'], Key=key, Body=rng.randbytes(rng.randint(0, 2048)))
    base = ['--table', names['table']]
    backup = [*base, 'backup', '--source', names['source'], '--vault', names['vault']]
    assert cli.main(backup) == 0

    first_point = _wait_next_second()
    changed = rng.sample(keys, OVERWRITES + DELETES)
    for key in changed[:OVERWRITES]:
        s3.put_object(Bucket=names['source'], Key=key, Body=rng.randbytes(64))
    for key in changed[OVERWRITES:]:
        s3.delete_object(Bucket=names['source'], Key=key)
    assert cli.main(backup) == 0
    second_point = _wait_next_second()

    for point, expected in ((first_point, OBJECTS), (second_point, OBJECTS - DELETES)):
        target = names['target']
        # 복구는 빈 버킷에만 하므로 시점마다 비우고 시작함.
        envkit.empty_bucket(s3, target)
        restore = [
            *base,
            'restore',
            '--source',
            names['source'],
            '--vault',
            names['vault'],
            '--target',
            target,
            '--at',
            point.isoformat(),
        ]
        assert cli.main(restore) == 0
        assert s3.list_objects_v2(Bucket=target)['KeyCount'] == expected


def test_verify_exits_non_zero_when_restore_was_tampered(names: dict[str, str]) -> None:
    s3 = common.s3()
    s3.put_object(Bucket=names['source'], Key='a.txt', Body=b'one')
    base = ['--table', names['table']]
    assert cli.main([*base, 'backup', '--source', names['source'], '--vault', names['vault']]) == 0
    point = _wait_next_second().isoformat()
    restore = [
        *base,
        'restore',
        '--source',
        names['source'],
        '--vault',
        names['vault'],
        '--target',
        names['target'],
        '--at',
        point,
    ]
    assert cli.main(restore) == 0

    s3.put_object(Bucket=names['target'], Key='a.txt', Body=b'tampered')
    verify = [*base, 'verify', '--source', names['source'], '--target', names['target']]
    assert cli.main([*verify, '--at', point]) == 1
