import simplejson as json
import pytest
from sys import path
path.append("../../")
from os import environ
from handlers.handle_book_upload import app as bookUpload

def test_handle_books():
    ret = bookUpload.lambda_handler(json.load(open("../events/bookUploadEvent.json")), "")
    data = json.loads(ret["body"])
    assert ret["statusCode"] == 200

if __name__ == "__main__":
    environ['AUDIO_S3_BUCKET'] = "aws-polly-test"
    environ['APP_STAGE'] = "local"
    pytest.main()