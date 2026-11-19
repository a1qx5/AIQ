import hashlib
import json

from aiq.chunking import (split_into_sections, chunk_markdown, MAX_CHARS, OVERLAP,
                          merge_small_sections, MERGE_LIMIT, CHUNKER_VERSION)


def test_nested_heading_paths():
    md = "# A\n\nintro\n\n## B\n\ntext b\n\n### C\n\ntext c\n\n## D\n\ntext d"
    paths = [s["heading_path"] for s in split_into_sections(md)]
    assert paths == ["A", "A > B", "A > B > C", "A > D"], paths


def test_long_paragraph_is_split_with_overlap():
    md = "# T\n\n" + "word " * 1000          # one 5000-character paragraph
    chunks = chunk_markdown(md, "long.md")
    assert len(chunks) > 1
    assert all(len(c["text"]) <= MAX_CHARS for c in chunks)
    # the end of one piece must repeat at the start of the next
    assert chunks[0]["text"][-OVERLAP:] == chunks[1]["text"][:OVERLAP]


def test_table_is_never_cut():
    table = "| a | b |\n|---|---|\n| 1 | 2 |\n| 3 | 4 |"
    filler = "x" * 1480                         # forces a chunk break on each side
    md = f"# T\n\n{filler}\n\n{table}\n\n{filler}"
    chunks = chunk_markdown(md, "table.md")
    holders = [c for c in chunks if table in c["text"]]
    assert len(holders) == 1, "table must sit whole inside exactly one chunk"


def test_no_heading_document():
    chunks = chunk_markdown("Just a short text.\n\nSecond paragraph.", "plain.md")
    assert len(chunks) == 1
    assert chunks[0]["heading_path"] == ""


def test_hash_inside_code_block_is_not_a_heading():
    md = "# A\n\n```\n# not a heading\n```\n\ntext"
    paths = [s["heading_path"] for s in split_into_sections(md)]
    assert paths == ["A"], paths


def test_small_sections_are_merged_with_titles_kept():
    sections = [
        {"heading_path": "Deck > Slide 1", "text": "Point A."},
        {"heading_path": "Deck > Slide 2", "text": "Point B."},
        {"heading_path": "Deck > Slide 3", "text": "Point C."},
    ]
    merged = merge_small_sections(sections)
    assert len(merged) == 1
    for expected in ("Slide 1", "Slide 2", "Slide 3", "Point A.", "Point B.", "Point C."):
        assert expected in merged[0]["text"], expected


def test_large_section_is_left_alone():
    # A large section is never merged into its neighbours' group. Since the forward-merge
    # rule, a small section directly BEFORE it is prepended to it (see the forward-merge
    # tests below); a small section AFTER it still stays separate.
    big = {"heading_path": "Big", "text": "x" * 500}
    small = {"heading_path": "Small", "text": "y"}
    merged = merge_small_sections([big, small])
    assert [m["text"] for m in merged] == ["x" * 500, "y"]


def test_small_title_section_is_prepended_to_following_large_section():
    title = {"heading_path": "Doc > Version", "text": "Version 2.5 | September 2026"}
    big = {"heading_path": "Doc > Architecture", "text": "x" * 500}
    merged = merge_small_sections([title, big])
    assert len(merged) == 1
    assert merged[0]["heading_path"] == "Doc > Architecture"   # the large section's path
    assert merged[0]["text"].startswith("Version\nVersion 2.5 | September 2026")
    assert merged[0]["text"].endswith("x" * 500)


def test_forward_merge_is_skipped_when_it_would_exceed_max_chars():
    title = {"heading_path": "Doc > Version", "text": "Version 2.5"}
    big = {"heading_path": "Doc > Architecture", "text": "x" * (MAX_CHARS - 5)}
    merged = merge_small_sections([title, big])
    assert [m["text"] for m in merged] == ["Version 2.5", "x" * (MAX_CHARS - 5)]
    assert [m["heading_path"] for m in merged] == ["Doc > Version", "Doc > Architecture"]


def test_small_group_at_end_of_document_still_works():
    big = {"heading_path": "Big", "text": "x" * 500}
    tail = [{"heading_path": "Tail > A", "text": "a"}, {"heading_path": "Tail > B", "text": "b"}]
    merged = merge_small_sections([big] + tail)
    assert len(merged) == 2
    assert merged[0]["text"] == "x" * 500
    assert "A\na" in merged[1]["text"] and "B\nb" in merged[1]["text"]
    # and through the full pipeline, a one-line last section is still a chunk
    chunks = chunk_markdown("# Big\n\n" + "x" * 500 + "\n\n# End\n\nBye.", "end.md")
    assert chunks[-1]["text"] == "Bye."


def test_merged_group_respects_limit():
    sections = [{"heading_path": f"S{i}", "text": "z" * 250} for i in range(10)]
    merged = merge_small_sections(sections)
    assert len(merged) > 1
    for m in merged:
        assert len(m["text"]) <= MERGE_LIMIT + 100, len(m["text"])


GOLDEN_SAMPLE = (
    "# Handbook\n\n"
    "## Version\n\nVersion 2.5 | September 2026\n\n"
    "## Architecture\n\n" + "The service layer talks to the database. " * 12 + "\n\n"
    "### Storage\n\nShort note.\n\n"
    "### Limits\n\nAnother short note.\n\n"
    "## Long text\n\n" + "word " * 700 + "\n\n"
    "## Prices\n\n"
    "| plan | price |\n|---|---|\n| basic | 10 |\n| pro | 25 |\n\n"
    "## Contact\n\nwrite to us."
)

# sha256 of the chunker output for GOLDEN_SAMPLE, per CHUNKER_VERSION.
GOLDEN = {"1": "3be13f6dd5e79ff7dfb7f97a24554302fbe1db0cdc3fc0bfa503196ff996eee6"}


def chunker_output_hash():
    chunks = chunk_markdown(GOLDEN_SAMPLE, "golden.md")
    serialised = json.dumps(chunks, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(serialised.encode("utf-8")).hexdigest()


def test_golden_chunker_output():
    actual = chunker_output_hash()
    assert actual == GOLDEN.get(CHUNKER_VERSION), (
        "Chunker output changed: bump CHUNKER_VERSION and add the new hash to GOLDEN "
        f"(version {CHUNKER_VERSION}, new hash {actual})"
    )


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("PASS", name)