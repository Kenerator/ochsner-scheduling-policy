"""The single trusted local native step; the native engine owns all progress."""
from pathlib import Path
from specify_cli.workflows.base import StepBase, StepResult, StepStatus
from poc_template.speckit_adapter import invoke_stage, semantic_dependencies
from poc_template.stage_guidance import strict_json, STAGES


class PocStage(StepBase):
    type_key = "poc-stage"

    def execute(self, config, context):
        try:
            dependencies = strict_json(context.inputs.get("dependencies", "{}"))
            feature_dir = context.inputs.get("feature_dir", "")
            # Use the most recently evaluated spec, plus plan/tasks when available.
            for prior_id in STAGES:
                prior = context.steps.get(prior_id, {})
                if prior.get("status") == "completed":
                    output = prior["output"]
                    feature_dir = output["feature_dir"]
                    dependencies.update(semantic_dependencies(output))
            inputs = {**context.inputs, "answers": strict_json(context.inputs.get("answers", "{}")),
                      "dependencies": dependencies, "feature_dir": feature_dir}
            result = invoke_stage(Path(context.project_root), context.run_id, config["stage"], inputs)
            status = {"complete": StepStatus.COMPLETED, "input_required": StepStatus.PAUSED}.get(result["status"], StepStatus.FAILED)
            return StepResult(status=status, output=result, error=result["summary"] if status == StepStatus.FAILED else None)
        except (ValueError, OSError, KeyError, TypeError) as error:
            return StepResult(status=StepStatus.FAILED, error=str(error))
