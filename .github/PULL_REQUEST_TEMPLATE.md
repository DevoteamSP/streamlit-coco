## Summary

<!-- One paragraph: what changed and why -->

## Type of change

- [ ] Bug fix
- [ ] New feature
- [ ] Documentation
- [ ] Security fix
- [ ] Refactor / tech debt

## Checklist

### Code
- [ ] Tests added or updated (`tests/`)
- [ ] All existing tests pass (`make test`)
- [ ] No new linting errors (`make lint`)

### Documentation
- [ ] `CHANGELOG.md` updated (under `[Unreleased]`)
- [ ] `doc/features/` updated if new or changed feature
- [ ] `README.md` updated if install/usage changed

### Security
- [ ] No secrets, credentials, or PII in code or tests
- [ ] No `shell=True` or unsafe subprocess calls
- [ ] No new pip-audit CVEs introduced
- [ ] No hardcoded Snowflake account names or database names

### Governance (N1+)
- [ ] `doc/roadmap.md` updated if this closes a roadmap item
- [ ] Issue linked (closes #NNN)
- [ ] Manual golden-path checklist run when UI/feature touched (`doc/features/*/test-checklist.md`)
