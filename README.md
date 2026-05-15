# taspac

`taspac` is a small CLI-first Agent-Ready Task Packet Generator.

Give it:
- a GitHub repository (or local repo)
- a plain-English engineering task

and it generates a structured markdown packet that gives AI coding agents useful repo-specific context before implementation starts.

```bash
taspac generate --repo https://github.com/example/repo --task "add JWT auth to upload endpoint"
```

For slower networks or larger repositories, increase the clone timeout:

```bash
taspac generate \
  --repo https://github.com/example/repo \
  --task "add JWT auth to upload endpoint" \
  --clone-timeout 300
```

## Why This Exists

Normally, when you give an AI coding agent a task, it starts with almost no context.

You end up repeatedly explaining:

- which files matter
- what parts of the repo are related
- what commands to run
- existing patterns in the codebase
- what could break if changed carelessly

`taspac` automates that briefing process.

It scans a repository and generates a structured task packet containing:

- relevant files
- nearby code snippets
- useful commands
- recent commits
- risks and constraints
- a focused implementation prompt

The goal is to reduce the amount of repo exploration and context reconstruction an AI agent has to do before it can start making useful changes.

`taspac` stays deliberately small: paste the packet into Claude Code, Codex, Cursor, Aider, or similar—no extra chat UI or multi-agent stack required.

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
