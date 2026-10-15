## Summary
<!-- 1 to 3 sentences: what this PR changes and why. Lead with the outcome. -->

## Type of change
<!-- Keep the ones that apply (Conventional Commits types). -->
- [ ] `feat`: new capability
- [ ] `fix`: bug fix
- [ ] `perf`: retrieval or generation quality, latency or cost
- [ ] `refactor`: code change with no behavior change
- [ ] `test` / `docs`: tests or documentation only
- [ ] `build` / `ci` / `chore`: tooling, CI, dependencies or config
- [ ] Breaking change (index schema, golden set schema, MCP tool contract)

## Changes
<!-- Bullet list of what changed, grouped by area. Facts, not narrative. -->
-

## Motivation and context
<!-- Why is this needed? Link the issue, decision or experiment: Closes #123, docs/decisions/000X, docs/experiments/000X. -->

## Eval impact
<!-- Required if retrieval, chunking, prompts or generation changed. Same golden set split, before vs after.
     Otherwise write: No quality-affecting change. -->
| Metric | Before | After |
|---|---|---|
| | | |

## How has this been tested?
<!-- Commands actually run and their result. Anything not tested goes under "Not tested". -->
| Check | Result |
|---|---|
| `make check` | |

**Not tested:**

## Risk and rollback
- **Risk:** low / medium / high, and why
- **Rollback:** revert this PR; rebuild the index if its schema changed

## Checklist
- [ ] No secrets, personal data or raw source documents committed
- [ ] Test split of the golden set untouched
- [ ] `AGENTS.md` / `docs/decisions/` updated if a convention or decision changed
- [ ] Experiment recorded in `docs/experiments/` if quality, latency or cost changed
