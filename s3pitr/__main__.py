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

"""명령줄 도구. python -m s3pitr {backup,restore,verify} ..."""

from __future__ import annotations

import argparse
import datetime
import logging
import sys
from collections.abc import Sequence

from s3pitr import backup, catalog, common, restore, verify

logger = logging.getLogger(__name__)


def _parse_time(value: str) -> datetime.datetime:
    """ISO 8601 시각을 받음. 시간대가 없으면 어느 시각인지 알 수 없어서 거부함."""
    parsed = datetime.datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        raise argparse.ArgumentTypeError(f'시간대를 붙여야 함(예: {value}+09:00): {value}')
    return parsed


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog='s3pitr', description='S3 증분 백업과 시점 복구')
    parser.add_argument('--table', required=True, help='카탈로그 DynamoDB 테이블 이름')
    commands = parser.add_subparsers(dest='command', required=True)

    backup_cmd = commands.add_parser('backup', help='새 버전만 금고로 복사')
    backup_cmd.add_argument('--source', required=True)
    backup_cmd.add_argument('--vault', required=True)
    backup_cmd.add_argument('--prefix', default='')

    for name, help_text in (('restore', '시점 복구 후 검증'), ('verify', '복구 결과만 검증')):
        cmd = commands.add_parser(name, help=help_text)
        cmd.add_argument('--source', required=True)
        cmd.add_argument('--target', required=True)
        cmd.add_argument(
            '--at', required=True, type=_parse_time, help='예: 2026-10-30T09:00:00+09:00'
        )
        cmd.add_argument('--prefix', default='')
        if name == 'restore':
            cmd.add_argument('--vault', required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """명령을 실행하고 종료 코드를 돌려줌. 검증이 실패하면 1."""
    args = _parser().parse_args(argv)
    logging.basicConfig(level=logging.INFO, format='%(levelname)s %(name)s %(message)s')
    s3 = common.s3()
    backup_catalog = catalog.Catalog(common.dynamodb().Table(args.table))

    if args.command == 'backup':
        backup.run_backup(s3, backup_catalog, args.source, args.vault, args.prefix)
        return 0

    plan = restore.plan_restore(backup_catalog.entries(args.source), args.at, args.prefix)
    if args.command == 'restore':
        restore.run_restore(s3, plan, args.vault, args.target, args.source)
    report = verify.verify_restore(s3, plan, args.target)
    return 0 if report.ok else 1


if __name__ == '__main__':
    sys.exit(main())
