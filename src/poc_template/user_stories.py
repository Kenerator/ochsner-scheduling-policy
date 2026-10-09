"""Offline Persona-derived story seeds, never semantic intake extraction or scope approval."""
from .persona_render import text

STORIES_PATH = "docs/product/user-stories.md"
SUPPORT_STEP = "Select or map a Support/Admin Persona and reconcile its draft story against intake."


def render_story_drafts(snapshots: list[dict], intakes: list[dict]) -> tuple[str, bool]:
    """Use already-validated snapshots; native Specify performs actual reconciliation."""
    lines = ["# User Stories — draft and index", "",
             "Stage 0 background, not approved scope or completion evidence. Supplied stories, "
             "journeys and scenarios remain verbatim in intake. These seeds do not assert that "
             "intake lacks stories; reconcile it first during native Specify.", "",
             "**Origin** (specified/inferred) is separate from **scope** (proposed/accepted/deferred). "
             "Inferred story wording can describe an explicitly required capability; preserve that "
             "requirement. Acceptance of an inference does not change its origin. Persona labels "
             "and drafts grant no permissions.", "", "## Supplied sources", ""]
    lines += ([f"- [Intake {i}]({item['path'].removeprefix('docs/product/')})"
               for i, item in enumerate(intakes, 1)] or ["- Intake not yet supplied."])
    lines += ["", "## Native specification index", "",
              "After Specify, link the feature `spec.md` User Scenarios & Testing sections here. "
              "Move reconciled draft detail into those native stories and replace it here with links, "
              "retaining Persona pins and origin/source labels there. Native `tasks.md` tracks "
              "implementation; this is not another progress ledger.", "", "## Provisional seeds", ""]
    support = []
    for number, snapshot in enumerate(snapshots, 1):
        pin = f"{snapshot['namespace']}:{snapshot['id']}@{snapshot['revision']}"
        traits = snapshot.get("traits", {})
        goal = traits.get("goals") or traits.get("purpose") or snapshot.get("description")
        lines += [f"### DRAFT-{number:02d} — {text(snapshot['name'])}", "",
                  f"- **Persona:** {text(snapshot['name'])} · {pin} · actor type: {snapshot['actor_type']} "
                  "([card](personas.md)).",
                  "- **Origin:** INFERRED from the selected Persona; not specified product scope.",
                  "- **Scope:** proposed; priority and benefit need input reconciliation.",
                  f"- **Story seed:** As {text(snapshot['name'])}, I want to {text(goal)}, "
                  "so I can achieve this outcome within my documented constraints."]
        if snapshot.get("scenarios"):
            scenario = snapshot["scenarios"][0]
            lines.append(f"- **Acceptance seed:** Given {text(scenario['given'])}; "
                         f"When {text(scenario['when'])}; Then {text(scenario['then'])}.")
        else:
            lines.append("- **Acceptance seed:** pending a concrete Given/When/Then scenario.")
        lines.append("")
        # A known portfolio family/component is a coverage hint, not role authentication.
        if (snapshot.get("family_id") == "enterprise-support" or
                "enterprise-support" in snapshot.get("component_basis", {})):
            support.append(f"{text(snapshot['name'])} ({pin})")
    if not snapshots:
        lines += ["Primary-user Persona/story selection pending. Infer a useful journey from intake "
                  "when available; do not invent a named Persona or call it validated research.", ""]
    lines += ["## Support/Admin coverage", ""]
    if support:
        lines += ["Persona mapping: " + "; ".join(support) + ". See the corresponding seeds above.", ""]
    else:
        lines += ["**Persona selection pending:** corresponding Support/Admin placeholder in "
                  "[Personas](personas.md); not a fabricated identity or permission.", ""]
    lines += ["- **Origin:** INFERRED generic teammate need; scope proposed, not a required admin UI.",
              "- **Story seed:** As the mapped support/admin teammate, I want accurate outcome and "
              "recovery context, so I can help without making the user repeat work or taking unsafe action.",
              "- **Acceptance seed:** Given an unresolved case; When a permitted summary or diagnostic "
              "is inspected; Then known facts, missing information, attempted/completed/unknown outcomes "
              "and a truthful next step are distinguishable, with sensitive data excluded as required.",
              "", "Always retain this coverage or an explicit documented deferral. It may be served by "
              "existing help, diagnostics or documentation; do not silently add a console, authentication, "
              "live handoff or new permissions. Validate against actual policy and interfaces.", ""]
    return "\n".join(lines), not support
