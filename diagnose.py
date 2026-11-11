import json
import re
import sys
from pathlib import Path

PROJECT = Path(r"C:\IQ projects\AIQ")
MD_DIR = PROJECT / "dummy_v2_md"

question_id = sys.argv[1]  # e.g. Q002
data = json.loads((PROJECT / "eval_questions.json").read_text(encoding="utf-8"))
questions = data["questions"] if isinstance(data, dict) and "questions" in data else data
question = next(item for item in questions if item["id"] == question_id)

md_path = MD_DIR / (Path(question["source_file"]).stem + ".md")
markdown = md_path.read_text(encoding="utf-8")
paragraphs = [p.strip() for p in re.split(r"\n\s*\n", markdown) if p.strip()]

expected = question["expected_answer"]
expected_words = set(re.findall(r"\w{4,}", expected.lower()))

print("EXPECTED:", expected)
print(f"MD file: {md_path.name}, {len(markdown)} chars, {len(paragraphs)} paragraphs\n")

scored = []
for paragraph in paragraphs:
    paragraph_words = set(re.findall(r"\w{4,}", paragraph.lower()))
    overlap = len(expected_words & paragraph_words) / max(len(expected_words), 1)
    scored.append((overlap, paragraph, expected_words - paragraph_words))
scored.sort(key=lambda item: item[0], reverse=True)

for overlap, paragraph, missing in scored[:3]:
    print(f"--- word overlap {overlap:.0%}")
    print("missing words:", [ascii(word) for word in sorted(missing)])
    print(paragraph[:500], "\n")