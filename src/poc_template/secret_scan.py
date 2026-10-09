"""Small staged-blob credential guard, not a confidentiality or history audit."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

from .project_git import git_environment

MAX_BYTES = 16 * 1024 * 1024
ALLOWLIST = ".poc-secret-allowlist.json"
RULES = {
    "private-key": re.compile(r"-----BEGIN (?:[A-Z0-9]+ )*PRIVATE KEY-----"),
    "github-token": re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{60,})\b"),
    "provider-token": re.compile(r"\bsk-(?:proj-|ant-)?[A-Za-z0-9_-]{24,}\b"),
    "aws-access-key": re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    "slack-token": re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b"),
}
ASSIGNMENT = re.compile(
    r'''(?i)["']?\b(?:[A-Za-z0-9]+_)*(?:api[_-]?key|access[_-]?(?:key|token)|auth[_-]?token|client[_-]?secret|password|passwd|secret)["']?\s*[:=]\s*(?:"([^"\r\n]{8,})"|'([^'\r\n]{8,})'|([A-Za-z0-9_+/=-]{12,}))(?=\s*(?:$|[,}#;)\]]))''')
PLACEHOLDERS = {"changeme", "replace-me", "your-api-key", "not-a-real-secret", "redacted"}


def git(root: Path, *args: str, index: Path | None = None, absent_ok=False) -> bytes:
    env = git_environment()
    if index is not None:
        env["GIT_INDEX_FILE"] = str(index)
    try:
        result = subprocess.run(["git", "-C", str(root), *args], env=env,
                                stdin=subprocess.DEVNULL, capture_output=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise ValueError("Credential scan: Git unavailable or timed out; no clean result") from error
    if result.returncode and not (absent_ok and result.returncode == 1):
        # Git output and command input are not echoed: they may contain private data.
        raise ValueError("Credential scan: Git operation failed; check project/index access")
    return result.stdout


def repository(project: Path) -> Path:
    root = project.resolve()
    observed = os.fsdecode(git(root, "rev-parse", "--show-toplevel")).strip()
    if Path(observed).resolve() != root:
        raise ValueError("Select the exact repository root, not a directory in another repository")
    return root


def blob(root: Path, oid: str, index: Path | None) -> bytes:
    if int(git(root, "cat-file", "-s", oid, index=index)) > MAX_BYTES:
        raise ValueError("Credential scan incomplete: staged blob exceeds 16 MiB; reduce or keep it outside Git")
    return git(root, "cat-file", "blob", oid, index=index)


def exceptions(data: bytes) -> list[dict]:
    try:
        document = json.loads(data)
        rows = document["allow"]
        if set(document) != {"allow"} or not isinstance(rows, list):
            raise ValueError
        for row in rows:
            if (not isinstance(row, dict) or set(row) != {"path", "rule", "sha256", "reason"}
                    or not all(isinstance(value, str) for value in row.values())
                    or row["rule"] not in {*RULES, "inline-credential", "credential-file"}
                    or not re.fullmatch(r"[0-9a-f]{64}", row["sha256"])
                    or len(row["reason"].strip()) < 8):
                raise ValueError
        return rows
    except (ValueError, TypeError, KeyError, UnicodeError) as error:
        raise ValueError("Invalid staged credential allowlist; see docs/internal/security.md") from error


def scan(project: Path, index: Path | None = None) -> dict:
    root = repository(project)
    if index is not None:
        index = index.resolve()
        gitdir = Path(os.fsdecode(git(root, "rev-parse", "--absolute-git-dir")).strip()).resolve()
        if not index.is_relative_to(gitdir) or not index.is_file():
            raise ValueError("Commit index must be a regular file inside this repository's Git directory")
    entries = []
    for record in git(root, "ls-files", "--stage", "-z", index=index).split(b"\0"):
        if not record:
            continue
        metadata, path = record.split(b"\t", 1)
        mode, oid, stage = metadata.decode("ascii").split()
        if stage != "0":
            raise ValueError("Credential scan incomplete: resolve unmerged index entries first")
        entries.append((mode, oid, os.fsdecode(path)))
    allowances = []
    for mode, oid, path in entries:
        if path == ALLOWLIST:
            if mode not in {"100644", "100755"}:
                raise ValueError("Credential allowlist must be a regular staged file")
            allowances = exceptions(blob(root, oid, index))
    report = dict(findings=[], scanned_files=0, allowed_findings=0, binary_files=0,
                  symlinks_not_followed=0, submodules_not_scanned=0)
    for mode, oid, path in entries:
        if mode == "120000":
            report["symlinks_not_followed"] += 1
            continue
        if mode == "160000":
            report["submodules_not_scanned"] += 1
            continue
        data = blob(root, oid, index)
        digest = hashlib.sha256(data).hexdigest()
        report["scanned_files"] += 1
        report["binary_files"] += int(b"\0" in data)
        # Also look for recognizable ASCII credentials in bounded binary blobs.
        text = data.decode("utf-8", errors="replace")
        matches = set()
        name = Path(path).name.lower()
        if ((name == ".env" or name.startswith(".env.")) and name not in {".env.example", ".env.template"}
                or name in {"credentials.json", "secrets.json"} or name.endswith((".p12", ".pfx"))):
            matches.add((1, "credential-file"))
        for number, line in enumerate(text.splitlines(), 1):
            for rule, pattern in RULES.items():
                if pattern.search(line):
                    matches.add((number, rule))
            for match in ASSIGNMENT.finditer(line):
                value = next(group for group in match.groups() if group is not None)
                if (value.lower() not in PLACEHOLDERS
                        and not re.fullmatch(r"\$\{[A-Za-z_][A-Za-z0-9_]*\}|<[^<>]+>", value)):
                    matches.add((number, "inline-credential"))
        for line, rule in sorted(matches):
            if any(row["path"] == path and row["rule"] == rule and row["sha256"] == digest
                   for row in allowances):
                report["allowed_findings"] += 1
            else:
                report["findings"].append(dict(path=path, line=line, rule=rule))
    return report


HOOK = '''#!/bin/sh
# PoC-Template staged credential guard v1
set -eu
root=$(git rev-parse --show-toplevel)
cd "$root"
if [ -n "${POC_PYTHON:-}" ]; then
    python="$POC_PYTHON"
elif [ -x .venv/bin/python ]; then
    python=.venv/bin/python
else
    python=
    for candidate in python3 python3.14 python3.13 python3.12 python3.11; do
        if command -v "$candidate" >/dev/null 2>&1 && "$candidate" -c 'import sys; sys.exit(sys.version_info < (3, 11))' >/dev/null 2>&1; then
            python="$candidate"
            break
        fi
    done
    if [ -z "$python" ]; then
        echo 'Credential guard needs Python 3.11+: create .venv or set POC_PYTHON to your compatible interpreter.' >&2
        exit 2
    fi
fi
export PYTHONPATH="$root/src"
# git commit -a/--only may supply a temporary candidate index.
if [ -n "${GIT_INDEX_FILE:-}" ]; then
    exec "$python" -m poc_template secrets scan --project "$root" --index "$GIT_INDEX_FILE"
fi
exec "$python" -m poc_template secrets scan --project "$root"
'''


def install_hook(project: Path) -> dict:
    root = repository(project)
    if git(root, "config", "--get", "core.hooksPath", absent_ok=True):
        raise ValueError("Existing core.hooksPath preserved; run secrets scan manually or integrate into your hook")
    if not (root / "src/poc_template/secret_scan.py").is_file():
        raise ValueError("Project has no bundled scanner; scan manually from the Template environment instead")
    hooks = Path(os.fsdecode(git(root, "rev-parse", "--git-path", "hooks")).strip())
    if not hooks.is_absolute():
        hooks = root / hooks
    if hooks.is_symlink():
        raise ValueError("Existing symlinked hooks directory preserved; integrate manually")
    hooks.mkdir(parents=True, exist_ok=True)
    target = hooks / "pre-commit"
    if target.is_symlink() or target.exists() and target.read_bytes() != HOOK.encode():
        raise ValueError("Existing pre-commit hook preserved; run secrets scan manually or integrate into your hook")
    if not target.exists():
        with target.open("xb") as stream:
            stream.write(HOOK.encode())
    target.chmod(0o755)
    return dict(status="installed", hook="pre-commit", scope="local repository only")
