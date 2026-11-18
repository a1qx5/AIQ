import json
import re
from pathlib import Path
from aiq.chunking import chunk_markdown
from aiq.config import MD_DIR
from aiq.questions import load_questions


def normalize(text):
    return re.sub(r"\s+", " ", text).strip().lower()


def numbers_in(text):
    # "142.000 EUR" and "142,000 EUR" both become "142000"
    return {re.sub(r"\D", "", n) for n in re.findall(r"\d[\d.,]*\d|\d", text)}


def core_answer(expected):
    """Extract the answer before any parenthetical commentary.

    Example: "125.000 EUR (superseded by 142.000 EUR in November)" -> "125.000 EUR"
    """
    paren_pos = expected.find(" (")
    if paren_pos != -1:
        return expected[:paren_pos]
    return expected


def words_in(text):
    return set(re.findall(r"\w{3,}", text.lower()))


def fact_found(expected, text):
    """Returns 'exact' (the literal phrase), 'loose' (all the numbers, or all
    the words, found together in ONE paragraph, so word order doesn't matter),
    or None (not found)."""
    if normalize(expected) in normalize(text):
        return "exact"

    expected_numbers = numbers_in(expected)
    expected_words = words_in(expected)
    for paragraph in re.split(r"\n\s*\n", text):
        if expected_numbers and expected_numbers <= numbers_in(paragraph):
            return "loose"
        if expected_words and expected_words <= words_in(paragraph):
            return "loose"
    return None


questions = load_questions()

counts = {"OK": 0, "LOST_IN_CONVERSION": 0, "SPLIT_BY_CHUNKER": 0, "NO_MD_FILE": 0, "SKIPPED_NO_SINGLE_SOURCE": 0}

for q in questions:
    expected = q.get("expected_answer", "")
    source_file = q.get("source_file")
    if not source_file or expected == "NOT_IN_CORPUS":
        continue  # unanswerable questions have nothing to find

    # Check if source_file looks like a real single file (has extension)
    if not source_file or source_file == "multiple" or "." not in source_file:
        status = "SKIPPED_NO_SINGLE_SOURCE"
        counts[status] += 1
        print(f"{status:<25} {q['id']:<6} {str(q.get('trap_type')):<14}")
        continue

    md_path = MD_DIR / (Path(source_file).stem + ".md")
    if not md_path.exists():
        status = "NO_MD_FILE"
    else:
        markdown = md_path.read_text(encoding="utf-8")
        chunks = chunk_markdown(markdown, source_path=md_path.name)
        core_expected = core_answer(expected)
        if not fact_found(core_expected, markdown):
            status = "LOST_IN_CONVERSION"
        elif not any(fact_found(core_expected, c["text"]) for c in chunks):
            status = "SPLIT_BY_CHUNKER"
        else:
            status = "OK"

    counts[status] += 1
    if status != "OK":
        print(f"{status:<20} {q['id']:<6} {str(q.get('trap_type')):<14} "
              f"{source_file} | {q.get('location')}")

print("\nSummary:", counts)

# Per-file chunk statistics
print("\n" + "="*80)
print("CHUNK STATISTICS")
print("="*80)
print(f"{'File':<50} {'Chunks':>7} {'Min':>6} {'Avg':>6} {'Max':>6} {'<150':>5}")
print("-" * 80)

md_files = sorted(MD_DIR.glob("*.md"))
for md_file in md_files:
    markdown = md_file.read_text(encoding="utf-8")
    chunks = chunk_markdown(markdown, source_path=md_file.name)

    if chunks:
        chunk_lengths = [len(c["text"]) for c in chunks]
        num_chunks = len(chunks)
        min_len = min(chunk_lengths)
        avg_len = sum(chunk_lengths) // num_chunks
        max_len = max(chunk_lengths)
        under_150 = sum(1 for length in chunk_lengths if length < 150)

        print(f"{md_file.name:<50} {num_chunks:>7} {min_len:>6} {avg_len:>6} {max_len:>6} {under_150:>5}")
    else:
        print(f"{md_file.name:<50} {'0':>7} {'N/A':>6} {'N/A':>6} {'N/A':>6} {'0':>5}")