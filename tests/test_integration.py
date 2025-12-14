"""
Integration tests for the complete workflow
"""
import os
import sqlite3
import tempfile
import pytest
from pathlib import Path
import subprocess
import sys


@pytest.fixture
def test_vault(tmp_path):
    """Create a test vault with full structure"""
    vault = tmp_path / "vault"
    vault.mkdir()
    
    # Create directory structure
    (vault / "00.daily").mkdir()
    (vault / "99.system" / "db").mkdir(parents=True)
    (vault / "99.system" / "taxonomy").mkdir(parents=True)
    (vault / "01.index").mkdir()
    (vault / "02.blog" / "drafts").mkdir(parents=True)
    (vault / "99.system" / "logs").mkdir()
    
    # Create taxonomy file
    taxonomy = vault / "99.system" / "taxonomy" / "tags.yml"
    taxonomy.write_text("""
approved:
  book:
    - "TestBook"
  tech:
    - "python"
  topic:
    - "test"
    - "workflow"
rules:
  allow_new_prefix: ["new", "tmp"]
aliases:
  py: "tech:python"
""")
    
    # Initialize database
    init_sql_path = Path(__file__).parent.parent / "init_db.sql"
    db_path = vault / "99.system" / "db" / "notes.sqlite"
    
    subprocess.run(
        ["sqlite3", str(db_path)],
        stdin=open(init_sql_path),
        check=True,
        capture_output=True
    )
    
    # Create sample daily files
    daily1 = vault / "00.daily" / "2025-12-13.md"
    daily1.write_text("""---
date: 2025-12-13
tags: []
---

## Summary

Test daily note 1

## Key Takeaways (indexed)

- Learning Python basics ^20251213-t1
- Understanding workflows ^20251213-t2

## INDEX

- [learning] ![[00.daily/2025-12-13.md#^20251213-t1]] #tech:python #topic:test ^20251213-l1
- [idea] Automate daily workflow #topic:workflow ^20251213-i1
- [action] Review Python docs effort=30 status=inbox #tech:python ^20251213-a1
""")
    
    daily2 = vault / "00.daily" / "2025-12-14.md"
    daily2.write_text("""---
date: 2025-12-14
tags: []
---

## Summary

Test daily note 2

## Key Takeaways (indexed)

- Chapter 1 insights ^20251214-t1

## INDEX

- [learning] ![[daily/2025-12-14.md#^20251214-t1]] #book:TestBook #topic:test ^20251214-l1
- [action] Read chapter 2 effort=60 status=inbox #book:TestBook ^20251214-a1
""")
    
    return vault


class TestFullWorkflow:
    """Test the complete workflow from daily notes to indexes"""
    
    def test_etl_and_build_index(self, test_vault):
        """Test ETL and index building"""
        # Get Python path
        python_path = sys.executable
        
        # Run ETL
        etl_result = subprocess.run(
            [python_path, "-m", "scripts.etl", "--vault", str(test_vault), "--full"],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent)
        )
        
        assert etl_result.returncode == 0, f"ETL failed: {etl_result.stderr}"
        assert "Files scanned: 2" in etl_result.stdout
        
        # Verify database content
        db_path = test_vault / "99.system" / "db" / "notes.sqlite"
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM items")
        item_count = cursor.fetchone()[0]
        assert item_count == 5, f"Expected 5 items, got {item_count}"
        
        cursor.execute("SELECT COUNT(*) FROM tags")
        tag_count = cursor.fetchone()[0]
        assert tag_count > 0, "No tags found"
        
        conn.close()
        
        # Run build_index
        build_result = subprocess.run(
            [python_path, "-m", "scripts.build_index", "--vault", str(test_vault)],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent)
        )
        
        assert build_result.returncode == 0, f"Build index failed: {build_result.stderr}"
        
        # Verify index files created
        assert (test_vault / "01.index" / "ideas.md").exists()
        assert (test_vault / "01.index" / "actions.md").exists()
        assert (test_vault / "01.index" / "books" / "TestBook.md").exists()
        
        # Verify ideas.md content
        ideas_content = (test_vault / "01.index" / "ideas.md").read_text()
        assert "# Ideas Index" in ideas_content
        assert "2025-12-13" in ideas_content
        assert "^20251213-i1" in ideas_content
        
        # Verify actions.md content
        actions_content = (test_vault / "01.index" / "actions.md").read_text()
        assert "# Actions Index" in actions_content
        assert "inbox" in actions_content
        assert "30m" in actions_content or "60m" in actions_content
        
        # Verify book index
        book_content = (test_vault / "01.index" / "books" / "TestBook.md").read_text()
        assert "# Book: TestBook" in book_content
        assert "2025-12-14" in book_content
    
    def test_validate_daily(self, test_vault):
        """Test daily validation"""
        python_path = sys.executable
        
        result = subprocess.run(
            [python_path, "-m", "scripts.validate_daily", "--vault", str(test_vault)],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent)
        )
        
        assert result.returncode == 0, f"Validation failed: {result.stderr}"
        assert "Files valid: 2" in result.stdout
    
    def test_export_pack(self, test_vault):
        """Test export pack generation"""
        python_path = sys.executable
        
        # First run ETL to populate database
        subprocess.run(
            [python_path, "-m", "scripts.etl", "--vault", str(test_vault), "--full"],
            capture_output=True,
            cwd=str(Path(__file__).parent.parent)
        )
        
        # Generate export pack
        result = subprocess.run(
            [python_path, "-m", "scripts.export_pack", 
             "--vault", str(test_vault),
             "--tag", "book:TestBook",
             "--type", "learning"],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent)
        )
        
        assert result.returncode == 0, f"Export pack failed: {result.stderr}"
        
        # Verify export file created
        exports = list((test_vault / "02.blog" / "drafts").glob("*.md"))
        assert len(exports) == 1, f"Expected 1 export file, got {len(exports)}"
        
        # Verify export content
        export_content = exports[0].read_text()
        assert "book:TestBook" in export_content
        assert "2025-12-14" in export_content
        assert "^20251214-l1" in export_content
