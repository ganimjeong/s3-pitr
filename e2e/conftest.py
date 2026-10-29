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
"""통합 시험 픽스처. AWS_ENDPOINT_URL이 없으면 moto 서버를 HTTP로 띄움."""

from __future__ import annotations

import os
import socket
import uuid
from collections.abc import Iterator

import pytest
from moto import server

from s3pitr import common, envkit


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        return int(sock.getsockname()[1])


@pytest.fixture(scope='session')
def endpoint() -> Iterator[str]:
    """시험이 요청을 보낼 엔드포인트. 코드는 이 값을 모르고 boto3가 환경 변수로 읽음."""
    existing = os.environ.get('AWS_ENDPOINT_URL')
    if existing:
        yield existing
        return
    port = _free_port()
    moto_server = server.ThreadedMotoServer(ip_address='127.0.0.1', port=port)
    moto_server.start()
    url = f'http://127.0.0.1:{port}'
    with pytest.MonkeyPatch.context() as patch:
        patch.setenv('AWS_ENDPOINT_URL', url)
        patch.setenv('AWS_ACCESS_KEY_ID', 'testing')
        patch.setenv('AWS_SECRET_ACCESS_KEY', 'testing')
        patch.setenv('AWS_DEFAULT_REGION', 'us-east-1')
        yield url
    moto_server.stop()


@pytest.fixture
def names(endpoint: str) -> Iterator[dict[str, str]]:
    """시험마다 겹치지 않는 버킷, 테이블 이름. 끝나면 버킷을 비우고 지움."""
    suffix = uuid.uuid4().hex[:8]
    created = {
        'source': f'src-{suffix}',
        'vault': f'vault-{suffix}',
        'target': f'restore-{suffix}',
        'table': f'catalog-{suffix}',
    }
    s3 = common.s3()
    envkit.create_bucket(s3, created['source'], versioned=True)
    envkit.create_bucket(s3, created['vault'], versioned=True)
    envkit.create_bucket(s3, created['target'])
    envkit.create_catalog_table(common.dynamodb(), created['table'])
    yield created
    for key in ('source', 'vault', 'target'):
        envkit.empty_bucket(s3, created[key])
        s3.delete_bucket(Bucket=created[key])
    common.dynamodb().Table(created['table']).delete()
