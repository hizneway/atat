from atst.domain.csp.file_uploads import AzureUploader
from azure.storage.blob.models import Blob


class MockBlockBlobService(object):
    def __init__(self, exception=None, **kwargs):
        self.exception = exception

    def get_blob_to_bytes(self, blob_name="test.pdf", **kwargs):
        if self.exception:
            raise self.exception
        else:
            return Blob(name=blob_name, content=b"mock content")


def test_download_task_order_success(app, monkeypatch):
    uploader = AzureUploader(config=app.config)
    uploader.BlockBlobService = MockBlockBlobService

    task_order = uploader.download_task_order("test.pdf")
    assert task_order["name"] == "test.pdf"
    assert task_order["content"] == b"mock content"
