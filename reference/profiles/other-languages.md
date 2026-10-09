# Polyglot projects — optional, off

Reviewed: 2026-10-05. Keep domain code and thin adapters grouped by responsibility. If several ecosystems are needed, use `packages/<name>/` or clear language-specific subdirectories, each with its own lock/build/test commands. Put cross-language contracts and architecture in shared docs; avoid duplicate business logic.

At adoption: choose the smallest useful stack, pin toolchains/dependencies, test cross-boundary contracts and provide a single demo/reset entry point. Rust, Go or TypeScript are options, not mandatory bootstrap dependencies.
