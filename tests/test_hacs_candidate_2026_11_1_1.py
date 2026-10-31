"""Immutable identity and release-train guard for the BE HACS test candidate."""

from __future__ import annotations

import json
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERSION = "2026.11.1.1"
TAG = f"v{VERSION}"


def test_hacs_test_version_is_consistent_across_runtime_and_project():
    manifest = json.loads(
        (ROOT / "custom_components/frank_energie/manifest.json").read_text()
    )
    project = tomllib.loads((ROOT / "pyproject.toml").read_text())
    constants = (ROOT / "custom_components/frank_energie/const.py").read_text()

    assert manifest["version"] == VERSION
    assert project["tool"]["poetry"]["version"] == VERSION
    assert f'VERSION: Final[str] = "{VERSION}"' in constants
    assert manifest["requirements"] == ["python-frank-energie==2026.9.20"]


def test_hacs_candidate_is_full_zip_pre_release_not_default_branch():
    hacs = json.loads((ROOT / "hacs.json").read_text())
    publisher = (
        ROOT / ".github/workflows/publish-consolidated-hacs-test.yml"
    ).read_text()

    assert hacs["zip_release"] is True
    assert hacs["filename"] == "frank_energie.zip"
    assert "fix/be-price-provenance-truth" in publisher
    assert "refs/heads/fix/be-price-provenance-truth" in publisher
    assert "tests/test_hacs_candidate_2026_11_1_1.py" in publisher
    assert "--prerelease" in publisher
    assert "gh release create" in publisher
    assert "gh release view" in publisher
    assert "SHA256SUMS.txt" in publisher
    assert "Hassfest Home Assistant validation" in publisher
    assert "HACS integration validation" in publisher
    assert TAG in publisher
    assert "TAG=v2026.11.1.1" in publisher
    assert "BLOCK: immutable Git tag already exists" in publisher
    assert "Reject stale release train commits" in publisher
    assert "github.sha" in publisher
    assert "action_required)$'; then" in publisher
    assert publisher.count("\njobs:\n") == 1
    assert len(publisher.splitlines()) < 260


def test_live_acceptance_and_backout_are_explicit():
    candidate = (ROOT / "docs/candidates/2026.11.1.1.md").read_text()
    tracker = (ROOT / "docs/engineering/RELEASE_TRAIN.md").read_text()

    assert "finance defaults **OFF**" in candidate
    assert "Home Assistant" in candidate
    assert "Rollback" in candidate
    assert "#11" in candidate
    assert "v2026.10.31.2" in candidate
    assert TAG in tracker
    assert "Draft" in tracker
