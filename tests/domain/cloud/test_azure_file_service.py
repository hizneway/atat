import pytest
from azure.storage.blob.models import Blob

from atat.domain.csp.files import AzureFileService


@pytest.fixture
def mock_block_blob_service():
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
                    name=self.blob_name, content=self.content, metadata=self.metadata,
                )

    return MockBlockBlobService


@pytest.fixture
def file_service(app, mock_block_blob_service):
    file_service = AzureFileService(config=app.config)
    file_service.BlockBlobService = mock_block_blob_service
    return file_service


@pytest.fixture
def task_order(file_service):
    return file_service.download_task_order(file_service.BlockBlobService.blob_name)


class Test_download_task_order:
    def test_name(self, task_order, file_service):
        assert task_order["name"] == file_service.BlockBlobService.blob_name

    def test_content(self, task_order, file_service):
        assert task_order["content"] == file_service.BlockBlobService.content

    def test_filename(self, task_order, file_service):
        assert (
            task_order["filename"] == file_service.BlockBlobService.metadata["filename"]
        )

    def test_no_metadata(self, file_service):
        file_service.BlockBlobService.metadata = None
        task_order = file_service.download_task_order(
            file_service.BlockBlobService.blob_name
        )
        assert task_order["filename"] == AzureFileService.DEFAULT_FILENAME

    def test_no_filename_in_metadata(self, file_service):
        file_service.BlockBlobService.metadata = {}
        task_order = file_service.download_task_order(
            file_service.BlockBlobService.blob_name
        )
        assert task_order["filename"] == AzureFileService.DEFAULT_FILENAME
