"""Read-only local diagnostics; no assistant invocation, installation or automatic repair."""
import os
from pathlib import Path
import shutil
import sys

from .bootstrap import normalize_execution
from .bootstrap_workflow import config_for
from .project_git import git_environment
from .spec_kit_assets import verify_assets, verify_runtime
from .speckit_adapter import run_process


def inspect_project(root: Path) -> dict:
    root = Path(root).resolve()
    checks = []

    def note(name, status, detail):
        checks.append(dict(name=name, status=status, detail=detail))

    note("python", "ok" if sys.version_info >= (3, 11) else "error",
         f"{sys.executable}: {sys.version.split()[0]}; Python 3.11+ required")
    if not root.is_dir():
        note("project", "error", "Project directory does not exist")
        return dict(project=str(root), status="issues", checks=checks)
    config, required = {}, False
    try:
        if (root/".specify/bootstrap.json").exists():
            config = config_for(root)
            normalize_execution(config["integration"], config.get("execution"))
            required = config["through"] > 0
            note("configuration", "ok", f"Cumulative target {config['through']}; {config['integration']}")
        else:
            note("configuration", "warning", "No bound bootstrap configuration; checking Template/offline surface only")
    except (ValueError, OSError, KeyError, TypeError) as error:
        note("configuration", "error", str(error))
    for name, verifier in (("assets", verify_assets), ("runtime", verify_runtime)):
        try:
            verifier(root)
            note(name, "ok", "Reviewed Spec-Kit pin verified")
        except (ValueError, OSError, KeyError, TypeError) as error:
            note(name, "error" if name == "assets" or required else "warning", str(error))
    integration = config.get("integration", "codex")
    extra = f"SPECKIT_INTEGRATION_{integration.upper()}_EXTRA_ARGS"
    if os.environ.get(extra, "").strip():
        note("environment", "error" if required else "warning",
             extra + " is set; remove it before automatic stages (value withheld)")
    redirects = [key for key in ("SPECIFY_INIT_DIR", "SPECIFY_FEATURE", "SPECIFY_FEATURE_DIRECTORY") if os.environ.get(key)]
    if redirects:
        note("environment", "warning", "Native runner ignores ambient root/feature overrides: " + ", ".join(redirects))
    executable = os.environ.get(f"SPECKIT_INTEGRATION_{integration.upper()}_EXECUTABLE", integration)
    note("assistant", "ok" if shutil.which(executable) else "error" if required else "warning",
         f"{integration} executable {'available' if shutil.which(executable) else 'not found'}; account/model access not tested")
    lock = root/".specify/workflows/poc-bootstrap.lock"
    if lock.exists() or lock.is_symlink():
        note("owner_lock", "error" if required else "warning",
             "Bootstrap owner lock exists; inspect its owner before recovery. Doctor never deletes it")
    git = shutil.which("git")
    if git:
        try:
            result = run_process([git, "rev-parse", "--show-toplevel"], root, timeout=10, env=git_environment())
            same_root = result["returncode"] == 0 and Path(result["stdout"].strip()).resolve() == root
            note("git_root", "ok" if same_root else "warning", "Exact local Git root verified" if same_root else "No exact project Git root; do not mutate a parent repository")
            if same_root:
                revision = run_process([git, "rev-parse", "--verify", "HEAD"], root, timeout=10, env=git_environment())
                note("source_commit", "ok" if revision["returncode"] == 0 else "warning",
                     revision["stdout"].strip() if revision["returncode"] == 0 else "Meaningful baseline not committed yet")
        except OSError:
            note("git_root", "warning", "Git inspection could not start; resolve host tool permissions")
    else:
        note("git_root", "warning", "Git executable not found; offline checks continue")
    note("storage", "ok", f"{shutil.disk_usage(root).free // (1024 * 1024)} MiB available; no new storage gate")
    return dict(project=str(root), status="issues" if any(c["status"] == "error" for c in checks) else "ready", checks=checks)
