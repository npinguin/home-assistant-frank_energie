"""Guard the single immutable, exact-head Frank Energie HACS test lifecycle."""

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
WORKFLOWS = ROOT / ".github" / "workflows"


def test_only_one_active_branch_test_publisher() -> None:
    """Legacy release-specific publishers cannot silently create older tags."""
    assert not (WORKFLOWS / "publish-integrated-hacs-test.yml").exists()
    assert not (WORKFLOWS / "publish-graphql-hacs-test.yml").exists()
    assert (WORKFLOWS / "publish-qualified-hacs-test.yml").is_file()


def test_candidate_publisher_is_version_neutral_and_gate_complete() -> None:
    """A marker change requests one test release, never a normal code push."""
    source = (WORKFLOWS / "publish-qualified-hacs-test.yml").read_text()
    assert "docs/candidates/TEST_RELEASE_CANDIDATE.json" in source
    assert "workflow_dispatch:" in source
    assert "fix/be-price-provenance-truth" in source
    assert 'candidate.get("version")' in source
    assert 'manifest["version"]' in source
    assert "pyproject.toml" in source
    assert "python-frank-energie==2026.9.20" in source
    for check in (
        "Flake8 and pytest",
        "Ruff",
        "Quality Scale Validation",
        "Link Check",
        "HACS structure validation",
        "Hassfest Home Assistant validation",
    ):
        assert check in source
    assert "head_sha=" in source and "event=pull_request" in source
    assert 'test "$CURRENT" = "$GITHUB_SHA"' in source
    assert "gh release view" in source and "git/ref/tags/" in source
    assert "--prerelease" in source and "SHA256SUMS.txt" in source
    assert '--target "$GITHUB_SHA"' in source
    assert "v2026.10.31.1" not in source
    assert "v2026.10.31.2" not in source
    assert "v2026.11.1.1" not in source


def test_stable_zip_workflow_cannot_repackage_immutable_test_tags() -> None:
    """A new prerelease must not be overwritten by a second unqualified ZIP."""
    source = (WORKFLOWS / "release.yml").read_text()
    assert "!github.event.release.prerelease" in source
