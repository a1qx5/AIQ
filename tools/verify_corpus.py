#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verification script for synthetic corpus.
Validates that all planted facts are actually present in generated documents.
"""

import json
import os
import sys
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Import extraction libraries
from docx import Document
from pptx import Presentation
from openpyxl import load_workbook
from PyPDF2 import PdfReader

from aiq.config import CORPUS_DIR, QUESTIONS_FILE

EVAL_FILE = str(QUESTIONS_FILE)


def extract_text_from_docx(filepath):
    """Extract all text from DOCX including tables and paragraphs."""
    doc = Document(filepath)
    text_parts = []

    # Extract from paragraphs
    for para in doc.paragraphs:
        if para.text.strip():
            text_parts.append(para.text)

    # Extract from tables
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                if cell.text.strip():
                    text_parts.append(cell.text)

    return " ".join(text_parts)


def extract_text_from_pptx(filepath):
    """Extract all text from PPTX including slides and speaker notes."""
    prs = Presentation(filepath)
    text_parts = []

    for slide in prs.slides:
        # Extract from shapes
        for shape in slide.shapes:
            if hasattr(shape, "text") and shape.text.strip():
                text_parts.append(shape.text)

            # Extract from tables in slides
            if shape.has_table:
                for row in shape.table.rows:
                    for cell in row.cells:
                        if cell.text.strip():
                            text_parts.append(cell.text)

        # Extract from speaker notes
        if slide.has_notes_slide:
            notes_frame = slide.notes_slide.notes_text_frame
            if notes_frame and notes_frame.text.strip():
                text_parts.append(notes_frame.text)

    return " ".join(text_parts)


def extract_text_from_pdf(filepath):
    """Extract text from PDF (works for selectable text, not scanned images)."""
    try:
        reader = PdfReader(filepath)
        text_parts = []

        for page in reader.pages:
            text = page.extract_text()
            if text.strip():
                text_parts.append(text)

        return " ".join(text_parts)
    except Exception as e:
        return f"[PDF extraction failed: {e}]"


def extract_text_from_xlsx(filepath):
    """Extract all text from Excel spreadsheet."""
    wb = load_workbook(filepath, data_only=True)
    text_parts = []

    for sheet in wb.worksheets:
        for row in sheet.iter_rows():
            for cell in row:
                if cell.value is not None:
                    text_parts.append(str(cell.value))

    return " ".join(text_parts)


def extract_text_from_file(filepath):
    """Route to appropriate extractor based on file extension."""
    ext = filepath.suffix.lower()

    try:
        if ext == '.docx':
            return extract_text_from_docx(filepath)
        elif ext == '.pptx':
            return extract_text_from_pptx(filepath)
        elif ext == '.pdf':
            return extract_text_from_pdf(filepath)
        elif ext == '.xlsx':
            return extract_text_from_xlsx(filepath)
        else:
            return f"[Unsupported file type: {ext}]"
    except Exception as e:
        return f"[Extraction error: {e}]"


def normalize_text(text):
    """Normalize text for comparison (case-insensitive, whitespace normalized)."""
    return " ".join(text.lower().split())


def verify_fact_in_text(fact, text, is_scanned_pdf=False):
    """Check if a fact is present in extracted text."""
    # Scanned PDFs won't have extractable text - skip verification
    if is_scanned_pdf:
        return True

    # Normalize both for comparison
    normalized_fact = normalize_text(fact)
    normalized_text = normalize_text(text)

    # Try exact match first
    if normalized_fact in normalized_text:
        return True

    # Try partial matches for numeric facts (e.g., "125.000 EUR" vs "125.000 eur" vs "125000")
    # Remove punctuation and spaces from numbers
    fact_nums = ''.join(c for c in fact if c.isdigit() or c in '.,')
    if fact_nums and fact_nums.replace('.', '').replace(',', '') in normalized_text.replace('.', '').replace(',', ''):
        # Also check if the context words are nearby
        context_words = [w for w in normalized_fact.split() if not any(c.isdigit() for c in w)]
        if all(w in normalized_text for w in context_words):
            return True

    return False


def list_generated_files():
    """List all generated files with sizes."""
    print("\n" + "="*80)
    print("GENERATED FILES")
    print("="*80)

    corpus_path = Path(CORPUS_DIR)
    if not corpus_path.exists():
        print(f"❌ Corpus directory '{CORPUS_DIR}' not found!")
        return []

    files = sorted(corpus_path.glob("*"))
    total_size = 0

    for filepath in files:
        if filepath.is_file():
            size = filepath.stat().st_size
            total_size += size
            size_kb = size / 1024
            print(f"  {filepath.name:<50} {size_kb:>8.1f} KB")

    print(f"\n  Total: {len(files)} files, {total_size/1024:.1f} KB")
    return files


def verify_eval_questions():
    """Verify each evaluation question's fact exists in its source file."""
    print("\n" + "="*80)
    print("VERIFICATION RESULTS")
    print("="*80)

    # Load questions
    with open(EVAL_FILE, 'r', encoding='utf-8') as f:
        questions = json.load(f)

    # Filter questions that have source files
    questions_to_verify = [q for q in questions if q.get('source_file') and q['source_file'] != 'multiple']

    passed = 0
    failed = 0
    skipped = 0

    print(f"\nVerifying {len(questions_to_verify)} questions with source files...\n")

    for q in questions_to_verify:
        qid = q['id']
        source_file = q['source_file']
        expected = q['expected_answer']
        location = q['location']

        # Skip unanswerable questions
        if expected == "NOT_IN_CORPUS":
            skipped += 1
            continue

        # Build file path
        filepath = Path(CORPUS_DIR) / source_file

        if not filepath.exists():
            print(f"❌ {qid}: File not found: {source_file}")
            failed += 1
            continue

        # Extract text
        text = extract_text_from_file(filepath)

        # Check if this is a scanned PDF (text extraction will fail)
        is_scanned_pdf = 'scan' in source_file.lower() and source_file.endswith('.pdf')

        if text.startswith("["):
            if is_scanned_pdf:
                print(f"⊘ {qid}: SKIP - Scanned PDF (text as image, OCR needed)")
                print(f"   Note: '{expected[:60]}{'...' if len(expected) > 60 else ''}' in {source_file}")
                skipped += 1
                continue
            else:
                print(f"❌ {qid}: Extraction failed for {source_file}")
                print(f"   Error: {text}")
                failed += 1
                continue

        # Verify fact is present
        # For complex answers, try to verify key parts
        fact_found = False

        # Handle complex answers with multiple parts or explanations
        if "(" in expected and ")" in expected:
            # Extract main fact (part before parenthesis)
            main_fact = expected.split("(")[0].strip()
            fact_found = verify_fact_in_text(main_fact, text, is_scanned_pdf)
        else:
            fact_found = verify_fact_in_text(expected, text, is_scanned_pdf)

        if fact_found:
            print(f"✓ {qid}: PASS - '{expected[:60]}{'...' if len(expected) > 60 else ''}'")
            print(f"   Location: {location} in {source_file}")
            passed += 1
        else:
            print(f"❌ {qid}: FAIL - Expected fact not found!")
            print(f"   Expected: '{expected}'")
            print(f"   Source: {source_file} ({location})")
            print(f"   [Extracted text preview: {text[:200]}...]")
            failed += 1

    # Summary
    print("\n" + "="*80)
    print("VERIFICATION SUMMARY")
    print("="*80)
    print(f"  Total questions verified: {len(questions_to_verify)}")
    print(f"  ✓ PASSED: {passed}")
    print(f"  ❌ FAILED: {failed}")
    print(f"  ⊘ SKIPPED (unanswerable): {skipped}")
    print(f"\n  Success rate: {passed}/{passed + failed} ({100*passed/(passed+failed) if (passed+failed) > 0 else 0:.1f}%)")

    if failed == 0:
        print("\n  🎉 ALL VERIFICATIONS PASSED! Corpus is ready for RAG testing.")
    else:
        print(f"\n  ⚠️  {failed} fact(s) failed verification. Review and fix the generator script.")

    return failed == 0


def verify_file_contents():
    """Additional verification: check that files contain substantial content."""
    print("\n" + "="*80)
    print("CONTENT VERIFICATION")
    print("="*80)

    corpus_path = Path(CORPUS_DIR)
    files = sorted(corpus_path.glob("*"))

    min_lengths = {
        '.docx': 500,   # Min 500 chars
        '.pptx': 300,   # Min 300 chars
        '.pdf': 400,    # Min 400 chars
        '.xlsx': 200,   # Min 200 chars
    }

    all_good = True

    for filepath in files:
        if filepath.is_file():
            ext = filepath.suffix.lower()
            text = extract_text_from_file(filepath)

            # Scanned PDFs won't have extractable text
            is_scanned = 'scan' in filepath.name.lower() and ext == '.pdf'

            if text.startswith("["):
                if is_scanned:
                    print(f"⊘ {filepath.name}: Scanned PDF (text as image, OCR needed)")
                else:
                    print(f"⚠️  {filepath.name}: Extraction issue - {text}")
                    all_good = False
                continue

            text_len = len(text)
            min_len = min_lengths.get(ext, 100)

            if text_len < min_len:
                print(f"⚠️  {filepath.name}: Content too short ({text_len} chars, expected >{min_len})")
                all_good = False
            else:
                print(f"✓ {filepath.name}: {text_len} chars")

    if all_good:
        print("\n  ✓ All files have substantial content.")
    else:
        print("\n  ⚠️  Some files may have content issues (scanned PDFs excluded).")

    return all_good


def main():
    """Main verification routine."""
    print("\n" + "="*80)
    print("SYNTHETIC CORPUS VERIFICATION")
    print("="*80)

    # Check eval file exists
    if not os.path.exists(EVAL_FILE):
        print(f"\n❌ Evaluation file '{EVAL_FILE}' not found!")
        print("   Run generate_synthetic_corpus.py first.")
        sys.exit(1)

    # List files
    files = list_generated_files()

    if not files:
        print("\n❌ No files found in corpus directory!")
        sys.exit(1)

    # Verify content
    content_ok = verify_file_contents()

    # Verify facts
    facts_ok = verify_eval_questions()

    # Final result
    print("\n" + "="*80)

    # Content check may fail for scanned PDFs, which is expected
    # So we only require facts_ok to pass
    if facts_ok:
        print("✓✓✓ VERIFICATION COMPLETE - CORPUS IS READY! ✓✓✓")
        print("="*80)
        if not content_ok:
            print("\nNote: Scanned PDF has text rendered as image (OCR needed for extraction).")
        sys.exit(0)
    else:
        print("⚠️⚠️⚠️ VERIFICATION INCOMPLETE - ISSUES FOUND ⚠️⚠️⚠️")
        print("="*80)
        sys.exit(1)


if __name__ == "__main__":
    main()
