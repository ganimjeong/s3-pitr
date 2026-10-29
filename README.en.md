# S3 Point-in-Time Restore

> [!IMPORTANT]
> A personal learning project. Not affiliated with Commvault or Clumio.
> Copyright 2026 Ajin Jeong. Licensed under the Apache License 2.0. See [LICENSE](LICENSE).

Incremental backup and point-in-time restore for Amazon S3 buckets, with the test automation that checks a restore is exactly right.

Code comments, commit messages and the design notes in `research/` and `til/` are written in Korean. This page summarizes them.

## What it does

- **Backup**: copies only the object versions that are not in the catalog yet from a versioned source bucket to a vault bucket. Each copy is recorded in a DynamoDB catalog with the SHA-256 checksum S3 computed during the copy. Delete markers are recorded too.
- **Point-in-time restore**: given a timestamp, rebuilds the bucket as it was at that moment into an empty bucket. Objects deleted later come back, objects created later are left out.
- **Verify**: compares every restored object's SHA-256 with the value recorded at backup time, and fails on missing objects and on objects that should not be there.

## Design decisions

| Decision | Why |
| --- | --- |
| Copy first, record second | If the process dies in between, what is left is an unrecorded file that the next run overwrites. Recording first could leave a catalog entry with no backup behind it, which the next run would skip and only a restore would reveal. |
| Two layers against duplicates | Known versions are skipped, and a conditional write (`attribute_not_exists`) rejects a second record of the same version even when two runs overlap. |
| Retries live only in botocore | Wrapping another retry loop around botocore multiplies attempts (5 x 8 = 40 in the worst case) and adds load exactly when S3 asks clients to slow down. `adaptive` mode also lowers the client's request rate after throttling. |
| SHA-256, not ETag | The ETag of a multipart upload is not the MD5 of the content. |
| Stop instead of guessing | S3 `LastModified` has one-second precision, and boto3 returns versions and delete markers as two separate lists, so the order of an overwrite and a delete within the same second is lost. If that decides the result, the restore stops and names the keys. |
| Restore only into an empty, different bucket | Writing over the source leaves nothing to fall back to. Restoring into a bucket that already has objects makes "unexpected object" impossible to tell apart from leftovers. |

## Usage

The source bucket must have versioning enabled. The catalog table and the buckets must exist.

```sh
python -m s3pitr --table s3pitr-catalog backup --source my-data --vault my-vault

python -m s3pitr --table s3pitr-catalog restore \
  --source my-data --vault my-vault --target my-restore --at 2026-10-30T09:00:00+09:00

python -m s3pitr --table s3pitr-catalog verify \
  --source my-data --target my-restore --at 2026-10-30T09:00:00+09:00
```

Timestamps without a timezone are rejected. `restore` and `verify` exit with 1 when verification fails. Objects larger than 5 GB are not supported yet.

## Tests

| Command | What runs |
| --- | --- |
| `make test` | Unit tests with `unittest` and `green` against `moto`, branch coverage report |
| `make e2e` | Integration tests with `pytest` against a moto server over HTTP. Only `AWS_ENDPOINT_URL` changes, so requests go through the same HTTP, parsing and retry path as real AWS |

Failure injection in the unit tests:

- running the same backup twice
- the process dying after a copy and before the record, and during a copy
- `SlowDown` (HTTP 503) answered twice, injected at the HTTP layer through botocore's `before-send` event so the real retry logic runs

When a test suite passed on the first run, each guarantee was broken on purpose to see whether a test failed. One gap was found this way and fixed: the first crash test could not tell "copy first" from "record first".

CI runs lint, mypy, format check, unit tests and integration tests on every pull request. LocalStack is not used because its images require an auth token since March 2026.

## How the repository is run

The setup follows the public `clumio-code/bulk_restore` repository: Ruff with the same rule set and single quotes, strict mypy, `green` for unit tests, pre-commit hooks including `clumio-code/pre-push-hooks` to block direct pushes to `main`, and the same CI step order. Every change goes through an issue (`PITR-<n>`), a `user/<name>/PITR-<n>/main` branch and a squash-merged pull request. Commits are signed.

## Retrospectives (Korean)

- [Initial setup](til/2026-10-27-initial-setup.md): matching the Python version to the runtime, where retries belong, why `isoformat()` is not a safe sort key
- [Repository protection](til/2026-10-27-repo-protection.md): signing, branch rules, how Dependabot is used
- [Incremental backup](til/2026-10-30-incremental-backup.md): copy before record, the crash test that missed a guarantee, simulating throttling
- [Point-in-time restore](til/2026-10-30-point-in-time-restore.md): the lost order inside one second, what verification must catch

## Not done yet

- Objects over 5 GB (multipart copy changes the SHA-256 into a composite checksum)
- Event-driven backup through S3 event notifications and SQS
- Parallel restore for large buckets
- A run against real AWS to record where moto differs
