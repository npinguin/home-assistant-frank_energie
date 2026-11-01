# Release Process

This document describes the release process for the Frank Energie Home Assistant integration.

## Goals

The release process aims to provide:

- Predictable releases
- High-quality updates
- Automated validation
- Backward compatibility where possible
- Compliance with Home Assistant best practices

## Versioning

The integration follows date-based versioning.

Example:

```text
2026.6.21
```

Version numbers generally follow:

```text
YYYY.M.D
```

Examples:

```text
2026.1.1
2026.6.21
2026.12.31
```

## Release Types

### Pre-release

Pre-releases are used for:

- New features
- Significant refactoring
- API changes
- Community testing

Pre-releases may contain:

- Experimental functionality
- Breaking changes
- Additional logging

### Stable Release

Stable releases are intended for general use.

Requirements:

- Successful CI validation
- Successful Hassfest validation
- Review of major changes
- Documentation updates

## Development Workflow

Typical workflow:

```text
Issue
  ↓
Feature Branch
  ↓
Implementation
  ↓
Tests
  ↓
CI Validation
  ↓
Pull Request
  ↓
Review
  ↓
Merge
  ↓
Release
```

## Branch Strategy

### Main Branch

```text
main
```

The main branch contains the latest development version.

All changes should be merged through pull requests.

### Feature Branches

Examples:

```text
feature/smart-battery
feature/new-entities
fix/authentication
fix/resolution-handling
```

Feature branches should be short-lived and focused on a single change.

## Pull Requests

Pull requests should:

- Have a clear description
- Reference related issues
- Include tests when appropriate
- Update documentation when necessary

### Documentation Updates

Documentation should be updated when:

- New entities are added
- Events change
- Features change
- Configuration changes
- User-visible behavior changes

Affected documentation may include:

- entities.md
- events.md
- examples.md
- user_features.md
- faq.md

## Continuous Integration

All pull requests should pass automated validation.

Typical checks include:

### Linting

Examples:

- Ruff
- Pylint

### Testing

Examples:

- Pytest
- Snapshot tests
- Config flow tests
- Coordinator tests

### Home Assistant Validation

Examples:

- Hassfest
- Manifest validation
- Translation validation

## Quality Standards

The integration targets Home Assistant Quality Scale compliance.

Reference:

https://www.home-assistant.io/docs/quality_scale/

Contributors should prioritize:

- Reliability
- Test coverage
- Documentation
- Diagnostics
- Reauthentication support

## Labels

The repository uses labels to organize work.

Examples may include:

- bug
- enhancement
- documentation
- config_flow
- coordinator
- sensor
- binary_sensor
- button
- number
- select
- diagnostics
- release
- pre-release

Labels help identify release content and affected areas.

## Release Checklist

Before creating a release:

### Code

- [ ] Code reviewed
- [ ] Tests passing
- [ ] Linting passing
- [ ] No known regressions

### Documentation

- [ ] Documentation updated
- [ ] New entities documented
- [ ] New events documented
- [ ] Examples updated

### Home Assistant Validation

- [ ] Hassfest passing
- [ ] Manifest valid
- [ ] Diagnostics verified

### Release Notes

- [ ] Breaking changes documented
- [ ] New features documented
- [ ] Fixes documented

## HACS Releases

The integration is distributed through HACS.

Release requirements:

- Valid version number
- GitHub release created
- Valid manifest
- Passing validation

Users receive updates through HACS after publication.

## Breaking Changes

Breaking changes should be minimized.

When unavoidable:

- Clearly document the change
- Include migration guidance
- Mention the change in release notes

Examples:

- Entity removals
- Entity renames
- Configuration changes
- Service changes

## Bug Fix Releases

Bug-fix releases should:

- Focus on a specific issue
- Avoid unrelated changes
- Include regression testing when possible

## Security Fixes

Security-related issues should be prioritized.

Examples:

- Authentication issues
- Token handling issues
- Sensitive data exposure

Documentation and release notes should be updated accordingly.

## Release Notes

Release notes should generally include:

### Added

New functionality.

### Changed

Behavior changes.

### Fixed

Bug fixes.

### Removed

Deprecated or removed functionality.

## Post-Release Verification

After release:

- Verify HACS availability.
- Verify installation works.
- Verify upgrade path works.
- Monitor issue reports.
- Monitor regression reports.

## Contributor Expectations

Contributors are encouraged to:

- Follow Home Assistant development standards.
- Write tests.
- Update documentation.
- Maintain backward compatibility.
- Use async-first patterns.

## Related Documentation

- architecture.md
- developer.md
- diagnostics.md
- entities.md
- events.md
- faq.md
- user_features.md
## Documentation publishing in this fork

This fork distributes the Home Assistant integration through HACS. Its maintained user
and contributor documentation is Markdown in `README.md` and `docs/`, linked directly
from GitHub. **Docusaurus Pages is not a release deliverable for this fork.**

On 2026-10-31, the obsolete `Deploy Docusaurus to GitHub Pages` workflow was retired
(see issue #9): the repository has a legacy `docusaurus.config.js` but **no**
`package.json` or npm/yarn lockfile, so `npm ci` / `npm run build` could never run
reproducibly. This was a pre-existing failure, not a regression of the Python
integration. Do not claim docs Pages deployment as a passing gate.

If Pages publishing becomes a requirement, introduce and review a complete Node
project with a committed lockfile and a working build, then separately reinstate
Pages CI. The Python test, Ruff, HACS and Hassfest validation remain independent.

## Event-specific labeling governance

The shared issue/PR title labeler runs on both issue and PR events. File-path and
size labeling are **PR-only** and must never run on issue events or on closed PRs.
This avoids the API failure tracked in issue #10 without removing issue triage.

## One qualified HACS test release train (fork)

The active Belgian fork uses one consolidated Draft PR #18 and one
version-neutral publisher, `.github/workflows/publish-qualified-hacs-test.yml`.
A normal code change does **not** publish a release. To request a new
controlled pre-release, update `docs/candidates/TEST_RELEASE_CANDIDATE.json`
with a unique version and maintain matching manifest/const/pyproject and
`docs/candidates/<version>.md`. All exact-head PR CI checks, HACS and
Hassfest must pass; an existing tag/release can never be replaced.

The publisher produces a deterministic HACS ZIP and checksum from the
exact validated source SHA. This is a **TEST-only** gate; stable promotion
requires separate real Home Assistant config-entry, device/entity/Recorder,
finance-source and rollback acceptance recorded in the consolidated PR.
Earlier version-specific publishers have been retired from the active
branch; their immutable historical tags and workflows remain audit evidence.
