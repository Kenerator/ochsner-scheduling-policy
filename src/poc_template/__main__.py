"""PoC scaffolding, personas and local diagnostics; intake remains reference data."""
import argparse
import json
from pathlib import Path
import re
import sys
import uuid

if sys.version_info < (3, 11):
    print("PoC-Template requires Python 3.11+; selected interpreter: " + sys.executable
          + ". Use a compatible interpreter or its project virtual environment; do not replace system Python.", file=sys.stderr)
    raise SystemExit(2)

from .persona_catalog import Catalog
from .persona_compose import load_recipe, read_json
from .persona_render import render_selection


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="poc-template")
    groups = parser.add_subparsers(dest="group", required=True)
    secrets = groups.add_parser("secrets", help="Basic staged-content credential checks; not a history/privacy audit")
    secret_commands = secrets.add_subparsers(dest="secret_action", required=True)
    for command in ("scan", "install"):
        operation = secret_commands.add_parser(command)
        operation.add_argument("--project", type=Path, required=True)
        if command == "scan":
            operation.add_argument("--index", type=Path, help="Candidate index supplied by Git's commit hook")
    doctor = groups.add_parser("doctor", help="Read-only local setup diagnostics; no assistant or installation")
    doctor.add_argument("--project", type=Path, required=True)
    qualify = groups.add_parser("qualify", help="Preview or execute trusted checks in a disposable committed-source environment")
    qualify.add_argument("--project", type=Path, required=True)
    qualify.add_argument("--profile", type=Path, help="Committed project-relative JSON profile; default docs/internal/qualification.json")
    qualify.add_argument("--execute", action="store_true", help="Run project-local installation and checks; executes trusted project code")
    bootstrap = groups.add_parser("bootstrap", help="Preview/create a project and execute cumulative Spec-Kit stages")
    bootstrap.add_argument("--template-root", type=Path, default=Path.cwd())
    bootstrap.add_argument("--destination", type=Path)
    bootstrap.add_argument("--name", help="Lowercase technical slug, e.g. poc-uat-001-01; destination may retain display capitalization")
    bootstrap.add_argument("--input", type=Path, action="append", default=[],
                           help="UTF-8 intake file; repeat for multiple files, or use - once to read stdin until EOF")
    bootstrap.add_argument("--rfp", type=Path,
                           help="Copy/index a local requirements directory recursively; originals stay Git-ignored")
    bootstrap.add_argument("--persona", action="append", default=[])
    bootstrap.add_argument("--persona-catalog", type=Path, help="External catalog for all selected personas; export only selected identities and their ancestry")
    bootstrap.add_argument("--through", type=int, choices=range(7), default=0)
    bootstrap.add_argument("--integration", choices=("codex", "claude"), default="codex")
    bootstrap.add_argument("--model", help="Explicit Codex model for this project/run only; otherwise keep configured default")
    bootstrap.add_argument("--reasoning-effort", choices=("low", "medium", "high", "xhigh", "max", "ultra"))
    bootstrap.add_argument("--stage-timeout", type=int, default=900, help="Per-stage seconds (1–86400); default 900")
    bootstrap.add_argument("--execute", action="store_true")
    bootstrap.add_argument("--no-git", action="store_true", help="Explicitly scaffold without a local Git repository")
    bootstrap.add_argument("--git-extension", action="store_true", help="Install pinned bundled native Spec-Kit Git hooks; requires the isolated tool profile")
    bootstrap.add_argument("--guidance-file", type=Path)
    bootstrap.add_argument("--no-references", action="store_true")
    bootstrap.add_argument("--exclude-reference", action="append", default=[])
    bootstrap.add_argument("--reference-overrides", type=Path)
    bootstrap_commands = bootstrap.add_subparsers(dest="bootstrap_action")
    for command in ("status", "resume", "converge", "prompts"):
        operation = bootstrap_commands.add_parser(command)
        operation.add_argument("--project", type=Path, required=True)
        operation.add_argument("--run", required=command != "prompts", help="Exact native run ID; never guesses latest")
        if command == "prompts":
            operation.add_argument("--integration", choices=("codex", "claude"), default=None)
        if command == "resume":
            operation.add_argument("--answer", action="append", default=[], help="QUESTION_ID=developer response")
            operation.add_argument("--retry-failed", action="store_true", help="Explicitly retry only after resolving a recorded failure's cause")
    personas = groups.add_parser("personas", help="Compose, retain and render pinned personas")
    personas.add_argument("--catalog", type=Path, default=Path("reference/personas/catalog.json"))
    personas.add_argument("--components-root", type=Path, default=Path("reference/personas/components"))
    personas.add_argument("--names", type=Path, default=Path("reference/personas/names.json"))
    personas.add_argument("--sources", type=Path, default=Path("reference/research/sources.json"))
    commands = personas.add_subparsers(dest="command", required=True)
    commands.add_parser("list", help="List current availability and pinned selection IDs")
    commands.add_parser("validate", help="Validate the existing catalog, including merge collisions")
    for command in ("compose", "derive"):
        operation = commands.add_parser(command)
        operation.add_argument("--recipe", type=Path, required=True)
        operation.add_argument("--name", required=command == "derive")
        if command == "compose":
            operation.add_argument("--family")
        else:
            operation.add_argument("--parent", required=True, help="namespace:id@revision")
            operation.add_argument("--difference", action="append", required=True)
    reuse = commands.add_parser("reuse", help="Read one exact snapshot without mutation")
    reuse.add_argument("--selection", required=True)
    retire = commands.add_parser("retire", help="Retire without releasing names or deleting snapshots")
    retire.add_argument("--id", required=True)
    render = commands.add_parser("render", help="Generate cards; never silently overwrite human documents")
    choices = render.add_mutually_exclusive_group(required=True)
    choices.add_argument("--selection", action="append", help="namespace:id@revision; repeat for several personas")
    choices.add_argument("--defer", action="store_true")
    render.add_argument("--output", type=Path)
    render.add_argument("--replace", action="store_true")
    render.add_argument("--no-references", action="store_true")
    render.add_argument("--exclude-reference", action="append", default=[])
    return parser


def selected(catalog: Catalog, selection: str) -> dict:
    match = re.fullmatch(r"([a-z0-9-]+):([a-z0-9-]+)@([0-9]+)", selection)
    if not match:
        raise ValueError("Selection requires namespace:id@positive-revision, not latest")
    namespace, identifier, revision = match.groups()
    snapshot = catalog.get(identifier, int(revision))
    if snapshot["namespace"] != namespace:
        raise ValueError("Selection namespace does not match this catalog")
    return snapshot


def emit(data) -> None:
    print(json.dumps(data, indent=2, sort_keys=True, allow_nan=False))


def dispatch(args: argparse.Namespace) -> int:
    if args.group == "secrets":
        from .secret_scan import scan, install_hook
        report = scan(args.project, args.index) if args.secret_action == "scan" else install_hook(args.project)
        emit(report)
        return 1 if report.get("findings") else 0
    if args.group == "doctor":
        from .doctor import inspect_project
        report = inspect_project(args.project)
        emit(report)
        return 0 if report["status"] == "ready" else 2
    if args.group == "qualify":
        from .qualification import qualify_project
        report = qualify_project(args.project, args.profile, execute=args.execute)
        emit(report)
        return 0 if report["status"] in {"preview", "passed"} else 2
    if args.group == "bootstrap":
        return dispatch_bootstrap(args)
    catalog = Catalog(args.catalog)
    if args.command == "validate":
        if not args.catalog.exists():
            raise ValueError("No catalog exists yet; compose a persona or choose an existing catalog")
        catalog.validate()
        print("Catalog valid; identity labels do not establish runtime authority.")
    elif args.command == "list":
        rows = []
        for record in catalog.list():
            snapshot = catalog.get(record["id"], record["revision"])
            rows.append({**record, "actor_type": snapshot["actor_type"],
                         "description": snapshot.get("description", "Persona"),
                         "selection": f"{record['namespace']}:{record['id']}@{record['revision']}"})
        emit(rows)
    elif args.command in ("compose", "derive"):
        composition = load_recipe(args.recipe, args.components_root)
        identifier = str(uuid.uuid4())  # Identity allocation, never trait synthesis.
        if args.command == "derive":
            parent = selected(catalog, args.parent)
            result = catalog.create(composition, name=args.name, persona_id=identifier,
                                    family_id=parent["family_id"], parent=(parent["id"], parent["revision"]),
                                    differences=args.difference)
        else:
            name = args.name or catalog.available_name(read_json(args.names).get("default"))
            result = catalog.create(composition, name=name, persona_id=identifier,
                                    family_id=args.family or args.recipe.stem)
        emit(result)
    elif args.command == "reuse":
        emit(selected(catalog, args.selection))
    elif args.command == "retire":
        catalog.retire(args.id)
        print(f"Retired {args.id}; names and retained snapshots remain reserved.")
    elif args.command == "render":
        snapshots = [] if args.defer else [selected(catalog, item) for item in args.selection]
        sources = {} if args.no_references else read_json(args.sources)
        document, steps = render_selection(snapshots, sources, references_enabled=not args.no_references,
                                           exclude=args.exclude_reference)
        if args.output is None:
            print(document, end="")
        else:
            if args.output.is_symlink():
                raise ValueError("Refusing a symlinked output")
            args.output.parent.mkdir(parents=True, exist_ok=True)
            # Exclusive create closes the existence-check race for normal exports.
            with args.output.open("w" if args.replace else "x", encoding="utf-8") as stream:
                stream.write(document)
            print(f"Generated {args.output}")
        for step in steps:
            print(f"Next step: {step}", file=sys.stderr)
    return 0


def dispatch_bootstrap(args) -> int:
    from .bootstrap import preview_bootstrap, create_scaffold
    from .bootstrap_workflow import run_bootstrap, status_bootstrap, resume_bootstrap, converge_bootstrap
    from .speckit_adapter import bounded_json
    if args.bootstrap_action:
        try:
            if args.bootstrap_action == "prompts":
                from .stage_handoff import render_handoff
                from .stage_handoff import HANDOFF_PATH
                from .bootstrap_workflow import config_for
                from .speckit_adapter import project_path
                root = args.project.resolve()
                config = config_for(root)
                integration = args.integration or config["integration"]
                if args.run:
                    state = status_bootstrap(root, args.run)
                    text = render_handoff(config, state["completed"], integration, state.get("reason", ""))
                else:
                    text = project_path(root, HANDOFF_PATH).read_text()
                    prefix = "$" if integration == "codex" else "/"
                    text = re.sub(r"^[/$](speckit-[a-z]+)", lambda match: prefix+match[1], text, flags=re.M)
                    text = text.replace("The blocks use " + config["integration"] + " syntax.", "The blocks use " + integration + " syntax.")
                print(text)
                return 0
            if args.bootstrap_action == "status":
                state = status_bootstrap(args.project, args.run)
            elif args.bootstrap_action == "converge":
                state = converge_bootstrap(args.project, args.run)
            else:
                answers = {}
                for answer in args.answer:
                    key, separator, value = answer.partition("=")
                    if not separator or key in answers:
                        raise ValueError("Each --answer must be a distinct QUESTION_ID=TEXT")
                    answers[key] = value
                state = resume_bootstrap(args.project, args.run, answers, retry_failed=args.retry_failed)
        except (ValueError, OSError, KeyError, TypeError) as error:
            print(f"Bootstrap recovery blocked: {error}", file=sys.stderr)
            return 4
    else:
        if args.destination is None or not args.name:
            raise ValueError("Bootstrap needs --destination and --name")
        guidance = bounded_json(args.guidance_file) if args.guidance_file else None
        overrides = bounded_json(args.reference_overrides) if args.reference_overrides else {}
        preview = preview_bootstrap(args.template_root, args.destination, args.name, args.input, args.persona,
                                    args.through, args.integration,
                                    {"enabled": not args.no_references, "exclude": args.exclude_reference, "overrides": overrides}, guidance,
                                    dict(model=args.model, reasoning_effort=args.reasoning_effort, stage_timeout_seconds=args.stage_timeout),
                                    stdin_stream=sys.stdin.buffer if Path("-") in args.input else None,
                                    persona_catalog=args.persona_catalog,
                                    git_options={"initialize": not args.no_git, "extension": args.git_extension},
                                    rfp=args.rfp)
        if not args.execute:
            emit({"destination": preview["destination"], "stages": preview["stages"], "files": len(preview["files"]),
                  "mode": "preview", "integration": args.integration, "guidance": preview["config"]["guidance"],
                  "execution": preview["config"]["execution"],
                  "git": preview["config"]["git"],
                  "rfp": preview["config"].get("rfp"),
                  "personas": preview["config"]["personas"], "spec_kit": preview["config"]["spec_kit"]})
            return 0
        root = create_scaffold(preview)
        if preview["config"].get("rfp"):
            rfp = preview["config"]["rfp"]
            print(f"RFP: {rfp['text_files']} text files, {rfp['attachments']} attachments; "
                  f"review indexed attachment needs in {root / rfp['manifest']}", file=sys.stderr)
        try:
            state = run_bootstrap(root)
        except (ValueError, OSError, KeyError, TypeError) as error:
            print(f"Project preserved at {root}; bootstrap execution blocked: {error}", file=sys.stderr)
            return 4
        args.project = root
    emit(state)
    if "handoff_path" in state:
        print(f"Remaining stage prompts: {args.project / state['handoff_path']}", file=sys.stderr)
    # A valid observation is not a stage-completion claim.
    if args.bootstrap_action == "status" and state["status"] == "running":
        return 0
    if state["status"] == "paused":
        for number, question in enumerate(state["questions"], 1):
            print(f"Question {number} of {len(state['questions'])}: {question['text']}", file=sys.stderr)
            for option in question["options"]:
                suffix = " (Recommended)" if option == question["recommendation"] else ""
                print(f"  - {option}{suffix}", file=sys.stderr)
            print(f"Recommendation: {question['recommendation']}", file=sys.stderr)
            print("Resume with the exact run ID and --answer " + question["id"] + "=YOUR_RESPONSE", file=sys.stderr)
        return 3
    return 0 if state["status"] == "completed" else 4


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return dispatch(args)
    except (ValueError, OSError) as error:
        print(f"{args.group.title()} operation failed: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
