from __future__ import annotations

import argparse
import re
import shlex
import subprocess
import tempfile
from collections import Counter
from dataclasses import dataclass
from pathlib import Path


STOPWORDS = {
    "a",
    "an",
    "and",
    "api",
    "for",
    "in",
    "of",
    "on",
    "or",
    "the",
    "to",
    "with",
}

MAX_FILES = 8
MAX_SNIPPETS = 10


@dataclass
class Match:
    path: str
    score: int
    reasons: list[str]


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "generate":
        packet = generate_packet(args.repo, args.task, args.output, args.clone_timeout)
        if args.output:
            print(f"Wrote task packet to {args.output}")
        else:
            print(packet)
        return 0

    parser.print_help()
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="taspac",
        description="Generate an agent-ready markdown task packet from a GitHub repo and task.",
    )
    subparsers = parser.add_subparsers(dest="command")

    generate = subparsers.add_parser("generate", help="Generate a task packet")
    generate.add_argument("--repo", required=True, help="GitHub URL or local git repo path")
    generate.add_argument("--task", required=True, help="Task description")
    generate.add_argument(
        "--output",
        "-o",
        help="Write markdown to a file instead of stdout",
    )
    generate.add_argument(
        "--clone-timeout",
        type=int,
        default=120,
        help="Seconds to allow for cloning remote repositories",
    )
    return parser


def generate_packet(repo: str, task: str, output: str | None = None, clone_timeout: int = 120) -> str:
    with tempfile.TemporaryDirectory(prefix="taspac-") as tmp:
        repo_path = prepare_repo(repo, Path(tmp), clone_timeout)
        keywords = extract_keywords(task)
        files = list_repo_files(repo_path)
        matches = rank_files(repo_path, files, keywords)
        snippets = collect_snippets(repo_path, matches, keywords)
        commands = infer_commands(repo_path)
        commits = recent_commits(repo_path, matches)
        risks = infer_risks(task, matches, snippets)
        packet = render_packet(repo, task, matches, snippets, commands, commits, risks)

    if output:
        Path(output).write_text(packet, encoding="utf-8")
    return packet


def prepare_repo(repo: str, tmp: Path, clone_timeout: int) -> Path:
    candidate = Path(repo).expanduser()
    if candidate.exists():
        return candidate.resolve()

    target = tmp / "repo"
    run(
        ["git", "clone", "--depth", "50", repo, str(target)],
        Path.cwd(),
        check=True,
        timeout=clone_timeout,
    )
    return target


def extract_keywords(task: str) -> list[str]:
    raw = re.findall(r"[A-Za-z0-9_./-]+", task.lower())
    words: list[str] = []
    for token in raw:
        for piece in re.split(r"[/_.-]+", token):
            if len(piece) >= 3 and piece not in STOPWORDS:
                words.append(piece)
    return [word for word, _ in Counter(words).most_common(20)]


def list_repo_files(repo_path: Path) -> list[str]:
    git_files = run(["git", "ls-files"], repo_path)
    files = git_files.stdout.splitlines() if git_files.returncode == 0 else []
    if not files:
        files = [
            str(path.relative_to(repo_path))
            for path in repo_path.rglob("*")
            if path.is_file() and ".git" not in path.parts
        ]
    return [path for path in files if is_candidate_file(path)]


def is_candidate_file(path: str) -> bool:
    ignored_parts = {"node_modules", ".venv", "venv", "dist", "build", "__pycache__"}
    if any(part in ignored_parts for part in Path(path).parts):
        return False
    ignored_exts = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".pdf", ".lock", ".min.js"}
    return not any(path.endswith(ext) for ext in ignored_exts)


def rank_files(repo_path: Path, files: list[str], keywords: list[str]) -> list[Match]:
    matches: list[Match] = []
    rg_counts = ripgrep_counts(repo_path, keywords, files)
    for file_path in files:
        path = repo_path / file_path
        score = 0
        reasons: list[str] = []
        lower_path = file_path.lower()

        for keyword in keywords:
            if keyword in lower_path:
                score += 5
                reasons.append(f"filename matches '{keyword}'")

        if file_path in rg_counts:
            score += min(rg_counts[file_path], 15)
            reasons.append(f"ripgrep found {rg_counts[file_path]} keyword hit(s)")

        text = read_text(path)
        if text:
            lower_text = text.lower()
            content_hits = sum(lower_text.count(keyword) for keyword in keywords) if not rg_counts else 0
            if content_hits:
                score += min(content_hits, 15)
                reasons.append(f"content mentions task keywords {content_hits} time(s)")

            imported = imported_names(text)
            import_hits = [name for name in imported if any(keyword in name.lower() for keyword in keywords)]
            if import_hits:
                score += 3
                reasons.append("imports related names")

        if score:
            matches.append(Match(file_path, score, dedupe(reasons)))

    matches.sort(key=lambda match: (-match.score, match.path))
    return matches[:MAX_FILES]


def ripgrep_counts(repo_path: Path, keywords: list[str], files: list[str]) -> dict[str, int]:
    if not keywords:
        return {}
    pattern = "|".join(re.escape(keyword) for keyword in keywords)
    result = run(["rg", "--count-matches", "--ignore-case", pattern, "--", *files], repo_path)
    if result.returncode not in {0, 1}:
        return {}

    counts: dict[str, int] = {}
    for line in result.stdout.splitlines():
        if ":" not in line:
            continue
        path, count = line.rsplit(":", 1)
        if is_candidate_file(path):
            counts[path] = int(count)
    return counts


def collect_snippets(repo_path: Path, matches: list[Match], keywords: list[str]) -> list[tuple[str, str]]:
    snippets: list[tuple[str, str]] = []
    for match in matches:
        path = repo_path / match.path
        text = read_text(path)
        if not text:
            continue
        lines = text.splitlines()
        hit_indexes = [
            index
            for index, line in enumerate(lines)
            if any(keyword in line.lower() for keyword in keywords)
        ]
        for index in hit_indexes[:2]:
            start = max(0, index - 2)
            end = min(len(lines), index + 3)
            body = "\n".join(lines[start:end]).strip()
            if body:
                snippets.append((f"{match.path}:{start + 1}-{end}", body))
        if len(snippets) >= MAX_SNIPPETS:
            break
    return snippets[:MAX_SNIPPETS]


def infer_commands(repo_path: Path) -> list[str]:
    commands: list[str] = []
    files = {path.name for path in repo_path.iterdir() if path.is_file()}

    if "package.json" in files:
        text = read_text(repo_path / "package.json")
        scripts = re.findall(r'"([^"]+)":\s*"[^"]+"', text.partition('"scripts"')[2].partition("}")[0])
        for script in scripts:
            if script in {"test", "lint", "typecheck", "build", "dev"}:
                commands.append(f"npm run {script}")
        if not commands:
            commands.append("npm install")

    if "pyproject.toml" in files:
        commands.extend(["python -m pytest", "python -m ruff check ."])
    if "requirements.txt" in files:
        commands.append("python -m pip install -r requirements.txt")
    if "Makefile" in files or "makefile" in files:
        commands.append("make test")
    if "docker-compose.yml" in files or "compose.yml" in files:
        commands.append("docker compose up --build")
    if "README.md" in files:
        commands.append("Review README.md setup and test instructions")

    return dedupe(commands) or ["Inspect project README, then run the closest test command."]


def recent_commits(repo_path: Path, matches: list[Match]) -> list[str]:
    commits: list[str] = []
    for match in matches[:5]:
        result = run(
            ["git", "log", "-3", "--format=%h | %s | %an", "--", match.path],
            repo_path,
        )
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                commits.append(f"{line} ({match.path})")
    return dedupe(commits)[:10]


def infer_risks(task: str, matches: list[Match], snippets: list[tuple[str, str]]) -> list[str]:
    task_lower = task.lower()
    paths = " ".join(match.path.lower() for match in matches)
    text = " ".join(body.lower() for _, body in snippets)
    risks: list[str] = []

    if any(word in task_lower for word in ["auth", "jwt", "token", "permission", "login"]):
        risks.append("Authentication work can affect access control; verify negative and expired-token cases.")
    if any(word in paths for word in ["migration", "schema", "model", "database", "db"]):
        risks.append("Matched files touch data models or storage; check migration and rollback expectations.")
    if any(word in paths for word in ["upload", "file", "s3", "blob"]):
        risks.append("Upload paths may need file size, content type, and storage error handling tests.")
    if "todo" in text or "fixme" in text:
        risks.append("Relevant snippets include TODO/FIXME markers; confirm whether they constrain the task.")
    if not matches:
        risks.append("No strong file matches were found; begin with repository exploration before editing.")

    return risks or ["Keep the change scoped and run the inferred tests before handing off."]


def render_packet(
    repo: str,
    task: str,
    matches: list[Match],
    snippets: list[tuple[str, str]],
    commands: list[str],
    commits: list[str],
    risks: list[str],
) -> str:
    lines = [
        "# Agent-Ready Task Packet",
        "",
        "## Task",
        f"- Repository: `{repo}`",
        f"- Task: {task}",
        "",
        "## Relevant Files",
    ]
    if matches:
        for match in matches:
            lines.append(f"- `{match.path}` - score {match.score}; {', '.join(match.reasons)}")
    else:
        lines.append("- No strong matches found.")

    lines.extend(["", "## Relevant Snippets"])
    if snippets:
        for location, body in snippets:
            lines.extend([f"### `{location}`", "```", body, "```"])
    else:
        lines.append("- No snippets found.")

    lines.extend(["", "## Suggested Commands"])
    lines.extend(f"- `{command}`" for command in commands)

    lines.extend(["", "## Recent Commits"])
    if commits:
        lines.extend(f"- {commit}" for commit in commits)
    else:
        lines.append("- No recent file-specific commits found.")

    lines.extend(["", "## Risks / Constraints"])
    lines.extend(f"- {risk}" for risk in risks)

    prompt = (
        "You are working in the repository above. Complete the task using the relevant files "
        "and snippets as starting points, keep changes scoped, run the suggested verification "
        "commands where applicable, and report any remaining risks."
    )
    lines.extend(["", "## Agent Prompt", prompt, ""])
    return "\n".join(lines)


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def imported_names(text: str) -> list[str]:
    names: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith(("import ", "from ", "require(")):
            names.extend(re.findall(r"[A-Za-z_][A-Za-z0-9_./-]+", stripped))
    return names


def dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            result.append(item)
            seen.add(item)
    return result


def run(
    args: list[str],
    cwd: Path,
    check: bool = False,
    timeout: int = 10,
) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            args,
            cwd=cwd,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=check,
            timeout=timeout,
        )
    except FileNotFoundError as exc:
        if check:
            raise SystemExit(f"Missing required command: {shlex.quote(args[0])}") from exc
        return subprocess.CompletedProcess(args, 127, "", str(exc))
    except subprocess.TimeoutExpired as exc:
        if check:
            raise SystemExit(f"Command timed out: {shlex.join(args)}") from exc
        return subprocess.CompletedProcess(args, 124, exc.stdout or "", exc.stderr or "")


if __name__ == "__main__":
    raise SystemExit(main())
