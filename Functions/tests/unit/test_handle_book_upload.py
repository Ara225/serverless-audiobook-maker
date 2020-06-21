import simplejson as json
import pytest
from sys import path
path.append("../../")
from os import environ
from handlers.handle_book_upload import app as bookUpload

def test_handle_books():
    ret = bookUpload.convert_text_to_ssml("hello\n\nhello\n\n")
    assert ret == "<speak><amazon:auto-breaths><p>hello</p><p>hello</p></amazon:auto-breaths></speak>"

if __name__ == "__main__":
    environ['APP_STAGE'] = "local"
    pytest.main()