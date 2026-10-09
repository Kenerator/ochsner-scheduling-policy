"""Local repository setup; native branching is opt-in, never push or auto-commit."""
import os
from pathlib import Path
import subprocess
import sys
import warnings


def git_environment() -> dict:
    # Ambient Git overrides must not redirect operations into another repository.
    return {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}


def verify_bundled_git(root: Path):
    from .spec_kit_assets import verify_runtime
    verify_runtime(root)
    from specify_cli.extensions import _commands
    if not _commands._locate_bundled_extension("git"):
        raise ValueError("Pinned runtime has no bundled Git extension; no network fallback is permitted")


def initialize_project(root: Path, options: dict):
    if not options["initialize"]:
        return
    try:
        result = subprocess.run(["git", "-c", "init.templateDir=", "init", "--quiet",
                                 "--initial-branch=main", str(root)],
                                env=git_environment(), stdin=subprocess.DEVNULL,
                                capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise ValueError(f"Scaffold preserved at {root}; local Git initialization failed: {error}. "
                         "Resolve Git access or explicitly choose --no-git for a new scaffold") from error
    if result.returncode:
        raise ValueError(f"Scaffold preserved at {root}; local Git initialization failed: {result.stderr.strip()}")
    from .secret_scan import install_hook
    try:
        install_hook(root)
    except ValueError as error:
        # Existing safeguards stay intact; manual scanning remains available.
        warnings.warn(f"Credential hook NOT installed: {error}. See docs/internal/security.md", stacklevel=2)
    if options["extension"]:
        verify_bundled_git(root)
        from .spec_kit_assets import native_argv
        # Upstream registers extension commands only for the active integration.
        # Use its normal switch operation to register both, without --force.
        import json
        selected = json.loads((root / ".specify/integration.json").read_text())["default_integration"]
        other = "claude" if selected == "codex" else "codex"
        for args in (["extension", "add", "git"], ["integration", "use", other],
                     ["integration", "use", selected]):
            operation = " ".join(args)
            recovery = (f"Scaffold preserved at {root}; optional Git setup ({operation}) failed. "
                        "Inspect partial extension/integration state before an explicit retry; "
                        "do not recreate or overwrite this project. See docs/internal/git-setup.md.")
            try:
                result = subprocess.run(native_argv(sys.executable, args), cwd=root,
                                        env=git_environment(), stdin=subprocess.DEVNULL,
                                        capture_output=True, text=True, timeout=60)
            except subprocess.TimeoutExpired as error:
                raise ValueError(f"{recovery} Process timed out after {error.timeout} seconds.") from error
            except OSError as error:
                raise ValueError(f"{recovery} Could not start the local tool: {error}.") from error
            if result.returncode:
                raise ValueError(f"{recovery} Exit {result.returncode}: "
                                 + (result.stderr or result.stdout)[-2000:])
        from .spec_kit_assets import manifest, verify_assets
        # Native integration switching rewrites script modes. Restore only the
        # reviewed executable declarations, then verify bytes rather than rehash.
        for relative in manifest(root).get("executable_files", []):
            (root / relative).chmod(0o755)
        verify_assets(root)
