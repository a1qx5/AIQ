"""Shared paths. Every script gets its folders from here, so nothing is hard-coded."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = ROOT / "data"
CORPUS_DIR = DATA_DIR / "dummy_v2"        # source files (docx, pptx, pdf, xlsx)
MD_DIR = DATA_DIR / "dummy_v2_md"         # Markdown made by Docling
OLD_MD_DIR = DATA_DIR / "dummy_md"        # first (v1) corpus, used only by archive/test_chunking.py

QUESTIONS_FILE = ROOT / "evals" / "eval_questions.json"
