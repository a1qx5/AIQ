import re
import sys
from pathlib import Path

from dotenv import load_dotenv

from aiq.chunking import chunk_markdown, build_embed_text
from aiq.config import MD_DIR
from aiq.embedders import get_embedder
from aiq.questions import load_questions

load_dotenv()
SHOW_TOP = 4

model_name = sys.argv[1]      # bge-m3 or voyage
question_id = sys.argv[2]     # e.g. Q003

questions = load_questions()
question = next(q for q in questions if q["id"] == question_id)
client = question["client"].lower()

records = []
for md_path in sorted(MD_DIR.glob("*.md")):
    if md_path.stem.split("-")[-1].lower() != client:
        continue
    markdown = md_path.read_text(encoding="utf-8")
    for chunk in chunk_markdown(markdown, source_path=md_path.name):
        records.append({
            "file": md_path.stem,
            "heading": chunk["heading_path"],
            "text": chunk["text"],
            "embed_text": build_embed_text(client, md_path.stem,
                                           chunk["heading_path"], chunk["text"]),
        })

embed = get_embedder(model_name)
chunk_vectors = embed([r["embed_text"] for r in records], is_query=False)
question_vector = embed([question["question"]], is_query=True)[0]
scores = chunk_vectors @ question_vector
order = scores.argsort()[::-1]

expected_core = re.split(r"\s*\(", question["expected_answer"])[0].strip().lower()
source_stem = Path(question["source_file"]).stem

print("QUESTION:", question["question"])
print("EXPECTED:", question["expected_answer"])
print("SOURCE  :", source_stem, "| trap:", question.get("trap_type"))

for position, index in enumerate(order[:SHOW_TOP], start=1):
    record = records[index]
    from_source = "SOURCE FILE" if record["file"] == source_stem else ""
    flat_text = re.sub(r"\s+", " ", record["text"].lower())
    has_fact = "EXACT FACT HERE" if expected_core in flat_text else ""
    print(f"\n#{position}  score {scores[index]:.2f}  {from_source}  {has_fact}")
    print(f"    {record['file']} | {record['heading'] or '(no heading)'}")
    print("    " + record["text"][:250].replace("\n", " "))