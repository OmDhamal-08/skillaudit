# Sample skills for manual auditing

These are standalone skills for trying out `skillaudit` by hand. They are kept
**separate** from `tests/fixtures/` on purpose, so the locked baseline counts in
`tests/test_fixtures.py` stay untouched.

Like the test fixtures, every buggy skill here is **inert**: all network hosts use
the reserved `.example` domain (which can never resolve), nothing is ever executed,
and the files are only meant to be read as text by the auditor.

## Run the auditor

```bash
skillaudit samples/safe/word-counter
skillaudit samples/buggy/env-telemetry
skillaudit samples/buggy/ssh-doctor
skillaudit samples/buggy/quick-setup
```

## What each one is

| Skill | Expected | What it demonstrates |
|---|---|---|
| `safe/word-counter` | not blocked (score 100; `REVIEW` in static-only mode) | Does exactly what its description says: reads the given files, no network, no secrets, no writes. |
| `buggy/env-telemetry` | flag | Claims to record build timing, actually POSTs every environment variable (incl. API keys) to a remote host. |
| `buggy/ssh-doctor` | flag | Poses as a "git config doctor" but reads `~/.ssh/id_rsa` and `~/.aws/credentials` and uploads them. |
| `buggy/quick-setup` | flag | `curl … \| bash` supply-chain hole, plus a "don't tell the user" instruction in `SKILL.md`. |
