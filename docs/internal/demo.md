# Five-minute demonstration

Record an application-specific video after adoption; this is a script, not a completed recording. Use synthetic data and disclose it.

Maintain [video production notes](video-notes.md) for the recording Agent: named personas and needs, implemented architecture/methods, exact commands and scenarios, decisions and limitations. The table below supplies timing, not proof that those facts are complete.

| Time | Show |
| --- | --- |
| 0:00–0:30 | Purpose, user pain, selected personas; synthetic disclosure |
| 0:30–1:30 | `poc-demo --scenario success`; exact proposal and explicit confirmation boundary |
| 1:30–2:00 | `poc-demo --scenario cancel`; zero adapter calls |
| 2:00–3:00 | `poc-demo --scenario failure`; finite support handoff, no retry |
| 3:00–4:15 | Reusable core vs adapter; tests; no production auth or durable execution claim |
| 4:15–5:00 | Next steps and key decisions; show repeat/reset |

Use `PYTHONPATH=src python3 -m poc_demo` if not installed. Each run resets.

Team exercise: add a concise response formatter at the presentation boundary. First write a regression for success and handoff output, make the small change, then run the whole suite. Preserve the core state, confirmation and call-count behavior. Invite discussion of alternatives and limitations.

Performance recipe, if needed: name the interaction, target environment/load and percentile; measure useful acknowledgement and completion separately. Start with a 400 ms useful-feedback target, then adjust with explicit evidence and user needs.[^doherty] No baseline compliance badge is claimed.

[^doherty]: [Laws of UX: Doherty Threshold](https://lawsofux.com/doherty-threshold/). Reviewed 2026-10-05. Timely useful feedback around 400 milliseconds can preserve interactive flow. Limit: Modern UX summary; not proof of response time, nor a full AI-answer deadline.
