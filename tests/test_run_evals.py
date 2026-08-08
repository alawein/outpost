"""tools/run_evals.py's filesystem-hashing and eval-discovery helpers are pure and testable
without a live claude call. The actual subprocess orchestration (run_one_eval's claude -p call)
is exercised only by python tools/run_evals.py itself, run by hand or in the dogfood record, not
by pytest -q, which stays fast, free, and deterministic."""
import hashlib
import pathlib
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from run_evals import discover_evals, hash_tree  # noqa: E402


def test_hash_tree_hashes_every_file_under_root():
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        (root / "a.txt").write_text("hello")
        (root / "sub").mkdir()
        (root / "sub" / "b.txt").write_text("world")
        hashes = hash_tree(root)
        assert set(hashes) == {"a.txt", "sub/b.txt"}
        assert hashes["a.txt"] == hashlib.sha256(b"hello").hexdigest()
        assert hashes["sub/b.txt"] == hashlib.sha256(b"world").hexdigest()


def test_hash_tree_returns_empty_dict_for_empty_dir():
    with tempfile.TemporaryDirectory() as tmp:
        assert hash_tree(pathlib.Path(tmp)) == {}


def test_hash_tree_skips_dot_git_directory():
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        (root / ".git").mkdir()
        (root / ".git" / "HEAD").write_text("ref: refs/heads/main")
        (root / "app.py").write_text("code")
        hashes = hash_tree(root)
        assert set(hashes) == {"app.py"}


def test_discover_evals_finds_every_subdir_with_a_task_md():
    with tempfile.TemporaryDirectory() as tmp:
        evals_dir = pathlib.Path(tmp)
        (evals_dir / "alpha").mkdir()
        (evals_dir / "alpha" / "task.md").write_text("do alpha")
        (evals_dir / "beta").mkdir()
        (evals_dir / "beta" / "task.md").write_text("do beta")
        (evals_dir / "not_an_eval").mkdir()  # no task.md, must be excluded
        assert discover_evals(evals_dir) == ["alpha", "beta"]


def test_discover_evals_returns_empty_list_for_empty_dir():
    with tempfile.TemporaryDirectory() as tmp:
        assert discover_evals(pathlib.Path(tmp)) == []
