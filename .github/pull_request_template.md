## Summary

Describe the purpose and scope of the change.

## Source-data impact

List the election types, years, file formats, or source columns affected. State
"none" when the change does not affect parsing or normalisation.

## Verification

- [ ] `pytest -q` passes
- [ ] New source formats or aliases have fixture-based tests
- [ ] API or data-dictionary changes are documented
- [ ] No archives, databases, credentials, caches, or virtual environments are included
- [ ] The branch is rebased on the current target branch
