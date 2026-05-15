# taspac

`taspac` is a small CLI-first Agent-Ready Task Packet Generator.

Give it:
- a GitHub repository (or local repo)
- a plain-English engineering task

and it generates a structured markdown packet that gives AI coding agents useful repo-specific context before implementation starts.

```bash
taspac generate --repo https://github.com/example/repo --task "add JWT auth to upload endpoint"
```

## Why This Exists

AI coding tools are surprisingly capable once they understand the shape of a codebase.

The problem is that most tasks are underspecified. Developers repeatedly re-explain:
- which files matter
- what commands to run
- what parts of the repo are risky
- which patterns already exist
- what should not break

`taspac` is a deliberately small tool that closes part of that context gap.

Instead of building another chat UI or multi-agent system, it focuses on generating a sharp, repo-aware task packet that can be pasted directly into tools like Claude Code, Codex, Cursor, or Aider.

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

## Demo Workflow

```bash
python -m taspac generate \
  --repo ./examples/demo-repo \
  --task "add JWT auth to upload endpoint" \
  --output examples/generated-packet.md
```

Open `examples/generated-packet.md` to see a sample task packet.

## Design Decisions

`taspac` intentionally keeps the implementation direct and local-first.

It:
- scores files using lightweight heuristics instead of embeddings infrastructure
- extracts nearby snippets around task-relevant matches
- infers likely commands from project files like `package.json`, `Makefile`, and `pyproject.toml`
- reads recent commits touching matched files using `git log`
- generates simple risk/invariant hints from task keywords and matched paths

The project deliberately avoids:
- authentication
- dashboards
- vector databases
- hosted infrastructure
- multi-agent orchestration
- long-running background services

The goal was to build the smallest genuinely useful version possible within a few hours.
