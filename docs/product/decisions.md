# Key decisions

- Reusable core with effects at a synthetic adapter; thin CLI for deterministic demonstrations.
- Confirmation binds an exact instance-scoped proposal. Cached results avoid replay in one sequential in-memory service, not across processes or concurrent distributed callers.
- Known unavailability hands off without automatic retries; unexpected programming errors remain visible.
- Personas and research are pinned inputs, not authority or validated facts by default.
- Optional profiles are disabled; introducing real services/security requires explicit design and qualification.

Record project-specific assumptions and tradeoffs briefly here. Use Spec-Kit feature tasks for implementation progress and next steps for future work—not a second status ledger.
