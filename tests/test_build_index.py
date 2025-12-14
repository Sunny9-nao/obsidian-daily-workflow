"""
Tests for build_index script
"""
import os
import sqlite3
import tempfile
import pytest
from pathlib import Path

from scripts.build_index import (
    atomic_write,
    build_ideas_index,
    build_actions_index,
    get_book_list,
    build_book_index
)


@pytest.fixture
def test_db(tmp_path):
    """Create a test database with sample data"""
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute("""
        CREATE TABLE items (
            id INTEGER PRIMARY KEY,
            date TEXT NOT NULL,
            type TEXT NOT NULL,
            text TEXT NOT NULL,
            ref_source_path TEXT,
            ref_block_id TEXT,
            source_path TEXT NOT NULL,
            block_id TEXT NOT NULL,
            effort_min INTEGER,
            status TEXT,
            content_hash TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    
    cursor.execute("""
        CREATE TABLE tags (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE
        )
    """)
    
    cursor.execute("""
        CREATE TABLE item_tags (
            item_id INTEGER NOT NULL,
            tag_id INTEGER NOT NULL,
            PRIMARY KEY (item_id, tag_id)
        )
    """)
    
    # Insert sample data
    cursor.execute("INSERT INTO tags (name) VALUES (?)", ("topic:test",))
    cursor.execute("INSERT INTO tags (name) VALUES (?)", ("book:TestBook",))
    
    cursor.execute("""
        INSERT INTO items (date, type, text, source_path, block_id, content_hash, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, ("2025-12-13", "idea", "Test idea", "daily/2025-12-13.md", "^20251213-i1", "hash1", "2025-12-13", "2025-12-13"))
    
    cursor.execute("""
        INSERT INTO items (date, type, text, source_path, block_id, effort_min, status, content_hash, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, ("2025-12-14", "action", "Test action", "daily/2025-12-14.md", "^20251214-a1", 30, "inbox", "hash2", "2025-12-14", "2025-12-14"))
    
    cursor.execute("""
        INSERT INTO items (date, type, text, source_path, block_id, content_hash, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, ("2025-12-15", "learning", "Test learning", "daily/2025-12-15.md", "^20251215-l1", "hash3", "2025-12-15", "2025-12-15"))
    
    # Link tags to items
    cursor.execute("INSERT INTO item_tags (item_id, tag_id) VALUES (1, 1)")  # idea -> topic:test
    cursor.execute("INSERT INTO item_tags (item_id, tag_id) VALUES (2, 1)")  # action -> topic:test
    cursor.execute("INSERT INTO item_tags (item_id, tag_id) VALUES (3, 2)")  # learning -> book:TestBook
    
    conn.commit()
    
    yield conn
    
    conn.close()


class TestAtomicWrite:
    """Test atomic file writing"""
    
    def test_atomic_write_success(self, tmp_path):
        """Test successful atomic write"""
        file_path = tmp_path / "test.md"
        content = "Test content"
        
        atomic_write(str(file_path), content)
        
        assert file_path.exists()
        assert file_path.read_text() == content
    
    def test_atomic_write_creates_directory(self, tmp_path):
        """Test that atomic write creates parent directories"""
        file_path = tmp_path / "subdir" / "test.md"
        content = "Test content"
        
        atomic_write(str(file_path), content)
        
        assert file_path.exists()
        assert file_path.read_text() == content


class TestBuildIdeasIndex:
    """Test ideas index generation"""
    
    def test_build_ideas_index(self, test_db):
        """Test ideas.md generation"""
        content = build_ideas_index(test_db)
        
        assert "# Ideas Index" in content
        assert "Total: 1 ideas" in content
        assert "2025-12-13" in content
        assert "^20251213-i1" in content
        assert "#topic:test" in content


class TestBuildActionsIndex:
    """Test actions index generation"""
    
    def test_build_actions_index(self, test_db):
        """Test actions.md generation"""
        content = build_actions_index(test_db)
        
        assert "# Actions Index" in content
        assert "Total: 1 active actions" in content
        assert "2025-12-14" in content
        assert "^20251214-a1" in content
        assert "[inbox|30m]" in content
        assert "#topic:test" in content


class TestBuildBookIndex:
    """Test book index generation"""
    
    def test_get_book_list(self, test_db):
        """Test getting list of books"""
        books = get_book_list(test_db)
        
        assert len(books) == 1
        assert "TestBook" in books
    
    def test_build_book_index(self, test_db):
        """Test book index generation"""
        content = build_book_index(test_db, "TestBook")
        
        assert "# Book: TestBook" in content
        assert "Total: 1 items" in content
        assert "2025-12-15" in content
        assert "^20251215-l1" in content
        assert "[learning]" in content
