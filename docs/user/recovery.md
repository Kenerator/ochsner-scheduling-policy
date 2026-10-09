# Recovery and limitations

- `simulated: true` means no real API, user account or production operation was involved.
- On cancellation, nothing happened. Start a new proposal if needed.
- On failure/handoff, use the adopting project's named support path. This template does not contact a representative.
- An unknown scenario prints the allowed choices and exits 2. Choose a documented scenario; do not loop retries.
- Restarting the process resets demo state. Real use needs durable duplicate protection and authorization; in-memory confirmation is not distributed exactly-once execution.

See [next steps](../product/next-steps.md) for real-use prerequisites.
