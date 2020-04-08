import pytest

from atat.domain.csp.files import AzureFileService
from azure.storage.blob.models import Blob


class MockBlockBlobService(object):
    blob_name = "1s4lsd45"
    content = b"mock content"
    metadata = {"filename": "test.pdf"}

    def __init__(self, exception=None, **kwargs):
        self.exception = exception

    def get_blob_to_bytes(self, blob_name, **kwargs):
        if self.exception:
            raise self.exception
        else:
            return Blob(
                name=MockBlockBlobService.blob_name,
                content=MockBlockBlobService.content,
                metadata=MockBlockBlobService.metadata,
            )


class Test_download_task_order:
    @pytest.fixture
    def file_service(self, app):
        file_service = AzureFileService(config=app.config)
        file_service.BlockBlobService = MockBlockBlobService
        return file_service

    @pytest.fixture
    def task_order(self, file_service):
        return file_service.download_task_order(MockBlockBlobService.blob_name)

    def test_name(self, task_order):
        assert task_order["name"] == MockBlockBlobService.blob_name

    def test_content(self, task_order):
        assert task_order["content"] == MockBlockBlobService.content

    def test_filename(self, task_order):
        assert task_order["filename"] == MockBlockBlobService.metadata["filename"]

    def test_no_metadata(self, file_service):
        MockBlockBlobService.metadata = None
        task_order = file_service.download_task_order(MockBlockBlobService.blob_name)
        assert task_order["filename"] == AzureFileService.DEFAULT_FILENAME

    def test_no_filename_in_metadata(self, file_service):
        MockBlockBlobService.metadata = {}
        task_order = file_service.download_task_order(MockBlockBlobService.blob_name)
        assert task_order["filename"] == AzureFileService.DEFAULT_FILENAME
