from aiq.chunking import chunk_markdown
from aiq.config import OLD_MD_DIR as MD_DIR

for md_file in sorted(MD_DIR.glob("*.md")):
    markdown = md_file.read_text(encoding="utf-8")
    chunks = chunk_markdown(markdown, source_path=md_file.name)

    print(f"\n=== {md_file.name}: {len(markdown)} chars -> {len(chunks)} chunks")
    for chunk in chunks:
        preview = chunk["text"][:80].replace("\n", " ")
        print(f"  [{chunk['chunk_index']}] {len(chunk['text']):>5} chars | "
              f"{chunk['heading_path'] or '(no heading)'} | {preview}")