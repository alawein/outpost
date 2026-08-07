"""tools/sync_labels.py's diff logic is pure and network-free: given a registry and a snapshot of
live labels, it computes create/update/unchanged/untouched-existing with no gh call. This is
what --apply's blast radius rests on, so it is proven here without a network dependency."""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from sync_labels import infer_repo, plan_sync  # noqa: E402

BUG = {"name": "type:bug", "color": "1d76db", "description": "A defect."}
FEATURE = {"name": "type:feature", "color": "1d76db", "description": "A new capability."}


def test_plan_creates_a_label_absent_from_live():
    plan = plan_sync([BUG], {})
    assert plan["to_create"] == [BUG]
    assert plan["to_update"] == []
    assert plan["unchanged"] == []


def test_plan_updates_a_label_with_drifted_color():
    live = {"type:bug": {"color": "ffffff", "description": BUG["description"]}}
    plan = plan_sync([BUG], live)
    assert plan["to_update"] == [BUG]
    assert plan["to_create"] == []


def test_plan_updates_a_label_with_drifted_description():
    live = {"type:bug": {"color": BUG["color"], "description": "stale text"}}
    plan = plan_sync([BUG], live)
    assert plan["to_update"] == [BUG]


def test_plan_reports_a_matching_label_as_unchanged():
    live = {"type:bug": {"color": BUG["color"], "description": BUG["description"]}}
    plan = plan_sync([BUG], live)
    assert plan["unchanged"] == ["type:bug"]
    assert plan["to_create"] == [] and plan["to_update"] == []


def test_plan_never_proposes_deleting_an_unmatched_live_label():
    live = {"bug": {"color": "d73a4a", "description": "old default"}}
    plan = plan_sync([BUG], live)
    assert plan["untouched_existing"] == ["bug"]
    assert "to_delete" not in plan
    # every key this function can return is additive or informational, never destructive
    assert set(plan) == {"to_create", "to_update", "unchanged", "untouched_existing"}


def test_plan_handles_a_full_mixed_batch():
    live = {
        "type:bug": {"color": BUG["color"], "description": BUG["description"]},  # unchanged
        "bug": {"color": "d73a4a", "description": "old default"},  # untouched existing
    }
    plan = plan_sync([BUG, FEATURE], live)
    assert plan["to_create"] == [FEATURE]
    assert plan["unchanged"] == ["type:bug"]
    assert plan["untouched_existing"] == ["bug"]


def _git(path, *args):
    import subprocess
    subprocess.run(["git", "-C", str(path), *args], check=True, capture_output=True)


def test_infer_repo_parses_an_https_origin(tmp_path):
    _git(tmp_path, "init")
    _git(tmp_path, "remote", "add", "origin", "https://github.com/alawein/outpost.git")
    assert infer_repo(tmp_path) == "alawein/outpost"


def test_infer_repo_returns_none_with_no_remote(tmp_path):
    _git(tmp_path, "init")
    assert infer_repo(tmp_path) is None
