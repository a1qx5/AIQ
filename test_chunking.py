from pathlib import Path
from chunking import chunk_markdown

MD_DIR = Path(r"C:\IQ projects\AIQ\dummy_md")

for md_file in sorted(MD_DIR.glob("*.md")):
    markdown = md_file.read_text(encoding="utf-8")
    chunks = chunk_markdown(markdown, source_path=md_file.name)

    print(f"\n=== {md_file.name}: {len(markdown)} chars -> {len(chunks)} chunks")
    for chunk in chunks:
        preview = chunk["text"][:80].replace("\n", " ")
        print(f"  [{chunk['chunk_index']}] {len(chunk['text']):>5} chars | "
              f"{chunk['heading_path'] or '(no heading)'} | {preview}")