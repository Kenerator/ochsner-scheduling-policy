# nxusKit — optional, off

Reviewed: 2026-10-05. An isolated adapter can add provider-independent AI and selected symbolic/hybrid reasoning when this concretely improves the PoC. Explain the purpose and benefit beside the adapter/feature flag; do not add SDK calls simply to demonstrate adoption.

At adoption: verify current SDK/package/licensing contracts, pin the dependency and use an explicit disabled-by-default feature flag. Keep imports and credentials behind the selected adapter. Test baseline without SDK/MCP/accounts, then actual selected integration and failure behavior. No SDK API shape or availability is presumed by this recipe.
