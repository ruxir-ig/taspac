from app.auth import verify_token


def upload_file(request):
    token = request.headers.get("authorization")
    user = verify_token(token)
    if not user:
        return {"status": 401, "body": "missing or invalid token"}

    file_obj = request.files["file"]
    return {"status": 201, "body": f"uploaded {file_obj.filename}"}
