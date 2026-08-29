"""The doc generator splices catalog-derived content into hand-authored docs at marked spans,
mirroring tests/test_templates_build.py's pattern: no real-repo disk dependency, a synthetic
catalog and synthetic doc text."""
import pytest

from kit.docs_build import apply_markers, build_docs
from kit.catalog import Catalog


def _cat(**overrides):
    base = dict(
        version="0.0.0",
        stages=[{"name": "Start", "summary": "begin"}],
        prompts=[{"name": "orient-repo", "path": "prompts/core/orient-repo.md",
                  "summary": "map a repo", "stage": "Start"}],
        templates=[], adapters=[], checks=[],
    )
    base.update(overrides)
    return Catalog(**base)


SIX_TOOLS = ["claude", "codex", "cursor", "copilot", "windsurf", "gemini"]
TOTALS = {"verify": [30, 30], "git": [18, 30], "none": [0, 30]}
HEADLINE = ("verify caught 30 of 30 seeded drifts across 6 tools; "
            "plain git status caught 18 of 30; copying by hand caught 0")


def _write_results(root, totals=TOTALS, tools=SIX_TOOLS):
    """A benchmark results fixture at the path the headline renderer reads."""
    import json
    d = root / "benchmarks" / "drift"
    d.mkdir(parents=True, exist_ok=True)
    d.joinpath("results.json").write_text(
        json.dumps({"kit_version": "0.0.0", "tools": tools, "scenarios": [], "rows": [],
                    "totals": totals}),
        encoding="utf-8")


# a README fixture carrying both of its required spans, the count in sync with the one-prompt
# catalog the build_docs tests write and the headline in sync with _write_results
README_IN_SYNC = (
    "The kit ships <!-- GENERATED:core-count-words -->one<!-- /GENERATED:core-count-words --> prompts.\n"
    f"<!-- GENERATED:benchmark-headline -->{HEADLINE}<!-- /GENERATED:benchmark-headline -->\n"
)


def test_benchmark_headline_renders_the_exact_sentence_from_results(tmp_path):
    from kit.docs_build import _render_benchmark_headline
    _write_results(tmp_path)
    assert _render_benchmark_headline(tmp_path) == HEADLINE


def test_benchmark_headline_follows_the_totals_and_tool_count(tmp_path):
    # the numbers come from totals and the tool count from len(tools), not from constants
    from kit.docs_build import _render_benchmark_headline
    _write_results(tmp_path, totals={"verify": [29, 30], "git": [17, 30], "none": [1, 30]},
                   tools=["claude", "codex"])
    assert _render_benchmark_headline(tmp_path) == (
        "verify caught 29 of 30 seeded drifts across 2 tools; "
        "plain git status caught 17 of 30; copying by hand caught 1")


def test_benchmark_headline_raises_a_value_error_when_results_are_missing(tmp_path):
    # docs_sync reports ValueError as a check failure; any other exception would crash the gate
    from kit.docs_build import _render_benchmark_headline
    with pytest.raises(ValueError, match="results.json"):
        _render_benchmark_headline(tmp_path)


def test_benchmark_headline_raises_a_value_error_on_malformed_totals(tmp_path):
    from kit.docs_build import _render_benchmark_headline
    _write_results(tmp_path, totals={"verify": [30, 30]})
    with pytest.raises(ValueError, match="totals"):
        _render_benchmark_headline(tmp_path)


def test_readme_requires_the_benchmark_headline_marker():
    from kit.docs_build import REQUIRED_MARKERS
    assert REQUIRED_MARKERS["README.md"] == {"core-count-words", "benchmark-headline"}


def test_build_docs_rerenders_a_stale_readme_headline(tmp_path):
    cat_dir = tmp_path / "kit" / "catalog"
    cat_dir.mkdir(parents=True)
    import json
    cat_dir.joinpath("catalog.json").write_text(json.dumps({
        "version": "0.0.0",
        "stages": [{"name": "Start", "summary": "begin"}],
        "prompts": [{"name": "orient-repo", "path": "prompts/core/orient-repo.md",
                     "summary": "map a repo", "stage": "Start"}],
        "templates": [], "adapters": [], "checks": [],
    }), encoding="utf-8")
    _write_results(tmp_path)
    (tmp_path / "README.md").write_text(
        README_IN_SYNC.replace("30 of 30 seeded", "29 of 30 seeded"), encoding="utf-8")
    result = build_docs(tmp_path)
    assert "README.md" in result
    assert f"<!-- GENERATED:benchmark-headline -->{HEADLINE}<!-- /GENERATED:benchmark-headline -->" in result["README.md"]


def test_apply_markers_replaces_matched_span():
    text = "before <!-- GENERATED:x --> stale <!-- /GENERATED:x --> after\n"
    out = apply_markers(text, {"x": lambda: "fresh"})
    assert out == "before <!-- GENERATED:x -->fresh<!-- /GENERATED:x --> after\n"


def test_apply_markers_raises_on_unknown_key():
    text = "<!-- GENERATED:mystery -->x<!-- /GENERATED:mystery -->\n"
    with pytest.raises(ValueError, match="mystery"):
        apply_markers(text, {})


def test_apply_markers_raises_on_unmatched_marker():
    text = "<!-- GENERATED:x -->only the open half\n"
    with pytest.raises(ValueError, match="x"):
        apply_markers(text, {"x": lambda: "y"})


def test_apply_markers_leaves_content_outside_markers_untouched():
    text = "# Title\n\nSome hand-written prose.\n\n<!-- GENERATED:n -->0<!-- /GENERATED:n -->\n\nMore prose.\n"
    out = apply_markers(text, {"n": lambda: "1"})
    assert "# Title" in out and "Some hand-written prose." in out and "More prose." in out
    assert "<!-- GENERATED:n -->1<!-- /GENERATED:n -->" in out


def test_apply_markers_is_a_noop_with_no_markers_present():
    text = "# Title\n\nJust prose, no markers.\n"
    assert apply_markers(text, {"anything": lambda: "z"}) == text


def test_build_docs_covers_only_docs_with_drift(tmp_path):
    # a tiny root: one doc with a stale marker (must appear in the result), one doc with no
    # markers at all (must not appear), one doc whose required markers are already in sync (must
    # not appear either), matching build_docs's drift-only contract
    cat_dir = tmp_path / "kit" / "catalog"
    cat_dir.mkdir(parents=True)
    import json
    cat_dir.joinpath("catalog.json").write_text(json.dumps({
        "version": "0.0.0",
        "stages": [{"name": "Start", "summary": "begin"}],
        "prompts": [{"name": "orient-repo", "path": "prompts/core/orient-repo.md",
                     "summary": "map a repo", "stage": "Start"}],
        "templates": [], "adapters": [], "checks": [],
    }), encoding="utf-8")
    _write_results(tmp_path)
    (tmp_path / "README.md").write_text(README_IN_SYNC.replace("-->one<!--", "-->nine<!--"),
                                        encoding="utf-8")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "onboarding.md").write_text("# Onboarding\n\nno markers here.\n",
                                                       encoding="utf-8")
    (tmp_path / "docs" / "workflow.md").write_text(
        "The kit ships <!-- GENERATED:core-count-digits -->9<!-- /GENERATED:core-count-digits --> prompts.\n"
        "<!-- GENERATED:skills-table -->\nstale\n<!-- /GENERATED:skills-table -->\n",
        encoding="utf-8")
    (tmp_path / "docs" / "plugin.md").write_text(
        "# Plugin\n\n"
        "<!-- GENERATED:core-count-words -->one<!-- /GENERATED:core-count-words -->\n",
        encoding="utf-8")
    result = build_docs(tmp_path)
    assert "README.md" in result
    assert "docs/workflow.md" in result
    assert "docs/onboarding.md" not in result
    assert "docs/plugin.md" not in result
    assert "one" in result["README.md"]
    assert "| Stage | Prompts | Use them to |" in result["docs/workflow.md"]  # the generated header row
    assert "| Start | `orient-repo` | begin |" in result["docs/workflow.md"]
    assert "<!-- GENERATED:core-count-digits -->1<!-- /GENERATED:core-count-digits -->" in result["docs/workflow.md"]


def test_build_docs_raises_when_a_required_marker_is_stripped(tmp_path):
    # a required marker pair removed from README.md (e.g. by a careless hand-edit) must fail the
    # build loudly, not silently stop verifying that content
    cat_dir = tmp_path / "kit" / "catalog"
    cat_dir.mkdir(parents=True)
    import json
    cat_dir.joinpath("catalog.json").write_text(json.dumps({
        "version": "0.0.0",
        "stages": [{"name": "Start", "summary": "begin"}],
        "prompts": [{"name": "orient-repo", "path": "prompts/core/orient-repo.md",
                     "summary": "map a repo", "stage": "Start"}],
        "templates": [], "adapters": [], "checks": [],
    }), encoding="utf-8")
    _write_results(tmp_path)
    (tmp_path / "README.md").write_text(README_IN_SYNC, encoding="utf-8")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "workflow.md").write_text(
        "<!-- GENERATED:core-count-digits -->1<!-- /GENERATED:core-count-digits -->\n", encoding="utf-8")
    (tmp_path / "docs" / "plugin.md").write_text(
        "<!-- GENERATED:core-count-words -->one<!-- /GENERATED:core-count-words -->\n", encoding="utf-8")
    with pytest.raises(ValueError, match="skills-table"):
        build_docs(tmp_path)


def test_build_docs_raises_on_a_core_prompt_with_a_typo_d_stage(tmp_path):
    # a core prompt whose stage does not match any entry in the catalog's stages list (a realistic
    # typo against the new stages schema) must raise a clear ValueError naming the bad stage, not a
    # bare KeyError from the skills-table renderer's dict lookup
    cat_dir = tmp_path / "kit" / "catalog"
    cat_dir.mkdir(parents=True)
    import json
    cat_dir.joinpath("catalog.json").write_text(json.dumps({
        "version": "0.0.0",
        "stages": [{"name": "Start", "summary": "begin"}],
        "prompts": [{"name": "orient-repo", "path": "prompts/core/orient-repo.md",
                     "summary": "map a repo", "stage": "Start-typo"}],
        "templates": [], "adapters": [], "checks": [],
    }), encoding="utf-8")
    _write_results(tmp_path)
    (tmp_path / "README.md").write_text(README_IN_SYNC, encoding="utf-8")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "workflow.md").write_text(
        "<!-- GENERATED:core-count-digits -->1<!-- /GENERATED:core-count-digits -->\n"
        "<!-- GENERATED:skills-table -->\nstale\n<!-- /GENERATED:skills-table -->\n",
        encoding="utf-8")
    (tmp_path / "docs" / "plugin.md").write_text(
        "<!-- GENERATED:core-count-words -->one<!-- /GENERATED:core-count-words -->\n",
        encoding="utf-8")
    with pytest.raises(ValueError, match="Start-typo"):
        build_docs(tmp_path)


def test_checks_line_renderer_emits_count_word_and_names():
    from kit.docs_build import _render_checks_line
    cat = _cat(checks=[{"name": "structure", "module": "m", "summary": "s"},
                       {"name": "catalog", "module": "m", "summary": "s"},
                       {"name": "roadmap", "module": "m", "summary": "s"}])
    assert _render_checks_line(cat) == "three checks (structure, catalog, roadmap)"


def test_roadmap_stage_counts_follow_catalog_order():
    import kit.docs_build as docs_build
    assert hasattr(docs_build, "_render_stage_counts"), "stage-counts renderer is missing"
    cat = _cat(
        stages=[
            {"name": "Build", "summary": "build"},
            {"name": "Start", "summary": "start"},
            {"name": "Scrutiny", "summary": "check"},
            {"name": "Archive", "summary": "archive"},
        ],
        prompts=[
            {"name": "build-a", "path": "prompts/core/build-a.md", "summary": "a",
             "stage": "Build"},
            {"name": "start-a", "path": "prompts/core/start-a.md", "summary": "a",
             "stage": "Start"},
            {"name": "build-b", "path": "prompts/core/build-b.md", "summary": "b",
             "stage": "Build"},
            {"name": "check-a", "path": "prompts/core/check-a.md", "summary": "a",
             "stage": "Scrutiny"},
            {"name": "check-b", "path": "prompts/core/check-b.md", "summary": "b",
             "stage": "Scrutiny"},
        ],
    )
    assert docs_build._render_stage_counts(cat) == (
        "two build, one start, two scrutiny, and zero archive"
    )
    assert "stage-counts" in docs_build.REQUIRED_MARKERS["docs/ROADMAP.md"]


def test_stage_counts_joins_exactly_two_stages_without_a_comma():
    import kit.docs_build as docs_build
    cat = _cat(
        stages=[{"name": "Start", "summary": "start"}, {"name": "Build", "summary": "build"}],
        prompts=[{"name": "start-a", "path": "prompts/core/start-a.md", "summary": "a",
                  "stage": "Start"}],
    )
    assert docs_build._render_stage_counts(cat) == "one start and zero build"


def test_stage_counts_raises_on_a_core_prompt_with_a_typo_d_stage():
    import kit.docs_build as docs_build
    cat = _cat(
        stages=[{"name": "Start", "summary": "start"}],
        prompts=[{"name": "start-a", "path": "prompts/core/start-a.md", "summary": "a",
                  "stage": "Start-typo"}],
    )
    with pytest.raises(ValueError, match="Start-typo"):
        docs_build._render_stage_counts(cat)
