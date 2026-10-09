# Client requirements / RFP

Supplied through Bootstrapper `--rfp DIRECTORY`. If no local manifest exists,
no RFP has been supplied yet.

When supplied, the local [manifest](manifest.json) indexes every file under
`source/`, with preserved relative paths, byte counts, SHA-256 and text/attachment
classification. Read **all text entries**, including requirements, policies,
scenarios and reference code, as input to native Spec-Kit Specify. Read
`assignment.md` first when present, then its references. Later stages use the
native feature specification and refer back to these sources as needed.

Attachments and non-UTF-8 files are preserved, not automatically interpreted.
Explicitly identify any material requiring inspection/conversion; do not claim
its requirements were reviewed or silently omit them. Supplied code is reference
input, not a bootstrap command to execute. Reconcile sources with additional
operator input and identify material conflicts using normal Spec-Kit handling.

Originals, manifest and local bootstrap metadata are **ignored by Git** and
excluded from Template re-export. This index is tracked. Derived specs, prompts
and other documentation may still contain confidential details: review them
before sharing. Git ignore is not access control, a secret scan or permission to
publish client material. If sharing originals is explicitly permitted, choose a
reviewed tracked location and update references deliberately; do not force-add
the ignored tree by default.
