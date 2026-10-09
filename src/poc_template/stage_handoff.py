"""Native invocation blocks, not another stage processor or progress ledger."""
from pathlib import Path
import re

from .stage_guidance import STAGES

HANDOFF_PATH = "docs/internal/spec-kit-handoff.md"


def stage_prompt(config: dict, stage: str, integration: str) -> str:
    if stage not in STAGES or integration not in {"codex", "claude"}:
        raise ValueError("Choose a native stage and codex/claude integration")
    command = ("$" if integration == "codex" else "/") + "speckit-" + stage
    arguments = []
    if stage == "specify":
        paths = [item["path"] for item in config.get("intake", []) if item.get("context", True)]
        arguments.append("Create the feature described in " + ", ".join(paths) + "." if paths else
                         "[Replace this with your feature description or requirements-file references.]")
        if config.get("user_stories"):
            arguments.append("Background draft User Stories and Persona mappings: " + config["user_stories"] + ". Reconcile with supplied intake.")
    guidance = config.get("effective_guidance", {}).get(stage, "")
    if guidance:
        arguments.append(guidance)
    return command + ("\n" + "\n".join(arguments) if arguments else "")


def render_handoff(config: dict, completed: list[str], integration: str, reason="") -> str:
    if tuple(completed) != STAGES[:len(completed)]:
        raise ValueError("Handoff needs an ordered completed stage prefix")
    lines = ["# Remaining Spec-Kit stages", "",
             "Generated handoff, not completion evidence. Run from this project's root. "
             "Use stages in order; both installed integrations share the local feature files. "
             "You may switch assistant for each stage. Do not run competing sessions on the same feature.", "",
             "The blocks use " + integration + " syntax. Claude uses `/speckit-STAGE`; "
             "Codex uses `$speckit-STAGE`. Change only the first-line prefix when switching assistant, "
             "or regenerate with `poc-template bootstrap prompts --project . --integration claude` (or `codex`).", "",
             "Manual stage execution does not update the automated workflow's completion state. "
             "Before manual continuation, stop/reconcile any live automated owner. Resolve any reported "
             "failure or pending question; these prompts do not bypass it. Let installed Spec-Kit handle "
             "its normal prerequisites, clarifications and Constitution checks.", ""]
    if reason:
        lines += ["Last automated result: " + reason, ""]
    for stage in STAGES[len(completed):]:
        prompt = stage_prompt(config, stage, integration)
        fence = "`" * max(3, 1 + max((len(item) for item in re.findall(r"`+", prompt)), default=0))
        lines += [f"## Stage {STAGES.index(stage)+1}: {stage.title()}", "",
                  f"Codex: `$speckit-{stage}` · Claude: `/speckit-{stage}`", "", fence+"text", prompt, fence, ""]
    if len(completed) == 6:
        lines += ["No stages remain.", ""]
    return "\n".join(lines)


def write_handoff(root: Path, completed: list[str], reason="", integration=None) -> dict:
    from .speckit_adapter import bounded_json, project_path
    config = bounded_json(project_path(root, ".specify/bootstrap.json"))
    destination = project_path(root, HANDOFF_PATH)
    destination.parent.mkdir(parents=True, exist_ok=True)
    # This one derived file is deliberately regenerable; it is not native state.
    destination.write_text(render_handoff(config, completed, integration or config["integration"], reason), encoding="utf-8")
    return {"handoff_path": HANDOFF_PATH, "remaining": list(STAGES[len(completed):])}
