#
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
#

# macOS와 리눅스에서 같은 셸로 돌게 함.
SHELL=/bin/bash

test_reports := build/test_reports/py
VERSION := $(shell cat VERSION)

.PHONY: *


clean:
	rm -rf build .mypy_cache .coverage .ruff_cache .pytest_cache *.egg-info dist

# 실행 의존성만 설치함.
install:
	pip install -r requirements.txt


# 개발 의존성까지 설치함.
install-dev:
	pip install -r requirements-dev.txt


# 단위 시험. JUnit XML과 커버리지 보고서를 build/test_reports/py에 만듦.
test:
	rm -rf $(test_reports) .coverage; \
	mkdir -p $(test_reports); \
	python3 -m green -v --run-coverage \
	  --junit-report=$(test_reports)/s3pitr-tests.xml s3pitr; \
	status=$$?; \
	python3 -m coverage xml -o $(test_reports)/s3pitr-coverage.xml; \
	python3 -m coverage html -d $(test_reports)/s3pitr-coverage-html; \
	python3 -m coverage report; \
	exit $$status


# 통합 시험. AWS_ENDPOINT_URL이 없으면 moto 서버를 직접 띄움.
e2e:
	python3 -m pytest -v


lint:
	ruff check


format:
	ruff format


format-check:
	ruff format --check


mypy:
	mypy s3pitr e2e
