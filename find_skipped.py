import json
from pathlib import Path

PROJECT = Path(r"C:\IQ projects\AIQ")
data = json.loads((PROJECT / "eval_questions.json").read_text(encoding="utf-8"))
questions = data["questions"] if isinstance(data, dict) and "questions" in data else data

file_clients = {p.stem.split("-")[-1].lower() for p in (PROJECT / "dummy_v2_md").glob("*.md")}
for q in questions:
    client = q.get("client", "").lower()
    if client not in file_clients:
        print(q["id"], repr(q.get("client")), q.get("trap_type"), q.get("source_file"))
print("clients with chunks:", sorted(file_clients))