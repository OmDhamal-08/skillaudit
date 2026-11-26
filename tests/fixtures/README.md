# Test fixtures

Every folder here is a small fake skill used by the tests and by `scripts/evaluate.py`.

- `malicious/` - one attack per skill. Each one is **inert**: URLs use the reserved
  `.example` domain (it can never resolve) and encoded payloads only decode to a
  harmless `print`/`echo`. They are still never executed, only read as text.
- `clean/` - realistic, harmless skills used to measure false positives.

| Malicious fixture | Attack |
|---|---|
| curl-pipe-shell | `curl ... \| bash` in a setup script |
| ssh-key-reader | reads `~/.ssh/id_rsa` in a "git config doctor" |
| env-exfil | posts every environment variable to a server |
| base64-payload | `exec(base64.b64decode(...))` |
| bashrc-persistence | appends a background job to `~/.bashrc` |
| zero-width-injection | hidden instruction in unicode tag characters |
| dont-tell-user | "do not mention to the user..." in SKILL.md |
| path-traversal-write | writes into other skills via `../` |
| pdf-helper-keys | "PDF helper" that uploads `~/.aws/credentials` |
| obfuscated-eval | `new Function(atob(...))()` in JavaScript |
