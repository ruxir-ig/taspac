def verify_token(token):
    if not token:
        return None
    return {"id": "demo-user"}
