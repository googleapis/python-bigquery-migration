# Copyright 2021 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from google.api_core.exceptions import InternalServerError
from google.api_core.exceptions import ServiceUnavailable
from google.api_core.exceptions import TooManyRequests

from google.cloud import storage

import pytest

from test_utils.retry import RetryErrors
from test_utils.system import unique_resource_id

from . import create_migration_workflow

retry_storage_errors = RetryErrors(
    (TooManyRequests, InternalServerError, ServiceUnavailable)
)

storage_client = storage.Client()
PROJECT_ID = storage_client.project


def _create_bucket(bucket_name, location=None):
    bucket = storage_client.bucket(bucket_name)
    retry_storage_errors(storage_client.create_bucket)(bucket_name, location=location)

    return bucket


@pytest.fixture
def buckets_to_delete():
    doomed = []
    yield doomed
    for item in doomed:
        if isinstance(item, storage.Bucket):
            retry_storage_errors(item.delete)(force=True)


def test_create_migration_workflow(capsys, buckets_to_delete):
    bucket_name = "bq_migration_create_workflow_test" + unique_resource_id()
    path = f"gs://{PROJECT_ID}/{bucket_name}"
    bucket = _create_bucket(bucket_name)
    buckets_to_delete.extend([bucket])

    create_migration_workflow.create_migration_workflow(path, path, PROJECT_ID)
    out, _ = capsys.readouterr()

    assert "demo-workflow-python-example-Teradata2BQ" in out
    assert "Current state:" in out
