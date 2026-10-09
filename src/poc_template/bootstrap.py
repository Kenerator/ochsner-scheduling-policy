"""Preview first, copy an explicit public surface, and never overwrite a project."""
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from typing import BinaryIO

from .persona_catalog import Catalog, validate_data
from .persona_render import render_selection, resolve_sources, definitions, text as persona_text
from .stage_guidance import STAGES, strict_json, extract_guidance, normalize_guidance, effective_guidance
from .user_stories import STORIES_PATH, SUPPORT_STEP, render_story_drafts
from .rfp_intake import INDEX as RFP_INDEX, MANIFEST as RFP_MANIFEST, snapshot_rfp

SPEC_KIT = {"version": "1.1.0", "revision": "f1d3a4f8337ebbd3ae22760a9c12e3352b93a175"}
PUBLIC_DIRS = ("src", "tests", "docs", "reference", "policies", "assets/ui", ".agents/skills", ".claude/skills",
               ".specify/scripts", ".specify/templates", ".specify/integrations", ".specify/memory")
PUBLIC_FILES = ("README.md", "AGENTS.md", "CLAUDE.md", "pyproject.toml", ".gitignore", ".gitattributes",
                ".specify/integration.json", ".specify/init-options.json", ".specify/.gitignore")
EXCLUDED = {".git", ".venv", ".superpowers", "__pycache__", "build", "dist", "node_modules"}
PRIVATE_DIRS = (Path("docs/internal/private"), Path("docs/product/intake/private"),
                Path("docs/product/RFP/source"), Path(RFP_MANIFEST))


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def stage_names(through: int) -> tuple[str, ...]:
    if type(through) is not int or not 0 <= through <= 6:
        raise ValueError("Choose a cumulative target from 0 through 6")
    return STAGES[:through]


def normalize_execution(integration: str, options: dict | None = None) -> dict:
    """Typed per-project choices; never arbitrary argv or permission configuration."""
    options = {} if options is None else options
    if not isinstance(options, dict) or set(options) - {"model", "reasoning_effort", "stage_timeout_seconds"}:
        raise ValueError("Execution accepts only model, reasoning_effort and stage_timeout_seconds")
    model, effort = options.get("model"), options.get("reasoning_effort")
    if model is not None and (not isinstance(model, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,99}", model)):
        raise ValueError("Model must be a model identifier, not command arguments")
    if effort is not None and (not isinstance(effort, str) or effort not in {"low", "medium", "high", "xhigh", "max", "ultra"}):
        raise ValueError("Choose a supported reasoning effort; model availability is checked by the native CLI")
    if integration != "codex" and (model is not None or effort is not None):
        raise ValueError("Explicit model/reasoning options currently support Codex only")
    timeout = options.get("stage_timeout_seconds", 900)
    if type(timeout) is not int or not 1 <= timeout <= 86400:
        raise ValueError("Stage timeout must be an integer from 1 through 86400 seconds")
    return dict(model=model, reasoning_effort=effort, stage_timeout_seconds=timeout)


def safe_destination(destination: Path) -> Path:
    path = Path(destination).absolute()
    def unsafe_link(part):
        if not part.is_symlink():
            return False
        # macOS exposes its ordinary temp tree through protected OS aliases.
        aliases = {Path("/var"): Path("/private/var"), Path("/tmp"): Path("/private/tmp")}
        return not (sys.platform == "darwin" and part in aliases and part.lstat().st_uid == 0
                    and part.resolve() == aliases[part])
    if any(unsafe_link(part) for part in (path, *path.parents)):
        raise ValueError("Refusing a symlinked destination or parent")
    if path.exists():
        raise ValueError("Destination already exists; choose a new directory")
    if not path.parent.is_dir():
        raise ValueError("Destination parent must already exist")
    return path.resolve()


def public_files(root: Path) -> dict[str, bytes]:
    files = {}
    candidates = [root / name for name in PUBLIC_FILES]
    for name in PUBLIC_DIRS:
        directory = root / name
        if directory.is_dir() and not directory.is_symlink():
            candidates.extend(directory.rglob("*"))
    for path in candidates:
        relative = path.relative_to(root)
        # Generated applications need starter behavior tests, not the bootstrapper's
        # own maintenance suite (which assumes this template's seed catalog/runtime).
        if relative.parts[0] == "tests" and relative.as_posix() != "tests/test_demo.py":
            continue
        if (not path.is_file() or any(part.is_symlink() for part in (path, *path.parents) if part != root.parent)
                or any(part in EXCLUDED or part.endswith(".egg-info") for part in relative.parts)
                or any(relative.is_relative_to(private) for private in PRIVATE_DIRS)
                or path.name.startswith(".env") or path.name.lower() in {"credentials.json", "secrets.json"}
                or path.suffix.lower() in {".pyc", ".pyo", ".pem", ".p12", ".pfx"}):
            continue
        files[relative.as_posix()] = path.read_bytes()
    return files


def select_native_integration(files: dict[str, bytes], integration: str) -> None:
    """Derive only the new project's native default; no runtime or stage call."""
    changed = {}
    for relative, keys in ((".specify/integration.json", ("integration", "default_integration")),
                           (".specify/init-options.json", ("ai", "integration"))):
        if relative not in files:
            continue
        state = strict_json(files[relative].decode())
        for key in keys:
            state[key] = integration
        files[relative] = (json.dumps(state, indent=2) + "\n").encode()
        changed[relative] = digest(files[relative])
    # Native shared templates use the selected assistant's command prefix.
    # Derive only those references in a fresh scaffold, not user-authored prose.
    prefix = "$" if integration == "codex" else "/"
    shared = {}
    for relative in list(files):
        if relative.startswith(".specify/templates/") and relative.endswith(".md"):
            before = files[relative]
            files[relative] = re.sub(rb"[/$]speckit-", lambda _: (prefix + "speckit-").encode(), before)
            if files[relative] != before:
                shared[relative] = changed[relative] = digest(files[relative])
    # These four native scripts embed invocation spelling as well. The bounded
    # transformations are compared with actual native integration switching in tests.
    for relative in (".specify/scripts/python/common.py", ".specify/scripts/bash/common.sh",
                     ".specify/scripts/bash/setup-tasks.sh", ".specify/scripts/bash/check-prerequisites.sh"):
        if relative not in files:
            continue
        before = files[relative]
        if relative.endswith("common.py"):
            after = re.sub(rb'return f"[/$]speckit\{separator\}\{name\}"',
                           lambda _: ('return f"' + prefix + 'speckit{separator}{name}"').encode(), before)
        elif relative.endswith("common.sh"):
            after = re.sub(rb"printf '[/$]speckit%s%s", lambda _: ("printf '" + prefix + "speckit%s%s").encode(), before)
        else:
            replacement = b"\\$speckit-" if integration == "codex" else b"/speckit-"
            after = re.sub(rb"\\?[/$]speckit-", lambda _: replacement, before)
        if after != before:
            files[relative] = after
            shared[relative] = changed[relative] = digest(after)
    native_record = ".specify/integrations/speckit.manifest.json"
    if shared and native_record in files:
        state = strict_json(files[native_record].decode())
        state["files"].update(shared)
        files[native_record] = (json.dumps(state, indent=2) + "\n").encode()
        changed[native_record] = digest(files[native_record])
    record_path = "reference/bootstrap/spec-kit.json"
    if record_path in files and changed:
        record = strict_json(files[record_path].decode())
        record["files"].update(changed)
        files[record_path] = (json.dumps(record, indent=2, sort_keys=True) + "\n").encode()


def render_research(document: str, source_ids: list[str], sources: dict, options: dict) -> str:
    resolved = resolve_sources({"references": source_ids}, sources,
                               references_enabled=options.get("enabled", True),
                               exclude=options.get("exclude", []), overrides=options.get("overrides", {}))
    # Only catalog-backed generated footnotes are changed; other authors' notes stay intact.
    for identifier in sources:
        document = re.sub(r"^\[\^" + re.escape(identifier) + r"\]:[^\n]*\n?", "", document, flags=re.M)
        if identifier not in resolved:
            document = document.replace(f"[^{identifier}]", "")
    return document.rstrip() + ("\n\n" + definitions(resolved) if resolved else "") + "\n"


def preview_bootstrap(template_root: Path, destination: Path, name: str, inputs: list[Path],
                      selections: list[str], through: int, integration: str,
                      reference_options: dict | None = None, guidance: dict | None = None,
                      execution: dict | None = None, stdin_stream: BinaryIO | None = None,
                      persona_catalog: Path | None = None, git_options: dict | None = None,
                      rfp: Path | None = None) -> dict:
    stages = stage_names(through)
    if not isinstance(name, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,79}", name):
        raise ValueError("Use a lowercase alphanumeric/hyphen technical slug (1–80 characters), e.g. --name poc-uat-001-01; destination/display capitalization may differ")
    if integration not in {"codex", "claude"}:
        raise ValueError("Choose codex or claude")
    execution = normalize_execution(integration, execution)
    git_options = {"initialize": True, "extension": False} if git_options is None else git_options
    if (not isinstance(git_options, dict) or set(git_options) != {"initialize", "extension"}
            or any(type(value) is not bool for value in git_options.values())):
        raise ValueError("Git options require boolean initialize and extension choices")
    if git_options["extension"] and not git_options["initialize"]:
        raise ValueError("Native Git extension requires local Git initialization")
    if git_options["extension"]:
        from .project_git import verify_bundled_git
        verify_bundled_git(template_root)
    destination = safe_destination(destination)
    root = Path(template_root).resolve()
    if (root / "reference/bootstrap/spec-kit.json").exists():
        from .spec_kit_assets import verify_assets
        verify_assets(root)
    files = public_files(root)
    select_native_integration(files, integration)
    executable = [name for name in files if (root / name).stat().st_mode & 0o100]
    intakes, total, marked_guidance, descriptions = [], 0, [], []
    if sum(Path(path) == Path("-") for path in inputs) > 1:
        raise ValueError("Use --input - only once; stdin cannot be replayed")
    for number, path in enumerate(inputs, 1):
        path = Path(path)
        if path == Path("-"):
            if stdin_stream is None:
                raise ValueError("--input - requires a stdin stream")
            # Bound the read itself; never buffer an unbounded pipe before validation.
            data = stdin_stream.read(1048576 + 1)
            suffix = ".md"
        else:
            if path.suffix.lower() not in {".md", ".txt", ".json", ".yaml", ".yml"} or not path.is_file() or path.is_symlink():
                raise ValueError("Intake must be a regular UTF-8 Markdown/text/JSON/YAML file; convert other formats first")
            if path.stat().st_size > 1048576:
                raise ValueError("Intake exceeds 1 MiB; preprocess explicitly")
            data = path.read_bytes()
            suffix = path.suffix.lower()
        if len(data) > 1048576:
            raise ValueError("Intake exceeds 1 MiB; preprocess explicitly")
        total += len(data)
        if total > 16777216:
            raise ValueError("Total intake exceeds 16 MiB; preprocess explicitly")
        try:
            document = data.decode("utf-8")
        except UnicodeDecodeError as error:
            raise ValueError("Intake must be UTF-8 text") from error
        if path == Path("-") and not document.strip():
            raise ValueError("Stdin intake is empty; provide content before EOF")
        body, marked = extract_guidance(document)
        descriptions.append(body)
        if marked is not None:
            marked_guidance.append(marked)
        relative = f"docs/product/intake/{number:03d}{suffix}"
        files[relative] = data
        intakes.append({"path": relative, "sha256": digest(data)})
    rfp_snapshot = snapshot_rfp(rfp, total) if rfp is not None else None
    if rfp_snapshot is not None:
        files.update(rfp_snapshot["files"])
        # The generic tracked index exposes local sources without leaking their
        # contents/names into handoff prompts or generated story indexes.
        if RFP_INDEX not in files:
            raise ValueError("Template is missing the RFP index")
        intakes.append({"path": RFP_INDEX, "sha256": digest(files[RFP_INDEX])})
        intakes.extend({"path": path, "sha256": digest(data), "context": False}
                       for path, data in sorted(rfp_snapshot["files"].items()))
        descriptions.append("Include the client requirements indexed by " + RFP_INDEX + ".")
    if len(marked_guidance) + (guidance is not None) > 1:
        raise ValueError("Choose one guidance file or intake block, not competing configurations")
    guidance = normalize_guidance(guidance if guidance is not None else (marked_guidance[0] if marked_guidance else None))
    pack_path = root / "reference/bootstrap/guidance/default.json"
    pack = strict_json(pack_path.read_text()) if pack_path.exists() else {}
    effective = {stage: effective_guidance(guidance, stage, pack) for stage in STAGES}
    options = reference_options or {}
    sources_path = root / "reference/research/sources.json"
    sources = strict_json(sources_path.read_text()) if sources_path.exists() else {}
    snapshots, external_data, persona_source = [], None, None
    if persona_catalog is not None:
        if not selections:
            raise ValueError("--persona-catalog requires at least one pinned --persona selection")
        path = Path(persona_catalog)
        if path.is_symlink() or not path.is_file():
            raise ValueError("External persona catalog must be a regular JSON file")
        with path.open("rb") as stream:
            raw = stream.read(1048576 + 1)
        if len(raw) > 1048576:
            raise ValueError("External persona catalog exceeds 1 MiB")
        external_data = strict_json(raw.decode("utf-8"))
        if not isinstance(external_data, dict):
            raise ValueError("External persona catalog must be a JSON object")
        validate_data(external_data)
        persona_source = digest(raw)
        # A project catalog inside the public tree is input, not a second export.
        source_path = path.resolve()
        if source_path.is_relative_to(root):
            source_relative = source_path.relative_to(root).as_posix()
            files.pop(source_relative, None)
            executable = [item for item in executable if item != source_relative]
    if selections:
        catalog = Catalog(root / "reference/personas/catalog.json") if external_data is None else None
        for selection in selections:
            match = re.fullmatch(r"([a-z0-9-]+):([a-z0-9-]+)@([1-9][0-9]*)", selection)
            if not match:
                raise ValueError("Use a pinned namespace:id@revision persona")
            namespace, identifier, revision = match.groups()
            if external_data is None:
                snapshot = catalog.get(identifier, int(revision))
            else:
                try:
                    snapshot = external_data["personas"][identifier]["revisions"][revision]
                except KeyError as error:
                    raise ValueError(f"Unknown pinned persona: {identifier}@{revision}") from error
            if snapshot["namespace"] != namespace:
                raise ValueError("Persona namespace does not match")
            snapshots.append(snapshot)
    if external_data is not None:
        # Retain complete selected identity histories and necessary parents, never unrelated people.
        retained = set()
        for snapshot in snapshots:
            identifier = snapshot["id"]
            while identifier is not None and identifier not in retained:
                retained.add(identifier)
                parent = external_data["personas"][identifier]["parent"]
                identifier = parent["id"] if parent else None
        exported = {**external_data, "personas": {key: external_data["personas"][key] for key in sorted(retained)}}
        validate_data(exported)
        files["reference/personas/catalog.json"] = (json.dumps(exported, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    cards, next_steps = render_selection(snapshots, sources, references_enabled=options.get("enabled", True),
                                         exclude=options.get("exclude", []), overrides=options.get("overrides", {}))
    stories, support_pending = render_story_drafts(snapshots, [item for item in intakes if item.get("context", True)])
    files[STORIES_PATH] = stories.encode()
    if support_pending:
        cards += "\n## Support/Admin Persona selection pending\n\n" + SUPPORT_STEP + "\n"
        next_steps.append(SUPPORT_STEP)
    files["docs/product/personas.md"] = cards.encode()
    notes_path = "docs/internal/video-notes.md"
    if snapshots and notes_path in files:
        notes = ["Selected personas; evidence labels and full constraints remain in the [persona cards](../product/personas.md). Validate relevant needs in the actual application.", ""]
        for snapshot in snapshots:
            identity = f"{snapshot['namespace']}:{snapshot['id']}@{snapshot['revision']}"
            notes.append(f"- **{persona_text(snapshot['name'])}** ({identity}): "
                         + persona_text(snapshot.get("description", snapshot.get("traits", {}).get("purpose"))))
            if snapshot.get("requirements"):
                notes.append("  Acceptance requirements: " + "; ".join(persona_text(item) for item in snapshot["requirements"]))
        document = files[notes_path].decode()
        start, end = "<!-- Bootstrap: selected personas -->", "<!-- Bootstrap: end selected personas -->"
        rendered = "\n".join(notes)
        if start in document and end in document.partition(start)[2]:
            before, rest = document.split(start, 1)
            after = rest.split(end, 1)[1]
            document = before + start + "\n" + rendered + "\n" + end + after
        else:
            document = document.rstrip() + "\n\n## Selected personas\n\n" + rendered + "\n"
        files[notes_path] = document.encode()
    if "README.md" in files:
        readme = files["README.md"].decode()
        example = selections[0] if selections else "namespace:persona-id@1"
        readme = readme.replace("poc-template-seed-v1:seed-constrained-operator@1", example)
        readme = readme.replace("poc-template-seed-v1:seed-observer@1", example)
        files["README.md"] = readme.encode()
    steps = files.get("docs/product/next-steps.md", b"# Next steps\n").decode()
    for step in next_steps:
        if step not in steps:
            steps += "\n- " + step + "\n"
    files["docs/product/next-steps.md"] = steps.encode()
    for relative, data in list(files.items()):
        if relative.endswith(".md") and not relative.startswith((".agents/skills/", ".claude/skills/", ".specify/templates/", "docs/product/intake/", "docs/product/RFP/source/")):
            document = data.decode()
            identifiers = sorted(set(re.findall(r"\[\^([a-z0-9-]+)\]", document)) & set(sources))
            if identifiers:
                files[relative] = render_research(document, identifiers, sources, options).encode()
    source_digest = digest(b"".join(os.fsencode(name) + b"\0" + digest(data).encode() for name, data in sorted(files.items()))
                           + json.dumps(sorted(executable)).encode())
    config = {"schema_version": 1, "name": name, "through": through, "integration": integration,
              "execution": execution, "git": dict(git_options),
              "spec_kit": SPEC_KIT, "source_sha256": source_digest, "intake": intakes, "personas": list(selections),
              "research": options, "guidance": guidance, "guidance_revision": pack.get("revision", "none"),
              "effective_guidance": effective, "guidance_sha256": {stage: digest(text.encode()) for stage, text in effective.items()},
              "feature_description": "\n\n".join(descriptions), "user_stories": STORIES_PATH}
    if persona_source is not None:
        config["persona_catalog"] = {"path": "reference/personas/catalog.json", "source_sha256": persona_source,
                                     "sha256": digest(files["reference/personas/catalog.json"])}
    if rfp_snapshot is not None:
        config["rfp"] = rfp_snapshot["summary"]
    if len(config["feature_description"].encode()) > 32768:
        config["feature_description"] = "Read all bound local intake files: " + ", ".join(item["path"] for item in intakes if item.get("context", True))
    config["feature_description"] += "\n\nBackground draft User Stories and Persona mappings: " + STORIES_PATH + ". Reconcile with supplied intake."
    config["control_hashes"] = {path: digest(data) for path, data in files.items()
                                if path.startswith(("src/poc_template/", "reference/bootstrap/step/"))
                                or path in {"reference/bootstrap/result-schema.json", ".specify/memory/constitution.md"}
                                or (persona_source is not None and path == "reference/personas/catalog.json")}
    if len((json.dumps(config, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()) > 1048576:
        raise ValueError("Bootstrap configuration exceeds 1 MiB; shorten explicit guidance/metadata before creating")
    return {"destination": str(destination), "stages": list(stages), "config": config, "files": files,
            "executable_files": executable, "directories": rfp_snapshot["directories"] if rfp_snapshot else []}


def create_scaffold(preview: dict) -> Path:
    destination = safe_destination(Path(preview["destination"]))
    destination.mkdir()  # Exclusive ownership claim; a second writer cannot win.
    for relative in preview.get("directories", []):
        if Path(relative).is_absolute() or ".." in Path(relative).parts:
            raise ValueError("Scaffold paths must stay inside the claimed destination")
        (destination / relative).mkdir(parents=True, exist_ok=True)
    for relative, data in sorted(preview["files"].items()):
        path = destination / relative
        if Path(relative).is_absolute() or ".." in Path(relative).parts:
            raise ValueError("Scaffold paths must stay inside the claimed destination")
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as stream:
            stream.write(data)
        if relative in preview.get("executable_files", []):
            path.chmod(0o755)
    config = destination / ".specify/bootstrap.json"
    config.parent.mkdir(parents=True, exist_ok=True)
    with config.open("x", encoding="utf-8") as stream:
        json.dump(preview["config"], stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    from .stage_handoff import write_handoff
    write_handoff(destination, [])
    from .project_git import initialize_project
    initialize_project(destination, preview["config"].get("git", {"initialize": False, "extension": False}))
    return destination
