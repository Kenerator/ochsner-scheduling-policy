# Supplied reference API provenance

Adopted: 2026-10-08. Purpose: reproducible private reviewer clones of the policy candidate.

Source package: `/Users/ken/codeRepos/PoC-RFP/patient_appointment_project`.
Only the supplied mock implementation, its documentation, fabricated fixtures, and canonical OpenAPI were copied. Assignment emails, intake metadata, policies, scenarios, and secrets are not included here. These files are unchanged supplied reference material; they are not a new scheduling backend. Data is explicitly fabricated in the supplied [fixture README](data/README.md).

The preserved layout lets [server.py](mock-api/server.py) read `../data/` and keeps supplied documentation links working. From the candidate root, run `python3 reference/mock-api/server.py --port 4012`; check that this candidate's port is free first. Restart only this process to reset its in-memory bookings and handoffs. Tests/demos must use their own server instance and state. The supplied README's default port is upstream documentation; the policy candidate uses 4012.

| Source filename (relative to package root) | SHA256 of unchanged source and copy |
| --- | --- |
| `mock-api/server.py` | `9597f92fe3ec19c16e08b1491fbac12e1ffed87bd41c137be1e638addac2d1f1` |
| `mock-api/README.md` | `b7d463b52e61cbf63cb0d70ebe661eea67b25332e4af19ff2b86ae239cafde80` |
| `data/README.md` | `be5b3dc7289a97838316f0f203bc6adae1d63bedce771e68555cfa8c55aab356` |
| `data/patients.json` | `4bc471bef84eccee513b2ae15127cbf532b6aa47f151831ff7c2a6b832889d48` |
| `data/providers.json` | `0745b592a15821474ebee45f868c3ed90d4bf24846903a17e7da0b210a3d92d6` |
| `data/slots.json` | `340bb75c9c737281de2e48b7c299141ce4c27e41001c0172c4e8f0927cf0ce9b` |
| `data/appointments.json` | `02be083e7d1d5841b29a4bb1fb663ba49f6c3d9ed47c236fa67545e8432d0d65` |
| `openapi/scheduling-api.yaml` | `62e17d269d924d1a3832c16a262cb85f78ebbceb078cdb73e759a91bf40fa735` |
