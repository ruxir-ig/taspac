# Agent-Ready Task Packet

## Task
- Repository: `./examples/demo-repo`
- Task: add JWT auth to upload endpoint

## Relevant Files
- `tests/test_upload.py` - score 13; filename matches 'upload', ripgrep found 5 keyword hit(s), imports related names
- `app/upload.py` - score 12; filename matches 'upload', ripgrep found 4 keyword hit(s), imports related names
- `app/auth.py` - score 5; filename matches 'auth'
- `README.md` - score 1; ripgrep found 1 keyword hit(s)
- `pyproject.toml` - score 1; ripgrep found 1 keyword hit(s)

## Relevant Snippets
### `tests/test_upload.py:1-3`
```
from app.upload import upload_file
```
### `tests/test_upload.py:3-7`
```
class Request:
    headers = {"authorization": "demo-token"}
    files = {"file": type("File", (), {"filename": "avatar.png"})()}
```
### `app/upload.py:1-3`
```
from app.auth import verify_token
```
### `app/upload.py:2-6`
```
def upload_file(request):
    token = request.headers.get("authorization")
    user = verify_token(token)
```
### `README.md:1-3`
```
# Demo Upload API

Small demo repository used by `taspac` verification.
```
### `pyproject.toml:1-4`
```
[project]
name = "demo-upload-api"
version = "0.1.0"
requires-python = ">=3.10"
```

## Suggested Commands
- `python -m pytest`
- `python -m ruff check .`
- `Review README.md setup and test instructions`

## Recent Commits
- No recent file-specific commits found.

## Risks / Constraints
- Authentication work can affect access control; verify negative and expired-token cases.
- Upload paths may need file size, content type, and storage error handling tests.

## Agent Prompt
You are working in the repository above. Complete the task using the relevant files and snippets as starting points, keep changes scoped, run the suggested verification commands where applicable, and report any remaining risks.
