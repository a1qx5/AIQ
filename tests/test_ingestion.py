#!/usr/bin/env python3
"""
Comprehensive tests for incremental ingestion evidence gaps A-F.

All tests use FAKE dummy data only. Destructive tests use --source scratch
and clean up afterwards.
"""

import os
import sys
import subprocess
import shutil
import time
from pathlib import Path
import psycopg
from dotenv import load_dotenv

from aiq.config import DATA_DIR, MD_DIR

# Scratch copy of the Markdown folder used by the destructive tests.
# Run this file from the project root: python -m tests.test_ingestion
SCRATCH = str(DATA_DIR / 'dummy_v2_md_scratch')


def get_db_connection():
    """Get a database connection."""
    load_dotenv()
    db_password = os.getenv("POSTGRES_PASSWORD")
    conn = psycopg.connect(
        host="127.0.0.1",
        port=5432,
        dbname="ai",
        user="ai",
        password=db_password,
        autocommit=True
    )
    return conn


def run_ingestion(model, source='sharepoint', source_dir=str(MD_DIR),
                  dry_run=False, force=False, inject_sleep=0):
    """Run the ingestion script and return the output."""
    cmd = [sys.executable, '-m', 'aiq.ingest_to_db', model]
    if source != 'sharepoint':
        cmd.extend(['--source', source])
    if source_dir != str(MD_DIR):
        cmd.extend(['--source-dir', source_dir])
    if dry_run:
        cmd.append('--dry-run')
    if force:
        cmd.append('--force')
    if inject_sleep > 0:
        cmd.extend(['--inject-sleep', str(inject_sleep)])

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )
    return result.returncode, result.stdout, result.stderr


def get_counts(conn, source):
    """Get document and chunk counts for a source."""
    doc_count = conn.execute(
        "SELECT COUNT(*) FROM documents WHERE source = %s",
        (source,)
    ).fetchone()[0]

    chunk_count = conn.execute(
        """
        SELECT COUNT(*) FROM chunks c
        JOIN documents d ON d.id = c.document_id
        WHERE d.source = %s
        """,
        (source,)
    ).fetchone()[0]

    ingestion_count = conn.execute(
        """
        SELECT COUNT(*) FROM ingestions i
        JOIN documents d ON d.id = i.document_id
        WHERE d.source = %s
        """,
        (source,)
    ).fetchone()[0]

    return doc_count, chunk_count, ingestion_count


def test_a_real_removal():
    """
    Test A: Real removal with scratch source.

    1. Create dummy_v2_md_scratch/ with copy of all files
    2. Run ingestion to populate database
    3. Delete one file
    4. Run ingestion again (no --dry-run)
    5. Show document/chunk/ingestion counts before and after
    """
    print("=" * 80)
    print("TEST A: Real Removal")
    print("=" * 80)

    # Setup: Create scratch directory
    scratch_dir = Path(SCRATCH)
    if scratch_dir.exists():
        shutil.rmtree(scratch_dir)
    shutil.copytree(MD_DIR, scratch_dir)

    try:
        conn = get_db_connection()

        # Initial ingestion
        print("\n1. Initial ingestion with all files:")
        returncode, stdout, stderr = run_ingestion('bge-m3', source='scratch', source_dir=SCRATCH)
        print(stdout)
        if returncode != 0:
            print(f"ERROR: {stderr}")
            return False

        # Get counts before deletion
        doc_before, chunk_before, ing_before = get_counts(conn, 'scratch')
        print(f"\nCounts before deletion:")
        print(f"  Documents: {doc_before}")
        print(f"  Chunks: {chunk_before}")
        print(f"  Ingestions: {ing_before}")

        # Delete one file
        file_to_delete = list(scratch_dir.glob("*.md"))[0]
        print(f"\n2. Deleting file: {file_to_delete.name}")
        file_to_delete.unlink()

        # Re-run ingestion
        print("\n3. Re-running ingestion after deletion:")
        returncode, stdout, stderr = run_ingestion('bge-m3', source='scratch', source_dir=SCRATCH)
        print(stdout)
        if returncode != 0:
            print(f"ERROR: {stderr}")
            return False

        # Get counts after deletion
        doc_after, chunk_after, ing_after = get_counts(conn, 'scratch')
        print(f"\nCounts after deletion:")
        print(f"  Documents: {doc_after}")
        print(f"  Chunks: {chunk_after}")
        print(f"  Ingestions: {ing_after}")

        print(f"\nChange:")
        print(f"  Documents: {doc_before} -> {doc_after} (delta: {doc_after - doc_before})")
        print(f"  Chunks: {chunk_before} -> {chunk_after} (delta: {chunk_after - chunk_before})")
        print(f"  Ingestions: {ing_before} -> {ing_after} (delta: {ing_after - ing_before})")

        conn.close()
        print("\n[PASS] TEST A PASSED")
        return True

    finally:
        # Cleanup
        if scratch_dir.exists():
            shutil.rmtree(scratch_dir)
        # Clean up database
        conn = get_db_connection()
        conn.execute("DELETE FROM documents WHERE source = 'scratch'")
        conn.close()


def test_b_zero_files_guard():
    """
    Test B: Zero-files guard.

    1. Create empty directory
    2. Run with empty dir, verify abort without deletion
    3. Verify counts unchanged
    4. Verify --force allows it to proceed
    """
    print("\n" + "=" * 80)
    print("TEST B: Zero-Files Guard")
    print("=" * 80)

    empty_dir = Path('empty_test_dir')
    if empty_dir.exists():
        shutil.rmtree(empty_dir)
    empty_dir.mkdir()

    try:
        conn = get_db_connection()

        # Setup: Populate database with scratch source
        scratch_dir = Path(SCRATCH)
        if scratch_dir.exists():
            shutil.rmtree(scratch_dir)
        shutil.copytree(MD_DIR, scratch_dir)

        print("\n1. Initial ingestion to populate database:")
        run_ingestion('bge-m3', source='scratch', source_dir=SCRATCH)

        doc_before, chunk_before, ing_before = get_counts(conn, 'scratch')
        print(f"\nCounts before empty-dir run:")
        print(f"  Documents: {doc_before}")
        print(f"  Chunks: {chunk_before}")
        print(f"  Ingestions: {ing_before}")

        # Cleanup scratch dir
        shutil.rmtree(scratch_dir)

        # Try with empty directory (should fail)
        print("\n2. Running with empty directory (should abort):")
        returncode, stdout, stderr = run_ingestion('bge-m3', source='scratch', source_dir='empty_test_dir')
        print(stdout)
        if stderr:
            print(f"STDERR: {stderr}")

        doc_after, chunk_after, ing_after = get_counts(conn, 'scratch')
        print(f"\nCounts after empty-dir run (should be unchanged):")
        print(f"  Documents: {doc_after}")
        print(f"  Chunks: {chunk_after}")
        print(f"  Ingestions: {ing_after}")

        if returncode != 1:
            print(f"[FAIL] TEST B FAILED: Expected exit code 1, got {returncode}")
            return False

        if doc_after != doc_before or chunk_after != chunk_before:
            print(f"[FAIL] TEST B FAILED: Counts changed when they shouldn't have")
            return False

        # Now try with --force (should succeed)
        print("\n3. Running with empty directory + --force (should succeed):")
        returncode, stdout, stderr = run_ingestion('bge-m3', source='scratch',
                                                   source_dir='empty_test_dir', force=True)
        print(stdout)
        if stderr:
            print(f"STDERR: {stderr}")

        doc_final, chunk_final, ing_final = get_counts(conn, 'scratch')
        print(f"\nCounts after --force run:")
        print(f"  Documents: {doc_final}")
        print(f"  Chunks: {chunk_final}")
        print(f"  Ingestions: {ing_final}")

        if returncode != 0:
            print(f"[FAIL] TEST B FAILED: --force run failed with code {returncode}")
            return False

        if doc_final != 0 or chunk_final != 0:
            print(f"[FAIL] TEST B FAILED: --force didn't delete all documents")
            return False

        conn.close()
        print("\n[PASS] TEST B PASSED")
        return True

    finally:
        # Cleanup
        if empty_dir.exists():
            shutil.rmtree(empty_dir)
        conn = get_db_connection()
        conn.execute("DELETE FROM documents WHERE source = 'scratch'")
        conn.close()


def test_c_fingerprint_reaction():
    """
    Test C: Fingerprint reaction.

    1. Monkeypatch chunking.MAX_CHARS
    2. Run dry-run, verify files show UPDATED
    3. Restore value, verify UNCHANGED
    """
    print("\n" + "=" * 80)
    print("TEST C: Fingerprint Reaction")
    print("=" * 80)

    scratch_dir = Path(SCRATCH)
    if scratch_dir.exists():
        shutil.rmtree(scratch_dir)
    shutil.copytree(MD_DIR, scratch_dir)

    try:
        # Initial ingestion with original values
        print("\n1. Initial ingestion with original chunking parameters:")
        returncode, stdout, stderr = run_ingestion('bge-m3', source='scratch',
                                                   source_dir=SCRATCH)
        print(stdout)

        # Dry-run with original values (should show UNCHANGED)
        print("\n2. Dry-run with original parameters (should show UNCHANGED):")
        returncode, stdout, stderr = run_ingestion('bge-m3', source='scratch',
                                                   source_dir=SCRATCH, dry_run=True)
        print(stdout)

        unchanged_count = stdout.count('UNCHANGED:')
        print(f"\nUNCHANGED files with original parameters: {unchanged_count}")

        # Monkeypatch MAX_CHARS and run dry-run
        print("\n3. Monkeypatching chunking.MAX_CHARS and running dry-run:")
        print("   Original MAX_CHARS: 1500")
        print("   Patched MAX_CHARS: 2000")

        # We need to run with modified chunking module
        test_script = Path('test_c_helper.py')
        test_script.write_text("""
import sys
from unittest.mock import patch
from aiq.config import DATA_DIR
from aiq import chunking

# Monkeypatch MAX_CHARS
with patch.object(chunking, 'MAX_CHARS', 2000):
    # Now run the ingestion
    from aiq.ingest_to_db import main
    sys.argv = ['ingest_to_db.py', 'bge-m3', '--source', 'scratch',
                '--source-dir', str(DATA_DIR / 'dummy_v2_md_scratch'), '--dry-run']
    main()
""")

        result = subprocess.run([sys.executable, 'test_c_helper.py'],
                              capture_output=True, text=True)
        print(result.stdout)
        if result.stderr and 'Warning' not in result.stderr:
            print(f"STDERR: {result.stderr}")

        updated_count = result.stdout.count('UPDATED:')
        print(f"\nUPDATED files with modified parameters: {updated_count}")

        test_script.unlink()

        # Verify dry-run again with original values shows UNCHANGED
        print("\n4. Final dry-run with original parameters (should show UNCHANGED again):")
        returncode, stdout, stderr = run_ingestion('bge-m3', source='scratch',
                                                   source_dir=SCRATCH, dry_run=True)
        print(stdout)

        final_unchanged_count = stdout.count('UNCHANGED:')
        print(f"\nUNCHANGED files after restoring parameters: {final_unchanged_count}")

        if updated_count == 0:
            print("\n[FAIL] TEST C FAILED: No files showed UPDATED with modified parameters")
            return False

        if final_unchanged_count != unchanged_count:
            print("\n[FAIL] TEST C FAILED: UNCHANGED count different after restoring parameters")
            return False

        print("\n[PASS] TEST C PASSED")
        return True

    finally:
        # Cleanup
        if scratch_dir.exists():
            shutil.rmtree(scratch_dir)
        if Path('test_c_helper.py').exists():
            Path('test_c_helper.py').unlink()
        conn = get_db_connection()
        conn.execute("DELETE FROM documents WHERE source = 'scratch'")
        conn.close()


def test_d_rollback_after_delete():
    """
    Test D: Rollback after delete.

    Force a failure after old chunks were deleted but before commit.
    Verify chunks are preserved and run continued with failed=1.
    """
    print("\n" + "=" * 80)
    print("TEST D: Rollback After Delete")
    print("=" * 80)

    scratch_dir = Path(SCRATCH)
    if scratch_dir.exists():
        shutil.rmtree(scratch_dir)
    shutil.copytree(MD_DIR, scratch_dir)

    try:
        conn = get_db_connection()

        # Initial ingestion
        print("\n1. Initial ingestion:")
        run_ingestion('bge-m3', source='scratch', source_dir=SCRATCH)

        # Get chunk IDs for first document before forced failure
        first_file = sorted(scratch_dir.glob("*.md"))[0]
        client = first_file.stem.split("-")[-1].lower()

        result = conn.execute(
            """
            SELECT c.id FROM chunks c
            JOIN documents d ON d.id = c.document_id
            WHERE d.source = 'scratch' AND d.client = %s AND c.embedding_model = 'BAAI/bge-m3'
            ORDER BY c.id
            """,
            (client,)
        )
        chunk_ids_before = [row[0] for row in result.fetchall()]
        print(f"\nChunk IDs for {first_file.name} before forced failure:")
        print(f"  {chunk_ids_before}")

        # Modify the first file to trigger re-ingestion
        print(f"\n2. Modifying {first_file.name} to trigger re-ingestion:")
        with open(first_file, 'a', encoding='utf-8') as f:
            f.write("\n\nModification for rollback test.")

        # Create a test script that injects a failure
        print("\n3. Running with injected failure (NULL text_hash on one chunk):")
        test_script = Path('test_d_helper.py')
        test_script.write_text(f"""
import sys
from unittest.mock import patch
from pathlib import Path
from aiq.config import DATA_DIR

# Track how many times compute_text_hash is called
call_count = {{}}

original_compute_text_hash = None

def failing_compute_text_hash(text):
    # Get the calling file name from stack
    import inspect
    frame = inspect.currentframe().f_back
    filename = Path(frame.f_code.co_filename).name

    # Count calls per run
    if filename not in call_count:
        call_count[filename] = 0
    call_count[filename] += 1

    # Fail on the 2nd chunk of the first file
    if call_count.get(filename, 0) == 2:
        return None  # This will cause NOT NULL constraint violation

    return original_compute_text_hash(text)

# Import after defining function
from aiq import ingest_to_db
original_compute_text_hash = ingest_to_db.compute_text_hash

with patch.object(ingest_to_db, 'compute_text_hash', failing_compute_text_hash):
    sys.argv = ['ingest_to_db.py', 'bge-m3', '--source', 'scratch',
                '--source-dir', str(DATA_DIR / 'dummy_v2_md_scratch')]
    ingest_to_db.main()
""")

        proc_result = subprocess.run([sys.executable, 'test_d_helper.py'],
                              capture_output=True, text=True)
        print(proc_result.stdout)
        if proc_result.stderr and 'Warning' not in proc_result.stderr and 'Loading weights' not in proc_result.stderr:
            print(f"STDERR: {proc_result.stderr}")

        # Check chunk IDs after - should be identical
        db_result = conn.execute(
            """
            SELECT c.id FROM chunks c
            JOIN documents d ON d.id = c.document_id
            WHERE d.source = 'scratch' AND d.client = %s AND c.embedding_model = 'BAAI/bge-m3'
            ORDER BY c.id
            """,
            (client,)
        )
        chunk_ids_after = [row[0] for row in db_result.fetchall()]
        print(f"\nChunk IDs for {first_file.name} after forced failure:")
        print(f"  {chunk_ids_after}")

        # Extract summary line
        summary_line = [line for line in proc_result.stdout.split('\n') if line.startswith('Summary:')]
        if summary_line:
            print(f"\nRaw summary line:")
            print(f"  {summary_line[0]}")

        test_script.unlink()

        # Verify chunks preserved
        if chunk_ids_before != chunk_ids_after:
            print("\n[FAIL] TEST D FAILED: Chunk IDs changed (rollback failed)")
            return False

        # Verify failed=1 in summary
        if 'failed' not in proc_result.stdout.lower() or '1 failed' not in proc_result.stdout.lower():
            print("\n[FAIL] TEST D FAILED: Summary doesn't show failed=1")
            return False

        conn.close()
        print("\n[PASS] TEST D PASSED")
        return True

    finally:
        # Cleanup: Restore modified file
        original_dir = Path(MD_DIR)
        if scratch_dir.exists():
            first_file = sorted(scratch_dir.glob("*.md"))[0]
            original_file = original_dir / first_file.name
            if original_file.exists():
                # Restore original content
                shutil.copy(original_file, first_file)
            shutil.rmtree(scratch_dir)
        if Path('test_d_helper.py').exists():
            Path('test_d_helper.py').unlink()
        conn = get_db_connection()
        conn.execute("DELETE FROM documents WHERE source = 'scratch'")
        conn.close()


def test_e_concurrency():
    """
    Test E: Concurrency with advisory lock.

    Start two runs on scratch source simultaneously.
    First has inject-sleep, second should exit cleanly.
    """
    print("\n" + "=" * 80)
    print("TEST E: Concurrency")
    print("=" * 80)

    scratch_dir = Path(SCRATCH)
    if scratch_dir.exists():
        shutil.rmtree(scratch_dir)
    shutil.copytree(MD_DIR, scratch_dir)

    try:
        print("\n1. Starting first ingestion with 5-second sleep after lock acquisition:")

        # Start first process with sleep
        proc1 = subprocess.Popen(
            [sys.executable, '-m', 'aiq.ingest_to_db', 'bge-m3',
             '--source', 'scratch', '--source-dir', SCRATCH,
             '--inject-sleep', '5'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Give it time to start Python, connect and take the lock (the lock is taken
        # before the model loads, so this is fast); it then holds the lock for 5 s.
        time.sleep(2)

        print("\n2. Starting second ingestion (should be blocked and exit):")

        # Start second process
        proc2 = subprocess.Popen(
            [sys.executable, '-m', 'aiq.ingest_to_db', 'bge-m3',
             '--source', 'scratch', '--source-dir', SCRATCH],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Wait for second process (might take time to load embedder before checking lock)
        stdout2, stderr2 = proc2.communicate(timeout=30)
        print("\nSecond process output:")
        print(stdout2)
        if stderr2 and 'Warning' not in stderr2:
            print(f"STDERR: {stderr2}")

        print(f"Second process exit code: {proc2.returncode}")

        # Wait for first process
        print("\n3. Waiting for first ingestion to complete:")
        stdout1, stderr1 = proc1.communicate(timeout=300)   # model load + embedding on CPU is slow
        print("\nFirst process output:")
        print(stdout1)

        print(f"First process exit code: {proc1.returncode}")

        # Verify second process exited with error and correct message
        if proc2.returncode != 1:
            print(f"\n[FAIL] TEST E FAILED: Second process should exit with code 1, got {proc2.returncode}")
            return False

        if 'another ingestion for scratch/bge-m3 is running' not in stdout2:
            print(f"\n[FAIL] TEST E FAILED: Second process didn't show expected lock message")
            return False

        # Verify first process completed successfully
        if proc1.returncode != 0:
            print(f"\n[FAIL] TEST E FAILED: First process failed with code {proc1.returncode}")
            return False

        print("\n[PASS] TEST E PASSED")
        return True

    finally:
        # Cleanup
        if scratch_dir.exists():
            shutil.rmtree(scratch_dir)
        conn = get_db_connection()
        conn.execute("DELETE FROM documents WHERE source = 'scratch'")
        conn.close()


def test_f_real_rows_dry_run():
    """
    Test F: Real rows dry-run for sharepoint source.

    Run with default source and show per-file status and summary.
    Do NOT run for real.
    """
    print("\n" + "=" * 80)
    print("TEST F: Real Rows Dry-Run (sharepoint source)")
    print("=" * 80)

    print("\nRunning: python -m aiq.ingest_to_db bge-m3 --dry-run")
    print()

    returncode, stdout, stderr = run_ingestion('bge-m3', dry_run=True)
    print(stdout)
    if stderr and 'Warning' not in stderr:
        print(f"STDERR: {stderr}")

    if returncode != 0:
        print(f"\n[FAIL] TEST F FAILED: Exit code {returncode}")
        return False

    print("\n[PASS] TEST F PASSED")
    return True


def _seed_scratch_with_one_file():
    """Put one document (fake data) into the scratch source and ingest it."""
    scratch_dir = Path(SCRATCH)
    if scratch_dir.exists():
        shutil.rmtree(scratch_dir)
    scratch_dir.mkdir(parents=True)
    first_file = sorted(MD_DIR.glob("*.md"))[0]
    shutil.copy(first_file, scratch_dir / first_file.name)
    run_ingestion('bge-m3', source='scratch', source_dir=SCRATCH)
    return scratch_dir


def _cleanup_scratch():
    scratch_dir = Path(SCRATCH)
    if scratch_dir.exists():
        shutil.rmtree(scratch_dir)
    conn = get_db_connection()
    conn.execute("DELETE FROM documents WHERE source = 'scratch'")
    conn.close()


def test_g_missing_directory_aborts():
    """Test G: a source directory that does not exist aborts, even with --force."""
    print("\n" + "=" * 80)
    print("TEST G: Missing Source Directory")
    print("=" * 80)
    try:
        conn = get_db_connection()
        _seed_scratch_with_one_file()
        docs_before, chunks_before, _ = get_counts(conn, 'scratch')

        for force in (False, True):
            returncode, stdout, stderr = run_ingestion(
                'bge-m3', source='scratch', source_dir='no_such_directory_xyz', force=force)
            print(f"force={force}: exit {returncode}, output: {stdout.strip()}")
            if returncode != 1 or 'does not exist' not in stdout:
                print(f"[FAIL] TEST G FAILED (force={force})")
                return False

        docs_after, chunks_after, _ = get_counts(conn, 'scratch')
        print(f"Documents {docs_before} -> {docs_after}, chunks {chunks_before} -> {chunks_after}")
        if (docs_before, chunks_before) != (docs_after, chunks_after) or docs_before == 0:
            print("[FAIL] TEST G FAILED: rows changed or nothing was seeded")
            return False
        conn.close()
        print("\n[PASS] TEST G PASSED")
        return True
    finally:
        _cleanup_scratch()


def test_h_empty_directory_without_force_aborts():
    """Test H: an empty directory aborts with the documented message and deletes nothing."""
    print("\n" + "=" * 80)
    print("TEST H: Empty Source Directory, no --force")
    print("=" * 80)
    empty_dir = Path('empty_test_dir_h')
    try:
        conn = get_db_connection()
        _seed_scratch_with_one_file()
        docs_before, chunks_before, ings_before = get_counts(conn, 'scratch')

        if empty_dir.exists():
            shutil.rmtree(empty_dir)
        empty_dir.mkdir()
        returncode, stdout, stderr = run_ingestion(
            'bge-m3', source='scratch', source_dir=str(empty_dir))
        print(f"exit {returncode}, output: {stdout.strip()}")

        docs_after, chunks_after, ings_after = get_counts(conn, 'scratch')
        print(f"Documents {docs_before} -> {docs_after}, chunks {chunks_before} -> {chunks_after}, "
              f"ingestions {ings_before} -> {ings_after}")

        if returncode != 1:
            print(f"[FAIL] TEST H FAILED: expected exit 1, got {returncode}")
            return False
        if "source directory is empty: nothing would remain for scratch" not in stdout:
            print("[FAIL] TEST H FAILED: message missing")
            return False
        if (docs_before, chunks_before, ings_before) != (docs_after, chunks_after, ings_after) \
                or docs_before == 0:
            print("[FAIL] TEST H FAILED: rows changed or nothing was seeded")
            return False
        conn.close()
        print("\n[PASS] TEST H PASSED")
        return True
    finally:
        if empty_dir.exists():
            shutil.rmtree(empty_dir)
        _cleanup_scratch()


def test_i_empty_directory_with_force_removes_scratch():
    """Test I: an empty directory with --force goes through and removes the scratch documents."""
    print("\n" + "=" * 80)
    print("TEST I: Empty Source Directory, with --force (scratch only)")
    print("=" * 80)
    empty_dir = Path('empty_test_dir_i')
    try:
        conn = get_db_connection()
        _seed_scratch_with_one_file()
        docs_before, chunks_before, _ = get_counts(conn, 'scratch')

        if empty_dir.exists():
            shutil.rmtree(empty_dir)
        empty_dir.mkdir()
        returncode, stdout, stderr = run_ingestion(
            'bge-m3', source='scratch', source_dir=str(empty_dir), force=True)
        print(f"exit {returncode}, output: {stdout.strip()}")

        docs_after, chunks_after, ings_after = get_counts(conn, 'scratch')
        print(f"Documents {docs_before} -> {docs_after}, chunks {chunks_before} -> {chunks_after}")

        if returncode != 0 or docs_before == 0 or (docs_after, chunks_after, ings_after) != (0, 0, 0):
            print("[FAIL] TEST I FAILED")
            return False
        conn.close()
        print("\n[PASS] TEST I PASSED")
        return True
    finally:
        if empty_dir.exists():
            shutil.rmtree(empty_dir)
        _cleanup_scratch()


def test_j_fingerprint_includes_model_id():
    """Test J: changing VOYAGE_MODEL (monkeypatched, file untouched) changes the fingerprint."""
    print("\n" + "=" * 80)
    print("TEST J: Fingerprint includes the embedding model id")
    print("=" * 80)
    from unittest.mock import patch
    from aiq import embedders
    from aiq.ingest_to_db import compute_pipeline_fingerprint

    before = compute_pipeline_fingerprint(embedders.model_id('voyage'))
    bge = compute_pipeline_fingerprint(embedders.model_id('bge-m3'))
    with patch.object(embedders, 'VOYAGE_MODEL', 'voyage-other-model-for-test'):
        patched_id = embedders.model_id('voyage')
        patched = compute_pipeline_fingerprint(patched_id)
    after = compute_pipeline_fingerprint(embedders.model_id('voyage'))

    print(f"voyage id: {embedders.model_id('voyage')}   bge-m3 id: {embedders.model_id('bge-m3')}")
    print(f"patched id: {patched_id}")
    print(f"fingerprint voyage           : {before}")
    print(f"fingerprint voyage (patched) : {patched}")
    print(f"fingerprint bge-m3           : {bge}")
    print(f"fingerprint voyage (restored): {after}")

    if patched == before or bge == before or after != before:
        print("[FAIL] TEST J FAILED")
        return False
    print("\n[PASS] TEST J PASSED")
    return True


def main():
    """Run all tests and generate final report."""
    print("\n" + "=" * 80)
    print("INCREMENTAL INGESTION EVIDENCE TESTS")
    print("=" * 80)

    results = {}

    results['A'] = test_a_real_removal()
    results['B'] = test_b_zero_files_guard()
    results['C'] = test_c_fingerprint_reaction()
    results['D'] = test_d_rollback_after_delete()
    results['E'] = test_e_concurrency()
    results['F'] = test_f_real_rows_dry_run()
    results['G'] = test_g_missing_directory_aborts()
    results['H'] = test_h_empty_directory_without_force_aborts()
    results['I'] = test_i_empty_directory_with_force_removes_scratch()
    results['J'] = test_j_fingerprint_includes_model_id()

    # Final report
    print("\n" + "=" * 80)
    print("FINAL REPORT")
    print("=" * 80)

    print("\n| Test | Result | Description |")
    print("|------|--------|-------------|")
    print(f"| A    | {'PASS' if results['A'] else 'FAIL'} | Real removal with scratch source |")
    print(f"| B    | {'PASS' if results['B'] else 'FAIL'} | Zero-files guard with --force override |")
    print(f"| C    | {'PASS' if results['C'] else 'FAIL'} | Fingerprint reaction to chunking changes |")
    print(f"| D    | {'PASS' if results['D'] else 'FAIL'} | Rollback after delete preserves chunks |")
    print(f"| E    | {'PASS' if results['E'] else 'FAIL'} | Concurrency control with advisory lock |")
    print(f"| F    | {'PASS' if results['F'] else 'FAIL'} | Real rows dry-run (sharepoint) |")
    print(f"| G    | {'PASS' if results['G'] else 'FAIL'} | Missing source directory aborts |")
    print(f"| H    | {'PASS' if results['H'] else 'FAIL'} | Empty directory aborts without --force |")
    print(f"| I    | {'PASS' if results['I'] else 'FAIL'} | Empty directory with --force (scratch) |")
    print(f"| J    | {'PASS' if results['J'] else 'FAIL'} | Fingerprint includes model id |")

    all_passed = all(results.values())
    print(f"\nOverall: {'ALL TESTS PASSED [PASS]' if all_passed else 'SOME TESTS FAILED [FAIL]'}")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
