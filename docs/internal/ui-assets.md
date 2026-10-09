# UI assets and familiar interaction

Updated: 2026-10-08. Adopted for the Ochsner-internal policy PoC under the Operator's explicit logo approval and required color-theme instruction. This is not a certified brand kit or a public-redistribution grant.

| Local asset | Origin / captured | Use / alt text | Authorized audience |
| --- | --- | --- | --- |
| [Ochsner logo](../../assets/ui/branding/ochsner-health-observed.svg) | Unchanged embedded logo from [Ochsner homepage](https://www.ochsner.org/), cached 2026-10-07 | Sponsor identification; alt text: “Ochsner Health” | Ochsner-internal PoC and private reviewer access |
| [Theme tokens](../../assets/ui/themes/ochsner-observed-theme.css) | Project-owned stylesheet using observed logo colors, prepared 2026-10-07 | Blue `#13477D`, gold `#E0A42E`, system fonts | Ochsner-internal PoC and private reviewer access |

Approval/provenance record: `/Users/ken/codeRepos/DevOps/engineering-notebook/poc-template/ochsner-invitation-and-branding-20261007.md`. Local source cache: `/Users/ken/codeRepos/DevOps/tmp/ochsner-brand-cache-20261007.gBNce2/`. The Operator considered the website's reuse limitations and expressly approved internal-only logo use; no additional per-use approval applies within that scope.

Unchanged asset SHA256:

- Logo: `a10693d454c93b7d036d2e03bc7ce75ab55eb7bc53dc6386190da20d1e421050`
- Theme: `09afe47f48247a7bf088a82e81d3683e793462be4cd7e49a74bec28b7794cdbd`

The SVG was checked for active constructs before adoption. No site CSS, tracking scripts, external font calls, homepage HTML, or Epic screenshots were adopted. Gold uses dark foreground tokens; actual UI keyboard/focus and contrast checks remain implementation verification, not a claim of accessibility conformance. Supplied assignment guidance takes precedence over observed branding conventions.

Runtime usage and UI verification should be linked from the [as-built walkthrough](as-built/code-walkthrough.md), [architecture](as-built/architecture.md), and [video notes](video-notes.md) once implemented.

Presentation repair (2026-10-09): `app.py` supplies a 222×26 viewBox and aspect-preserving responsive sizing at render time. The adopted SVG file and path geometry are unchanged.
