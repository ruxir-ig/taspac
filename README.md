# taspac

`taspac` is a small CLI-first Agent-Ready Task Packet Generator. Give it a GitHub repository URL, or a local git repository path, plus a task description. It produces a structured markdown packet an implementation agent can use as a starting point.

```bash
taspac generate --repo https://github.com/example/repo --task "add JWT auth to upload endpoint"
```

## What It Produces

The generated packet includes:

- Task
- Relevant Files
- Relevant Snippets
- Suggested Commands
- Recent Commits
- Risks / Constraints
- Agent Prompt

## Install Locally

```bash
python -m pip install -e .
```

You can also run without installing:

```bash
python -m taspac generate --repo ./examples/demo-repo --task "add JWT auth to upload endpoint"
```

## Heuristics

`taspac` keeps the implementation intentionally direct:

- Scores files by filename matches and task keyword mentions.
- Extracts nearby snippets around matched keywords.
- Looks at import lines for related names.
- Infers likely commands from `package.json`, `pyproject.toml`, `requirements.txt`, `Makefile`, `docker-compose.yml`, and `README.md`.
- Reads recent git commits touching matched files with `git log`.
- Adds simple risk notes from task words and matched filenames.

It uses subprocess calls to `git` and standard-library Python only. No auth, dashboard, SaaS, vector database, or long-running service is required.

## Demo Workflow

```bash
python -m taspac generate \
  --repo ./examples/demo-repo \
  --task "add JWT auth to upload endpoint" \
  --output examples/generated-packet.md
```

Open `examples/generated-packet.md` to see a sample task packet.
