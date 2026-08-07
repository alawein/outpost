"""The prose_length check catches a sprawling paragraph, respects markdown structure, and exempts
the append-only ledgers it cannot fairly hold to the ceiling."""
import pathlib

from kit.checks import prose_length

ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_prose_length_passes_on_the_real_repo():
    ok, detail = prose_length.run(ROOT)
    assert ok, detail


def test_paragraphs_splits_on_blank_lines():
    body = "First paragraph, one line.\n\nSecond paragraph, another line.\n"
    assert prose_length.paragraphs(body) == [
        "First paragraph, one line.",
        "Second paragraph, another line.",
    ]


def test_paragraphs_joins_wrapped_lines_into_one():
    body = "This sentence wraps\nacross two source lines\nas one paragraph.\n"
    assert prose_length.paragraphs(body) == [
        "This sentence wraps across two source lines as one paragraph."
    ]


def test_paragraphs_skips_headings_list_items_tables_and_blockquotes():
    body = (
        "# A heading\n\n"
        "- a list item\n"
        "- another\n\n"
        "| a | table |\n"
        "|---|---|\n"
        "| row | here |\n\n"
        "> a blockquote\n\n"
        "Real prose paragraph.\n"
    )
    assert prose_length.paragraphs(body) == ["Real prose paragraph."]


def test_paragraphs_skips_fenced_code_blocks():
    body = "Real prose.\n\n```\nnot prose, however long this fake code block pretends to be\n```\n\nMore real prose.\n"
    assert prose_length.paragraphs(body) == ["Real prose.", "More real prose."]


def test_run_flags_a_paragraph_over_the_ceiling(tmp_path):
    long_para = " ".join(["word"] * (prose_length.MAX_PARAGRAPH_WORDS + 1))
    (tmp_path / "doc.md").write_text(f"# Doc\n\n{long_para}\n", encoding="utf-8")
    ok, detail = prose_length.run(tmp_path)
    assert not ok and "paragraph too long" in detail and "doc.md" in detail


def test_run_passes_a_paragraph_at_exactly_the_ceiling(tmp_path):
    at_ceiling = " ".join(["word"] * prose_length.MAX_PARAGRAPH_WORDS)
    (tmp_path / "doc.md").write_text(f"# Doc\n\n{at_ceiling}\n", encoding="utf-8")
    ok, detail = prose_length.run(tmp_path)
    assert ok, detail


def test_run_strips_frontmatter_before_measuring(tmp_path):
    # a long frontmatter description is a distinct field (lint_prompt covers its own floor,
    # no ceiling), not markdown-body prose; it must not trip this check
    long_desc = " ".join(["word"] * (prose_length.MAX_PARAGRAPH_WORDS + 1))
    text = f"---\nname: x\ndescription: {long_desc}\n---\n\n# x\n\nShort body paragraph.\n"
    (tmp_path / "x.md").write_text(text, encoding="utf-8")
    ok, detail = prose_length.run(tmp_path)
    assert ok, detail


def test_is_exempt_covers_the_append_only_ledgers():
    assert prose_length.is_exempt("docs/DEBT.md")
    assert prose_length.is_exempt("docs/dogfooding.md")
    assert prose_length.is_exempt("docs/decisions/0001-repo-architecture.md")
    assert prose_length.is_exempt("docs/audit/2026-07-12.md")
    assert not prose_length.is_exempt("docs/contributing.md")
    assert not prose_length.is_exempt("README.md")


def test_run_skips_an_exempt_file_even_when_it_would_fail(tmp_path):
    long_para = " ".join(["word"] * (prose_length.MAX_PARAGRAPH_WORDS + 1))
    decisions = tmp_path / "docs" / "decisions"
    decisions.mkdir(parents=True)
    (decisions / "0099-example.md").write_text(f"# 0099\n\n{long_para}\n", encoding="utf-8")
    ok, detail = prose_length.run(tmp_path)
    assert ok, detail
