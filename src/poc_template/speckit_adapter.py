"""A bounded process/result boundary, not an agent or a second workflow engine."""
import hashlib
import json
import os
from pathlib import Path
import queue
import re
import signal
import subprocess
import sys
import threading
import time
import uuid

from .bootstrap import digest, normalize_execution
from .stage_guidance import STAGES, strict_json

RESULT_KEYS = {"run_id", "stage", "token", "status", "summary", "feature_dir", "artifacts", "questions", "findings"}
LIMIT = 1048576
REQUIRED_SEMANTIC_ARTIFACTS = {
    "specify": ["spec.md"], "clarify": ["spec.md"], "plan": ["spec.md", "plan.md"],
    **{stage: ["spec.md", "plan.md", "tasks.md"] for stage in ("tasks", "analyze", "implement", "converge")},
}


def bounded_json(path: Path):
    if path.is_symlink() or not path.is_file() or path.stat().st_size > LIMIT:
        raise ValueError(f"Missing, linked or oversized JSON: {path.name}")
    return strict_json(path.read_text(encoding="utf-8"))


def project_path(root: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute() or ".." in Path(relative).parts:
        raise ValueError("Artifact path must be project-relative")
    path = root / relative
    if not path.resolve().is_relative_to(root) or any(part.is_symlink() for part in (path, *path.parents) if part != root.parent):
        raise ValueError("Artifact path is linked or outside the project")
    return path


def _shape(value, keys, label):
    if not isinstance(value, dict) or set(value) != set(keys):
        raise ValueError(f"Invalid {label} fields")


def validate_stage_result(root: Path, expected_run: str, expected_stage: str, token: str, result: dict) -> dict:
    root = Path(root).resolve()
    _shape(result, RESULT_KEYS, "result")
    if (result["run_id"], result["stage"], result["token"]) != (expected_run, expected_stage, token):
        raise ValueError("Result does not match the current run/stage/token")
    if result["status"] not in {"complete", "input_required", "blocked", "failed"}:
        raise ValueError("Invalid stage status")
    if not isinstance(result["summary"], str) or not 0 < len(result["summary"]) <= 4000:
        raise ValueError("A bounded stage summary is required")
    for key in ("artifacts", "questions", "findings"):
        if not isinstance(result[key], list):
            raise ValueError(f"{key} must be a list")
    if len(result["artifacts"]) > 100 or len(result["findings"]) > 100:
        raise ValueError("Artifact/finding limits exceeded")
    if (result["status"] == "input_required") != bool(result["questions"]):
        raise ValueError("Only input_required carries a question; completion cannot hide one")
    question_ids = set()
    for question in result["questions"]:
        _shape(question, {"id", "text", "options", "recommendation"}, "question")
        if not isinstance(question["id"], str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}", question["id"]):
            raise ValueError("Invalid question ID")
        if question["id"] in question_ids:
            raise ValueError("Duplicate question ID")
        question_ids.add(question["id"])
        if not isinstance(question["options"], list) or not 2 <= len(question["options"]) <= 4:
            raise ValueError("A question needs 2–4 options and a recommendation")
        if any(not isinstance(text, str) or not text.strip() or len(text) > 2000
               for text in [question["text"], question["recommendation"], *question["options"]]):
            raise ValueError("Question text/options must be bounded strings")
    for finding in result["findings"]:
        _shape(finding, {"id", "severity", "text"}, "finding")
        if finding["severity"] not in {"critical", "high", "medium", "low"} or any(
                not isinstance(finding[key], str) or not 0 < len(finding[key]) <= 4000 for key in ("id", "text")):
            raise ValueError("Invalid finding")
    feature = result["feature_dir"]
    if not isinstance(feature, str):
        raise ValueError("feature_dir must be a string")
    if feature:
        path = project_path(root, feature)
        if len(Path(feature).parts) != 2 or Path(feature).parts[0] != "specs" or not path.is_dir():
            raise ValueError("Feature directory must be an existing specs/<feature> directory")
    required = REQUIRED_SEMANTIC_ARTIFACTS.get(expected_stage, []) if result["status"] == "complete" else []
    if required and not feature:
        raise ValueError("Completion requires a bound feature directory")
    reported_paths = {item.get("path") for item in result["artifacts"]
                      if isinstance(item, dict) and isinstance(item.get("path"), str)}
    # Prerequisites are known locally; a model need not repeat their metadata.
    artifact_items = [*result["artifacts"], *[
        dict(path=f"{feature}/{name}", sha256="") for name in required if f"{feature}/{name}" not in reported_paths]]
    artifacts, verified_artifacts, seen_paths = {}, [], set()
    for artifact in artifact_items:
        _shape(artifact, {"path", "sha256"}, "artifact")
        path = project_path(root, artifact["path"])
        if artifact["path"] in seen_paths:
            raise ValueError("Duplicate artifact")
        seen_paths.add(artifact["path"])
        # A visible question can mention a future output, but it is not evidence.
        if result["status"] == "input_required" and not path.exists() and artifact["sha256"] == "":
            continue
        if not path.is_file() or path.stat().st_size > LIMIT or not isinstance(artifact["sha256"], str):
            raise ValueError("Missing or oversized artifact")
        data = path.read_bytes()
        actual_digest = digest(data)
        if artifact["path"] in artifacts or artifact["sha256"] not in {"", actual_digest}:
            raise ValueError("Duplicate artifact or changed artifact bytes")
        artifacts[artifact["path"]] = data.decode("utf-8")
        verified_artifacts.append({**artifact, "sha256": actual_digest})
    result = {**result, "artifacts": verified_artifacts}
    if result["status"] != "complete":
        return result
    findings = list(result["findings"])
    def note(text, severity="medium"):
        findings.append(dict(id="content-review", severity=severity, text=text))
    spec = artifacts.get(f"{feature}/spec.md", "")
    if required and (not re.search(r"\bFR-\d+", spec) or not re.search(r"\bSC-\d+", spec)
                     or not re.search(r"scenario|given", spec, re.I)):
        note("Review the specification's requirements, scenarios and success criteria; format heuristics are not semantic proof.")
    if "[NEEDS CLARIFICATION" in spec:
        note("The specification has pending choices for the normal Clarify stage.")
    plan = artifacts.get(f"{feature}/plan.md", "")
    if "plan.md" in required and re.search(r"\[NEEDS CLARIFICATION|^.*:\s*\[(?:e\.g\.|INSERT|PROJECT NAME)", plan, re.I | re.M):
        note("Plan contains unresolved choices or unfilled template fields; review before dependent stages.", "high")
    if "plan.md" in required and any(not re.search(pattern, plan, re.I) for pattern in
                                    (r"python|typescript|rust|go\b|language", r"architect|structure", r"test|verif")):
        note("Review the plan's stack, architecture and verification approach; wording alone cannot establish completeness.")
    tasks = artifacts.get(f"{feature}/tasks.md", "")
    if "tasks.md" in required and (not re.search(r"\bT\d{3}\b", tasks) or not re.search(r"test", tasks, re.I)
                                   or not re.search(r"depend|order|phase", tasks, re.I)):
        note("Review actionable tasks, meaningful tests and dependency order; format heuristics are advisory.")
    if expected_stage == "implement" and re.search(r"- \[ \].*\bT\d{3}\b", tasks):
        note("Implementation still has incomplete agreed tasks.", "high")
    result = {**result, "findings": findings}
    if any(item["severity"] in {"critical", "high"} for item in findings):
        return {**result, "status": "blocked", "summary": "Content findings require developer review before advancement"}
    return result


def claude_diagnostics(envelope: dict) -> dict:
    """Retain permission visibility without retaining commands, inputs or secrets."""
    denials = envelope.get("permission_denials", [])
    denials = denials if isinstance(denials, list) else []
    names = {item.get("tool_name") for item in denials[:100]
             if isinstance(item, dict) and isinstance(item.get("tool_name"), str)
             and re.fullmatch(r"[A-Za-z0-9_.-]{1,80}", item["tool_name"])}
    result = dict(permission_denial_count=min(len(denials), 10000), denied_tools=sorted(names))
    session_id = envelope.get("session_id", "")
    if isinstance(session_id, str) and re.fullmatch(r"[a-fA-F0-9-]{36}", session_id):
        result["session_id"] = session_id
    return result


def codex_error_summary(stdout: str) -> str:
    """Classify service errors without echoing arbitrary error fields or tool output."""
    for line in stdout.splitlines():
        try:
            event = strict_json(line)
        except ValueError:
            continue
        if not isinstance(event, dict) or event.get("type") != "error":
            continue
        message = event.get("message", "")
        if not isinstance(message, str):
            continue
        match = re.search(r"The '([A-Za-z0-9][A-Za-z0-9._:/-]{0,99})' model is not supported when using Codex with a ChatGPT account", message)
        if match:
            return f"Codex model {match[1]} is not supported by this client/account connection; check native model access and client version"
        return "Codex reported a native error; inspect account/client diagnostics (arbitrary error details withheld)"
    return ""


def run_process(argv: list[str], root: Path, timeout: float = 900, env: dict | None = None,
                forward_progress=False, structured_stdout=False) -> dict:
    """Drain both pipes in bounded chunks. A timeout terminates only this owned group."""
    process = subprocess.Popen(argv, cwd=root, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, shell=False, start_new_session=True)
    chunks = queue.Queue(maxsize=16)
    def drain(stream, key):
        try:
            while data := os.read(stream.fileno(), 4096):
                chunks.put((key, data))
        finally:
            chunks.put((key, None))
            stream.close()
    for key, stream in (("stdout", process.stdout), ("stderr", process.stderr)):
        threading.Thread(target=drain, args=(stream, key), daemon=True).start()
    tails = {"stdout": b"", "stderr": b""}
    finished, timed_out, deadline = set(), False, time.monotonic() + timeout
    progress, stdout_size, overflow = b"", 0, False
    # EOF is not process completion: a child may close both pipes and keep working.
    while len(finished) < 2 or process.poll() is None:
        if time.monotonic() > deadline and not timed_out:
            timed_out = True
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        try:
            key, data = chunks.get(timeout=.05)
        except queue.Empty:
            continue
        if data is None:
            finished.add(key)
        else:
            if key == "stdout":
                stdout_size += len(data)
                overflow = structured_stdout and stdout_size > LIMIT
            tails[key] = (tails[key] + data)[-(LIMIT if structured_stdout and key == "stdout" else 32768):]
            if forward_progress and key == "stderr":
                progress = (progress + data)[-8192:]
                while b"\n" in progress:
                    line, progress = progress.split(b"\n", 1)
                    if line.startswith(b"Starting Spec-Kit "):
                        print(line.decode("utf-8", "replace"), file=sys.stderr, flush=True)
    returncode = process.wait()
    if overflow:
        raise ValueError("Structured stdout exceeds 1 MiB; result preserved only as a failed invocation")
    return {"returncode": returncode, "timed_out": timed_out,
            **{key: data.decode("utf-8", "replace") for key, data in tails.items()}}


def atomic_json(path: Path, value: dict):
    project_path(path.parent.resolve(), path.name)
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".new")
    with temporary.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def source_snapshot(root: Path) -> dict:
    """Development fingerprints, including root config; stream large files, not memory."""
    paths = list(root.iterdir())
    for folder in ("src", "tests", "specs", "docs", ".specify/memory"):
        paths.extend((root/folder).rglob("*"))
    snapshots = {}
    for path in paths:
        if path.is_file() and not path.is_symlink() and "__pycache__" not in path.parts:
            with path.open("rb") as stream:
                snapshots[path.relative_to(root).as_posix()] = hashlib.file_digest(stream, "sha256").hexdigest()
    return snapshots


def semantic_dependencies(result: dict) -> dict:
    """Reported metadata/docs are evidence, not automatically frozen prerequisites."""
    names = {result["feature_dir"] + "/" + name for name in ("spec.md", "plan.md", "tasks.md")}
    return {item["path"]: item["sha256"] for item in result["artifacts"] if item["path"] in names}


def invoke_stage(root: Path, run_id: str, stage: str, inputs: dict) -> dict:
    """Record known prelaunch failures without laundering an interrupted launch."""
    root = Path(root).resolve()
    if stage not in (*STAGES, "converge") or not re.fullmatch(r"[a-zA-Z0-9_-]+", run_id):
        raise ValueError("Invalid run/stage")
    directory = project_path(root, f".specify/workflows/runs/{run_id}")
    intent_path = directory/f"poc-{stage}-intent.json"
    outcome_path = directory/f"poc-{stage}-outcome.json"
    prior_token = bounded_json(intent_path)["token"] if intent_path.exists() else None
    prior_outcome = bounded_json(outcome_path) if outcome_path.exists() else None
    if prior_outcome and not intent_path.exists() and (
            prior_outcome.get("launch_state") != "not_launched" or
            prior_outcome.get("bootstrap_sha") != inputs.get("bootstrap_sha")):
        raise ValueError("Prelaunch outcome binding changed; inspect before retrying")
    launch = {"started": False}
    try:
        return _invoke_stage(root, run_id, stage, inputs, launch)
    except (ValueError, OSError, KeyError, TypeError) as error:
        current = bounded_json(intent_path) if intent_path.exists() else None
        if launch["started"] or (prior_token and (current is None or current["token"] == prior_token)):
            raise  # Existing/possibly launched intent still needs its original recovery.
        directory.mkdir(parents=True, exist_ok=True)
        if prior_outcome and not intent_path.exists():
            attempts = directory/f"poc-{stage}-attempts"
            attempts.mkdir(exist_ok=True)
            atomic_json(attempts/(prior_outcome["token"]+"-outcome.json"), prior_outcome)
        result = dict(run_id=run_id, stage=stage, token=current["token"] if current else uuid.uuid4().hex,
                      status="blocked", summary=str(error)[:4000], feature_dir="", artifacts=[], questions=[], findings=[])
        atomic_json(outcome_path, {"token": result["token"], "result": result,
                                  "launch_state": "not_launched", "bootstrap_sha": inputs.get("bootstrap_sha")})
        return result


def _invoke_stage(root: Path, run_id: str, stage: str, inputs: dict, launch: dict) -> dict:
    from specify_cli.integrations import get_integration
    root = Path(root).resolve()
    if stage not in (*STAGES, "converge") or not re.fullmatch(r"[a-zA-Z0-9_-]+", run_id):
        raise ValueError("Invalid run/stage")
    config_path = project_path(root, ".specify/bootstrap.json")
    config = bounded_json(config_path)
    config_sha = digest(config_path.read_bytes())
    if inputs.get("bootstrap_sha") != config_sha:
        raise ValueError("Bootstrap configuration changed; start a new project/run instead of amending completion")
    integration = config["integration"]
    execution = normalize_execution(integration, config.get("execution"))
    if os.environ.get(f"SPECKIT_INTEGRATION_{integration.upper()}_EXTRA_ARGS", "").strip():
        raise ValueError("Bootstrap uses native default argv; remove integration extra args before execution")
    for relative, expected in config.get("control_hashes", {}).items():
        if digest(project_path(root, relative).read_bytes()) != expected:
            raise ValueError(f"Bootstrap control changed: {relative}; start a reviewed new run")
    for item in config["intake"]:
        if digest(project_path(root, item["path"]).read_bytes()) != item["sha256"]:
            raise ValueError("Intake changed after preview")
    original_dependencies = inputs.get("dependencies", {})
    dependencies = dict(original_dependencies)
    feature_dir = inputs.get("feature_dir", "")
    if not feature_dir and dependencies:
        feature_dir = "/".join(next(path for path in dependencies if path.startswith("specs/") and path.endswith("/spec.md")).split("/")[:2])
    run_dir = project_path(root, f".specify/workflows/runs/{run_id}")
    run_dir.mkdir(parents=True, exist_ok=True)
    intent_path = run_dir / f"poc-{stage}-intent.json"
    outcome_path = run_dir / f"poc-{stage}-outcome.json"
    answers = inputs.get("answers", {})
    if not intent_path.exists() and outcome_path.exists():
        prior = bounded_json(outcome_path)
        if prior.get("launch_state") != "not_launched" or prior.get("bootstrap_sha") != config_sha:
            raise ValueError("Prelaunch outcome binding changed; inspect before retrying")
        if not inputs.get("retry_token"):
            return prior["result"]
        attempts = project_path(root, f".specify/workflows/runs/{run_id}/poc-{stage}-attempts")
        attempts.mkdir(exist_ok=True)
        atomic_json(attempts/(prior["token"]+"-outcome.json"), prior)
    if intent_path.exists():
        intent = bounded_json(intent_path)
        if intent["bootstrap_sha"] != config_sha or intent["dependencies"] != original_dependencies:
            raise ValueError("Invocation binding changed; reconcile the interrupted run")
        if not outcome_path.exists():
            raise ValueError("Interrupted invocation has no final outcome; inspect before retrying (no blind replay)")
        outcome = bounded_json(outcome_path)
        if outcome["token"] != intent["token"]:
            raise ValueError("Ambiguous invocation outcome")
        prior = validate_stage_result(root, run_id, stage, intent["token"], outcome["result"])
        if prior["status"] == "complete":
            evaluated = {item["path"]: item["sha256"] for item in prior["artifacts"]}
            for relative, expected in dependencies.items():
                if digest(project_path(root, relative).read_bytes()) != evaluated.get(relative, expected):
                    raise ValueError(f"Stale recovery dependency: {relative}")
            return prior
        retry = (prior["status"] in {"failed", "blocked"} and inputs.get("retry_token")
                 and inputs["retry_token"] != intent.get("retry_token", ""))
        if not retry and (prior["status"] != "input_required" or prior["questions"][0]["id"] not in answers):
            return prior
        if feature_dir and prior["feature_dir"] and prior["feature_dir"] != feature_dir:
            raise ValueError("Paused result changed the feature directory")
        feature_dir = prior["feature_dir"] or intent.get("feature_dir", feature_dir)
        dependencies.update(semantic_dependencies(prior))
        attempts = project_path(root, f".specify/workflows/runs/{run_id}/poc-{stage}-attempts")
        attempts.mkdir(exist_ok=True)
        atomic_json(attempts/(intent["token"]+"-intent.json"), intent)
        atomic_json(attempts/(intent["token"]+"-outcome.json"), outcome)
    for relative, expected in dependencies.items():
        if digest(project_path(root, relative).read_bytes()) != expected:
            raise ValueError(f"Stale dependency: {relative}")
    token = uuid.uuid4().hex
    before = source_snapshot(root)
    origin_before = intent.get("origin_before", intent.get("before", before)) if intent_path.exists() else before
    intent = {"token": token, "bootstrap_sha": config_sha, "dependencies": original_dependencies,
              "before": before, "origin_before": origin_before, "answers": answers, "pid": os.getpid(),
              "feature_dir": feature_dir, "retry_token": inputs.get("retry_token", "")}
    atomic_json(intent_path, intent)  # Durable before launch; absence of outcome must never authorize replay.
    schema_path = project_path(root, "reference/bootstrap/result-schema.json")
    final_path = run_dir / f"poc-{stage}-{token}.json"
    contract = {"run_id": run_id, "stage": stage, "token": token, "answers": answers,
                "result_schema": str(schema_path), "dependencies": dependencies, "feature_dir": feature_dir,
                "path_format": "project-relative POSIX",
                "required_semantic_artifact_names": REQUIRED_SEMANTIC_ARTIFACTS[stage]}
    # Let the installed native skill own its prerequisites/questions/workflow.
    # The extra text below is only the non-interactive transport/result boundary.
    prompt = ((config["feature_description"] + "\n") if stage == "specify" else "")
    prompt += config["effective_guidance"].get(stage, "")
    prompt += ("\nBootstrap handoff: execute this installed native stage as written. "
               "Selected local stage execution is authorized, subject to normal tool permissions. "
               "No external publication, deployment, credentials or permission bypass. "
               "Do not change bootstrap controls, managed assets or Constitution. "
               "Continue the contract feature_dir when present; answers are explicit developer responses, not expanded authority. "
               "After execution, return the result schema with project-relative paths and empty sha256 values for local hashing. "
               "Include existing required artifacts; a native question uses input_required and may mention a future file. "
               "Report failures/findings honestly, without repairing them merely to satisfy the result contract.")
    if stage == "implement":
        prompt += " This adapter's supported verification profile is Python unittest with test_feature*.py tests."
    prompt += "\nPOC_RESULT_CONTRACT\n" + json.dumps(contract)
    agent = get_integration(integration)
    invocation = agent.build_command_invocation(f"speckit.{stage}", prompt)
    argv = agent.build_exec_args(invocation, project_root=root, output_json=True)
    if not argv:
        raise ValueError("Integration does not support native execution")
    if integration == "codex":
        if execution["model"] is not None:
            argv += ["--model", execution["model"]]
        if execution["reasoning_effort"] is not None:
            argv += ["--config", "model_reasoning_effort=" + json.dumps(execution["reasoning_effort"])]
        argv += ["--sandbox", "read-only" if stage == "analyze" else "workspace-write", "--skip-git-repo-check",
                 "--output-schema", str(schema_path), "--output-last-message", str(final_path)]
    else:
        argv += ["--permission-mode", "acceptEdits", "--json-schema", schema_path.read_text()]
    env = dict(os.environ, SPECKIT_PYTHON_EXECUTABLE=sys.executable)
    env["PATH"] = str(Path(sys.executable).parent) + os.pathsep + env.get("PATH", "")
    env["PYTHONPATH"] = str(root/"src")
    if dependencies:
        env["SPECIFY_FEATURE_DIRECTORY"] = str(project_path(root, feature_dir))
    print(f"Starting Spec-Kit {stage} ({integration}); run {run_id}", file=sys.stderr, flush=True)
    fallback = dict(run_id=run_id, stage=stage, token=token, status="blocked", summary="Stage did not complete",
                    feature_dir="", artifacts=[], questions=[], findings=[])
    try:
        launch["started"] = True
        process = run_process(argv, root, timeout=execution["stage_timeout_seconds"], env=env,
                              structured_stdout=integration == "claude")
        if process["timed_out"] or process["returncode"] != 0:
            diagnostic = codex_error_summary(process["stdout"]) if integration == "codex" else ""
            raise ValueError("Agent timeout" if process["timed_out"] else
                             f"Agent exited {process['returncode']}: {diagnostic or (process['stderr'] or process['stdout'])[-2000:]}")
        if integration == "codex":
            result = bounded_json(final_path)
        else:
            envelope = strict_json(process["stdout"])
            if isinstance(envelope, dict):
                atomic_json(run_dir / f"poc-{stage}-{token}-diagnostics.json", claude_diagnostics(envelope))
            if not isinstance(envelope, dict) or envelope.get("is_error"):
                raise ValueError("Claude reported an error or no structured result")
            result = envelope.get("structured_output")
            if result is None:
                raise ValueError("Claude did not return structured_output")
            atomic_json(final_path, result)  # Preserve bounded structured diagnostics, not acceptance.
        result = validate_stage_result(root, run_id, stage, token, result)
        if digest(config_path.read_bytes()) != config_sha or any(
                digest(project_path(root, relative).read_bytes()) != expected for relative, expected in config.get("control_hashes", {}).items()):
            raise ValueError("Agent changed bootstrap controls/configuration; reconcile before proceeding")
        if feature_dir and result["feature_dir"] != feature_dir:
            raise ValueError("Agent changed the feature directory within this run")
        after = source_snapshot(root)
        if stage == "analyze" and before != after:
            raise ValueError("Analyze changed project sources/artifacts; reconcile before proceeding")
        if result["status"] == "complete" and stage in {"specify", "plan", "tasks"}:
            primary = f"{result['feature_dir']}/" + {"specify": "spec.md", "plan": "plan.md", "tasks": "tasks.md"}[stage]
            if origin_before.get(primary) == after.get(primary):
                raise ValueError("Unchanged old artifact cannot prove a newly invoked stage")
        if result["status"] == "complete":
            prerequisite = project_path(root, ".specify/scripts/python/check_prerequisites.py")
            check_env = dict(env, SPECIFY_FEATURE_DIRECTORY=str(root/result["feature_dir"]), SPECIFY_FEATURE_NO_PERSIST="1")
            checked = run_process([sys.executable, str(prerequisite), "--paths-only", "--json"], root, timeout=30, env=check_env)
            paths = strict_json(checked["stdout"])
            if checked["returncode"] or Path(paths["FEATURE_DIR"]).resolve() != (root/result["feature_dir"]).resolve():
                raise ValueError("Native prerequisite feature binding differs from result")
        if result["status"] == "complete" and stage == "implement":
            changed = [path for path, sha in after.items() if origin_before.get(path) != sha]
            if not any(path.startswith("src/") for path in changed) or not any(path.startswith("tests/") for path in changed):
                raise ValueError("Implementation lacks current-run code and meaningful test changes")
            verified = run_process([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_feature*.py", "-v"], root, timeout=120, env=env)
            if verified["returncode"] or not re.search(r"Ran [1-9][0-9]* tests?", verified["stderr"]):
                raise ValueError("Accepted Python unittest verification failed or executed no tests: " + verified["stderr"][-2000:])
    except (ValueError, OSError, KeyError, TypeError) as error:
        result = {**fallback, "summary": str(error)[:4000]}
    atomic_json(outcome_path, {"token": token, "result": result})
    return result
