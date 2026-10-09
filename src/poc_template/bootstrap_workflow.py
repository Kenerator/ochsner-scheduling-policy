"""Native JSON owns workflow progress. Only missing result/question handoff is local."""
import json
import os
from pathlib import Path
import re
import sys
import uuid
from contextlib import contextmanager

from .bootstrap import digest, stage_names, normalize_execution, SPEC_KIT
from .speckit_adapter import bounded_json, project_path, atomic_json, run_process, semantic_dependencies
from .spec_kit_assets import native_argv, verify_runtime, verify_assets
from .stage_guidance import strict_json


def make_definition(through: int, integration: str) -> dict:
    if integration not in {"codex", "claude"}:
        raise ValueError("Choose codex or claude")
    return {"schema_version": "1.0", "workflow": {"id": "poc-bootstrap", "name": "Cumulative PoC bootstrap",
             "version": "1.0.0", "integration": integration},
            "inputs": {"bootstrap_sha": {"type": "string"}, "answers": {"type": "string", "default": "{}"},
                       "retry_token": {"type": "string", "default": ""}},
            "steps": [{"id": stage, "type": "poc-stage", "stage": stage} for stage in stage_names(through)]}


def tool_environment(root: Path) -> dict:
    env = dict(os.environ, PYTHONPATH=str(root/"src"), SPECKIT_PYTHON_EXECUTABLE=sys.executable)
    env["PATH"] = str(Path(sys.executable).parent) + os.pathsep + env.get("PATH", "")
    # Ambient feature/root overrides must not redirect the controlled project.
    for key in ("SPECIFY_INIT_DIR", "SPECIFY_FEATURE", "SPECIFY_FEATURE_DIRECTORY"):
        env.pop(key, None)
    return env


def native(root: Path, args: list[str], parse=True) -> dict:
    timeout = 7200
    if args[:2] in (["workflow", "run"], ["workflow", "resume"]):
        config = bounded_json(project_path(root, ".specify/bootstrap.json"))
        execution = normalize_execution(config["integration"], config.get("execution"))
        timeout = execution["stage_timeout_seconds"] * max(1, len(stage_names(config["through"]))) + 300
    result = run_process(native_argv(sys.executable, args), root, env=tool_environment(root), timeout=timeout,
                         forward_progress=True, structured_stdout=parse)
    if result["returncode"] and result["stderr"].strip():
        diagnostic = "\n".join(line for line in result["stderr"].splitlines() if not line.startswith("Starting Spec-Kit "))
        if diagnostic.strip():
            print(diagnostic[-2000:], file=sys.stderr, flush=True)
    if not parse:
        if result["returncode"] or result["timed_out"]:
            raise ValueError("Native tooling failed: " + (result["stderr"] or result["stdout"])[-2000:])
        return {}
    try:
        state = strict_json(result["stdout"])
        if not isinstance(state, dict) or "status" not in state or "run_id" not in state:
            raise ValueError("Native status lacks run/status")
        return state
    except (ValueError, TypeError) as error:
        raise ValueError("Native run outcome unavailable: " + (result["stderr"] or result["stdout"])[-2000:]) from error


@contextmanager
def owned_lock(root: Path):
    directory = project_path(root, ".specify/workflows")
    directory.mkdir(parents=True, exist_ok=True)
    path = directory/"poc-bootstrap.lock"
    try:
        with path.open("x") as stream:
            stream.write(str(os.getpid()))
    except FileExistsError as error:
        raise ValueError("Bootstrap owner lock exists; inspect the prior process before recovery; no concurrent replay") from error
    try:
        yield
    finally:
        path.unlink()


def config_for(root: Path) -> dict:
    config = bounded_json(project_path(root, ".specify/bootstrap.json"))
    if config.get("spec_kit") != SPEC_KIT:
        raise ValueError("Bootstrap source/version pin changed")
    stage_names(config["through"])
    return config


def install_step(root: Path):
    source = project_path(root, "reference/bootstrap/step")
    installed = project_path(root, ".specify/workflows/steps/poc-stage")
    if installed.exists():
        if any(not (installed/name).is_file() or (installed/name).is_symlink()
               or (installed/name).read_bytes() != (source/name).read_bytes() for name in ("step.yml", "__init__.py")):
            raise ValueError("Conflicting installed poc-stage package; review before replacing")
        return
    native(root, ["workflow", "step", "add", "poc-stage", "--dev", str(source)], parse=False)


def run_bootstrap(root: Path) -> dict:
    root = Path(root).resolve()
    config = config_for(root)
    if config["through"] == 0:
        from .stage_handoff import write_handoff
        return {"status": "completed", "run_id": None, "through": 0, "attempted": [], "completed": [], "questions": [],
                **write_handoff(root, [])}
    verify_runtime(root)
    verify_assets(root)
    with owned_lock(root):
        install_step(root)
        definition = project_path(root, ".specify/workflows/poc-bootstrap.yml")
        atomic_json(definition, make_definition(config["through"], config["integration"]))  # JSON is valid YAML.
        sha = digest((root/".specify/bootstrap.json").read_bytes())
        state = native(root, ["workflow", "run", str(definition), "--input", f"bootstrap_sha={sha}", "--json"])
        return finish_handoff(root, status_bootstrap(root, state["run_id"]))


def finish_handoff(root: Path, state: dict) -> dict:
    from .stage_handoff import write_handoff
    return {**state, **write_handoff(root, state["completed"], state.get("reason", ""))}


def run_directory(root: Path, run_id: str) -> Path:
    if not isinstance(run_id, str) or not re.fullmatch(r"[a-zA-Z0-9_-]+", run_id):
        raise ValueError("Specify the exact native run ID")
    path = project_path(root, f".specify/workflows/runs/{run_id}")
    if not path.is_dir():
        raise ValueError("Native run not found")
    return path


def status_bootstrap(root: Path, run_id: str) -> dict:
    root = Path(root).resolve()
    config = config_for(root)
    directory = run_directory(root, run_id)
    state = native(root, ["workflow", "status", run_id, "--json"])
    stages = ("converge",) if state.get("workflow_id") == "poc-converge" else stage_names(config["through"])
    intents = [stage for stage in stages if (directory/f"poc-{stage}-intent.json").exists()]
    completed = [stage for stage in stages if state.get("steps", {}).get(stage) == "completed"]
    questions, reason = [], state.get("error") or ""
    pending = state.get("current_step_id")
    if pending and (directory/f"poc-{pending}-outcome.json").exists():
        outcome = bounded_json(directory/f"poc-{pending}-outcome.json")["result"]
        questions, reason = outcome["questions"], outcome["summary"]
    if state["status"] == "failed":
        questions, reason = [], state.get("error") or reason
    for stage in intents:
        intent = bounded_json(directory/f"poc-{stage}-intent.json")
        if intent["bootstrap_sha"] != digest((root/".specify/bootstrap.json").read_bytes()):
            raise ValueError("Run was authored with a different bootstrap configuration")
    return {**state, "through": config["through"], "attempted": intents, "completed": completed,
            "questions": questions, "reason": reason}


def resume_bootstrap(root: Path, run_id: str, answers: dict | None = None, *, retry_failed=False) -> dict:
    root = Path(root).resolve()
    verify_runtime(root)
    verify_assets(root)
    state = status_bootstrap(root, run_id)
    if state["status"] == "completed":
        return state
    if retry_failed and state["status"] != "failed":
        raise ValueError("Explicit retry is only for a recorded failed run after its cause is resolved")
    answers = answers or {}
    if state["status"] == "paused":
        required = {question["id"] for question in state["questions"]}
        if set(answers) != required or any(not isinstance(value, str) or not 0 < len(value.strip()) <= 4000 for value in answers.values()):
            raise ValueError("Provide exactly the pending question ID and a non-empty developer answer")
    elif answers:
        raise ValueError("This run has no pending question")
    directory = run_directory(root, run_id)
    pending = state.get("current_step_id")
    retry_args = []
    if retry_failed:
        record = bounded_json(directory/f"poc-{pending}-outcome.json")
        if record["result"]["status"] not in {"failed", "blocked"}:
            raise ValueError("No recorded failed invocation; inspect ambiguous recovery instead")
        if not (directory/f"poc-{pending}-intent.json").exists() and (
                record.get("launch_state") != "not_launched" or
                record.get("bootstrap_sha") != digest((root/".specify/bootstrap.json").read_bytes())):
            raise ValueError("No bound prelaunch failure; inspect ambiguous recovery instead")
        retry_args = ["--input", "retry_token=" + uuid.uuid4().hex]
    intent_path = directory/f"poc-{pending}-intent.json"
    prior_answers = bounded_json(intent_path).get("answers", {}) if intent_path.exists() else {}
    answers = {**prior_answers, **answers}
    with owned_lock(root):
        install_step(root)
        state = native(root, ["workflow", "resume", run_id, "--input", "answers=" + json.dumps(answers), *retry_args, "--json"])
        return finish_handoff(root, status_bootstrap(root, state["run_id"]))


def converge_bootstrap(root: Path, run_id: str) -> dict:
    """Explicit development follow-up; appends tasks but never invokes Implement."""
    root = Path(root).resolve()
    verify_runtime(root)
    verify_assets(root)
    state = status_bootstrap(root, run_id)
    if state["status"] != "completed" or "implement" not in state["completed"]:
        raise ValueError("Converge requires an explicitly selected completed implementation run")
    directory = run_directory(root, run_id)
    evaluated = bounded_json(directory/"poc-implement-outcome.json")["result"]
    dependencies = semantic_dependencies(evaluated)
    with owned_lock(root):
        install_step(root)
        definition = project_path(root, ".specify/workflows/poc-converge.yml")
        workflow = make_definition(0, config_for(root)["integration"])
        workflow["workflow"]["id"] = "poc-converge"
        workflow["inputs"]["dependencies"] = {"type": "string"}
        workflow["inputs"]["feature_dir"] = {"type": "string"}
        workflow["steps"] = [{"id": "converge", "type": "poc-stage", "stage": "converge"}]
        atomic_json(definition, workflow)
        sha = digest((root/".specify/bootstrap.json").read_bytes())
        next_state = native(root, ["workflow", "run", str(definition), "--input", "bootstrap_sha="+sha,
                                  "--input", "dependencies="+json.dumps(dependencies),
                                  "--input", "feature_dir="+evaluated["feature_dir"], "--json"])
        return status_bootstrap(root, next_state["run_id"])
