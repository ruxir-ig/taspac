from app.upload import upload_file


class Request:
    headers = {"authorization": "demo-token"}
    files = {"file": type("File", (), {"filename": "avatar.png"})()}


def test_upload_file():
    assert upload_file(Request())["status"] == 201
