from aiq.config import MD_DIR
from aiq.questions import load_questions

questions = load_questions()

file_clients = {p.stem.split("-")[-1].lower() for p in MD_DIR.glob("*.md")}
for q in questions:
    client = q.get("client", "").lower()
    if client not in file_clients:
        print(q["id"], repr(q.get("client")), q.get("trap_type"), q.get("source_file"))
print("clients with chunks:", sorted(file_clients))