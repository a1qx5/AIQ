from chunking import split_into_sections, chunk_markdown, MAX_CHARS, OVERLAP, merge_small_sections, MERGE_LIMIT


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
    big = {"heading_path": "Big", "text": "x" * 500}
    small = {"heading_path": "Small", "text": "y"}
    merged = merge_small_sections([small, big, small])
    assert [m["text"] for m in merged] == ["y", "x" * 500, "y"]


def test_merged_group_respects_limit():
    sections = [{"heading_path": f"S{i}", "text": "z" * 250} for i in range(10)]
    merged = merge_small_sections(sections)
    assert len(merged) > 1
    for m in merged:
        assert len(m["text"]) <= MERGE_LIMIT + 100, len(m["text"])


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("PASS", name)