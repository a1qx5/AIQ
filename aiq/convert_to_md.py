"""Convert every file in data/dummy_v2 to Markdown with Docling.
Run from the project root: python -m aiq.convert_to_md  (Docling container must be up)."""
import requests

from aiq.config import CORPUS_DIR, MD_DIR

DOCLING_URL = "http://localhost:5001/v1/convert/file"
DUMMY_DIR = CORPUS_DIR
OUT_DIR = MD_DIR
OUT_DIR.mkdir(parents=True, exist_ok=True)

for file_path in sorted(DUMMY_DIR.iterdir()):
    if not file_path.is_file():
        continue

    try:
        with open(file_path, "rb") as f:
            response = requests.post(
                DOCLING_URL,
                files={"files": f},
                data={"to_formats": "md"},
                timeout=300,
            )
        response.raise_for_status()
        result = response.json()
    except Exception as error:
        print(f"FAILED  {file_path.name}: {error}")
        continue

    markdown = result["document"]["md_content"] or ""
    print(
        f"{result['status']:<10} {file_path.name:<35} "
        f"{len(markdown):>6} chars  {result['processing_time']:.1f}s  "
        f"errors={result['errors']}"
    )

    # utf-8 on purpose: the Windows console can garble ă, ș, ț when printing,
    # which would look like a Docling bug but isn't one.
    (OUT_DIR / (file_path.stem + ".md")).write_text(markdown, encoding="utf-8")