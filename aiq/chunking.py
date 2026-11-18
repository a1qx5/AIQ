import re

MAX_CHARS = 1500   # target chunk size; tune this later against your test questions
OVERLAP = 200      # only used when one paragraph alone exceeds MAX_CHARS
MIN_SECTION_CHARS = 300   # a section shorter than this counts as "small"
MERGE_LIMIT = 800         # a merged group of small sections may not exceed this


def split_into_sections(markdown):
    """Cut the Markdown at headings. Returns a list of
    {"heading_path": "A > B", "text": "..."} dictionaries."""
    sections = []
    heading_stack = []   # e.g. [(1, "Strategie"), (2, "SEO")]
    current_lines = []
    in_code_block = False

    def save_current_section():
        text = "\n".join(current_lines).strip()
        if text:
            path = " > ".join(title for _, title in heading_stack)
            sections.append({"heading_path": path, "text": text})
        current_lines.clear()

    for line in markdown.splitlines():
        if line.strip().startswith("```"):
            in_code_block = not in_code_block   # '#' inside code is not a heading

        heading = None if in_code_block else re.match(r"^(#{1,6})\s+(.*)$", line)

        if heading:
            save_current_section()
            level = len(heading.group(1))
            title = heading.group(2).strip()
            # A heading closes every open heading of the same or lower level.
            while heading_stack and heading_stack[-1][0] >= level:
                heading_stack.pop()
            heading_stack.append((level, title))
        else:
            current_lines.append(line)

    save_current_section()
    return sections


def hard_split(paragraph):
    """Last resort for one very long paragraph. May cut mid-word, which is
    acceptable for now (better: split at sentence ends)."""
    pieces = []
    start = 0
    while start < len(paragraph):
        end = start + MAX_CHARS
        pieces.append(paragraph[start:end])
        if end >= len(paragraph):
            break
        start = end - OVERLAP
    return pieces


def pack_paragraphs(text):
    """Group the paragraphs of one section into chunks of at most MAX_CHARS."""
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks = []
    current = ""

    for paragraph in paragraphs:
        if len(paragraph) > MAX_CHARS:
            if current:
                chunks.append(current)
                current = ""
            chunks.extend(hard_split(paragraph))
        elif current and len(current) + 2 + len(paragraph) > MAX_CHARS:
            chunks.append(current)
            current = paragraph
        elif current:
            current = current + "\n\n" + paragraph
        else:
            current = paragraph

    if current:
        chunks.append(current)
    return chunks


def merge_small_sections(sections):
    """Join consecutive small sections so that slides and one-line sections do
    not become tiny chunks. In a merged group, every section's own title is kept
    inside the text, so the chunk still shows what each part is about."""
    merged = []
    group = []   # small sections waiting to be joined

    def flush_group():
        if not group:
            return
        if len(group) == 1:
            merged.append(group[0])          # a lone small section stays as it is
        else:
            parts = []
            for section in group:
                title = section["heading_path"].split(" > ")[-1]
                parts.append((title + "\n" + section["text"]).strip())
            merged.append({
                "heading_path": group[0]["heading_path"],
                "text": "\n\n".join(parts),
            })
        group.clear()

    for section in sections:
        size = len(section["text"])
        if size >= MIN_SECTION_CHARS:
            flush_group()
            merged.append(section)           # a large section is never merged
            continue
        group_size = sum(len(s["text"]) for s in group)
        if group and group_size + size > MERGE_LIMIT:
            flush_group()
        group.append(section)

    flush_group()
    return merged


def chunk_markdown(markdown, source_path):
    """Main entry point: Markdown in, a list of chunk dictionaries out."""
    chunks = []
    for section in merge_small_sections(split_into_sections(markdown)):
        for text in pack_paragraphs(section["text"]):
            chunks.append({
                "source_path": source_path,
                "heading_path": section["heading_path"],
                "chunk_index": len(chunks),
                "text": text,
            })
    return chunks

# The text that is actually embedded for a chunk. Used by ingestion, by the
# eval scripts, and by the pipeline fingerprint, so there is one copy only.
# Changing it changes the fingerprint, which makes ingestion re-embed everything.
EMBED_TEMPLATE = "Client: {client} | Document: {file_stem} | Section: {heading_path}\n\n{text}"


def build_embed_text(client, file_stem, heading_path, text):
    return EMBED_TEMPLATE.format(client=client, file_stem=file_stem,
                                 heading_path=heading_path, text=text)
