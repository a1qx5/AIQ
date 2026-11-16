import json
from pathlib import Path

from dotenv import load_dotenv

from chunking import chunk_markdown
from embedders import get_embedder

load_dotenv()

PROJECT = Path(r"C:\IQ projects\AIQ")
MD_DIR = PROJECT / "dummy_v2_md"
QUESTIONS_FILE = PROJECT / "eval_questions.json"
MODELS_TO_TEST = ["bge-m3", "voyage"]   # edit this list to run one or both


def load_chunk_records():
    records = []
    for md_path in sorted(MD_DIR.glob("*.md")):
        client = md_path.stem.split("-")[-1].lower()   # "...-technova" -> "technova"
        markdown = md_path.read_text(encoding="utf-8")
        for chunk in chunk_markdown(markdown, source_path=md_path.name):
            records.append({
                "client": client,
                "source_stem": md_path.stem,
                "embed_text": (
                    f"Client: {client} | Document: {md_path.stem} | "
                    f"Section: {chunk['heading_path']}\n\n{chunk['text']}"
                ),
            })
    return records


def load_questions():
    data = json.loads(QUESTIONS_FILE.read_text(encoding="utf-8"))
    return data["questions"] if isinstance(data, dict) and "questions" in data else data


def evaluate(embed, chunk_records, chunk_vectors, questions):
    """Returns one result dictionary per question."""
    question_vectors = embed([q["question"] for q in questions], is_query=True)
    results = []

    for q, q_vector in zip(questions, question_vectors):
        client = q.get("client", "").lower()
        candidates = [i for i, r in enumerate(chunk_records) if r["client"] == client]
        if not candidates:
            results.append({"id": q["id"], "kind": "no_client"})
            continue

        scores = chunk_vectors[candidates] @ q_vector       # cosine similarities
        ranked = [candidates[i] for i in scores.argsort()[::-1]]
        best_score = float(scores.max())

        unanswerable = q.get("expected_answer") == "NOT_IN_CORPUS" or not q.get("source_file")
        if unanswerable:
            results.append({"id": q["id"], "kind": "unanswerable", "best_score": best_score})
            continue

        source_stem = Path(q["source_file"]).stem
        rank = None
        for position, chunk_index in enumerate(ranked, start=1):
            if chunk_records[chunk_index]["source_stem"] == source_stem:
                rank = position
                break
        results.append({"id": q["id"], "kind": "answerable", "rank": rank,
                        "trap": q.get("trap_type"), "best_score": best_score})
    return results


chunk_records = load_chunk_records()
questions = load_questions()
print(f"{len(chunk_records)} chunks, {len(questions)} questions")

all_results = {}
for model_name in MODELS_TO_TEST:
    print(f"\n=== {model_name}")
    embed = get_embedder(model_name)
    chunk_vectors = embed([r["embed_text"] for r in chunk_records], is_query=False)
    print("vector matrix shape:", chunk_vectors.shape)
    all_results[model_name] = evaluate(embed, chunk_records, chunk_vectors, questions)

    answerable = [r for r in all_results[model_name] if r["kind"] == "answerable"]
    for k in (1, 3, 5):
        hits = sum(1 for r in answerable if r["rank"] is not None and r["rank"] <= k)
        print(f"hit@{k}: {hits}/{len(answerable)} = {hits / len(answerable):.0%}")

    if answerable:
        mean_best = sum(r["best_score"] for r in answerable) / len(answerable)
        print(f"mean best score, answerable questions: {mean_best:.2f}")
    for r in all_results[model_name]:
        if r["kind"] == "unanswerable":
            print(f"unanswerable {r['id']}: best score {r['best_score']:.2f}")

# Side by side: only the questions where some model did not rank the right file first
print("\n=== Questions where at least one model missed rank 1")
print("id     trap               " + "  ".join(f"{m:>8}" for m in MODELS_TO_TEST))
first_model = MODELS_TO_TEST[0]
for index, r in enumerate(all_results[first_model]):
    if r["kind"] != "answerable":
        continue
    ranks = [all_results[m][index].get("rank") for m in MODELS_TO_TEST]
    if any(rank != 1 for rank in ranks):
        print(f"{r['id']:<6} {str(r['trap']):<18} " + "  ".join(f"{str(x):>8}" for x in ranks))