"""
Tests for ETL script
"""
import os
import sqlite3
import tempfile
import pytest
from pathlib import Path

from scripts.etl import (
    TagNormalizer,
    compute_content_hash,
    extract_date_from_filename,
    ETLStats
)


class TestTagNormalizer:
    """Test tag normalization functionality"""
    
    def test_normalize_with_alias(self, tmp_path):
        """Test alias resolution"""
        # Create taxonomy file
        taxonomy_content = """
approved:
  tech:
    - playwright
aliases:
  pw: tech:playwright
rules:
  allow_new_prefix: ["new", "tmp"]
"""
        taxonomy_path = tmp_path / "tags.yml"
        taxonomy_path.write_text(taxonomy_content)
        
        normalizer = TagNormalizer(str(taxonomy_path))
        
        assert normalizer.normalize("pw") == "tech:playwright"
    
    def test_normalize_approved_tag(self, tmp_path):
        """Test approved tag passes through"""
        taxonomy_content = """
approved:
  tech:
    - playwright
  topic:
    - workflow
aliases: {}
rules:
  allow_new_prefix: ["new", "tmp"]
"""
        taxonomy_path = tmp_path / "tags.yml"
        taxonomy_path.write_text(taxonomy_content)
        
        normalizer = TagNormalizer(str(taxonomy_path))
        
        assert normalizer.normalize("tech:playwright") == "tech:playwright"
        assert normalizer.normalize("topic:workflow") == "topic:workflow"
    
    def test_normalize_new_prefix(self, tmp_path):
        """Test new prefix is allowed"""
        taxonomy_content = """
approved: {}
aliases: {}
rules:
  allow_new_prefix: ["new", "tmp"]
"""
        taxonomy_path = tmp_path / "tags.yml"
        taxonomy_path.write_text(taxonomy_content)
        
        normalizer = TagNormalizer(str(taxonomy_path))
        
        assert normalizer.normalize("new:something") == "new:something"
        assert normalizer.normalize("tmp:test") == "tmp:test"
    
    def test_normalize_unknown_prefix(self, tmp_path):
        """Test unknown prefix gets prefixed with 'new:'"""
        taxonomy_content = """
approved: {}
aliases: {}
rules:
  allow_new_prefix: ["new", "tmp"]
"""
        taxonomy_path = tmp_path / "tags.yml"
        taxonomy_path.write_text(taxonomy_content)
        
        normalizer = TagNormalizer(str(taxonomy_path))
        
        assert normalizer.normalize("unknown:tag") == "new:unknown:tag"
    
    def test_normalize_no_colon(self, tmp_path):
        """Test tag without colon gets prefixed with 'new:'"""
        taxonomy_content = """
approved: {}
aliases: {}
rules:
  allow_new_prefix: ["new", "tmp"]
"""
        taxonomy_path = tmp_path / "tags.yml"
        taxonomy_path.write_text(taxonomy_content)
        
        normalizer = TagNormalizer(str(taxonomy_path))
        
        assert normalizer.normalize("notag") == "new:notag"


class TestContentHash:
    """Test content hash computation"""
    
    def test_same_content_same_hash(self):
        """Test that same content produces same hash"""
        data1 = {
            'type': 'learning',
            'body': 'Test content',
            'tags': ['topic:test', 'tech:python'],
            'effort_min': None,
            'status': None
        }
        
        data2 = {
            'type': 'learning',
            'body': 'Test content',
            'tags': ['tech:python', 'topic:test'],  # Different order
            'effort_min': None,
            'status': None
        }
        
        hash1 = compute_content_hash(data1)
        hash2 = compute_content_hash(data2)
        
        assert hash1 == hash2
    
    def test_different_content_different_hash(self):
        """Test that different content produces different hash"""
        data1 = {
            'type': 'learning',
            'body': 'Test content',
            'tags': ['topic:test'],
            'effort_min': None,
            'status': None
        }
        
        data2 = {
            'type': 'learning',
            'body': 'Different content',
            'tags': ['topic:test'],
            'effort_min': None,
            'status': None
        }
        
        hash1 = compute_content_hash(data1)
        hash2 = compute_content_hash(data2)
        
        assert hash1 != hash2


class TestExtractDateFromFilename:
    """Test date extraction from filename"""
    
    def test_valid_filename(self):
        """Test valid filename format"""
        assert extract_date_from_filename("2025-12-13.md") == "2025-12-13"
        assert extract_date_from_filename("2024-01-01.md") == "2024-01-01"
    
    def test_invalid_filename(self):
        """Test invalid filename formats"""
        assert extract_date_from_filename("20251213.md") is None
        assert extract_date_from_filename("2025-12-13.txt") is None
        assert extract_date_from_filename("random.md") is None
        assert extract_date_from_filename("2025-12-13") is None


class TestETLStats:
    """Test ETL statistics tracking"""
    
    def test_add_error(self):
        """Test error tracking"""
        stats = ETLStats()
        
        stats.add_error("file.md", "line content", "error reason")
        
        assert stats.lines_failed == 1
        assert len(stats.errors) == 1
        assert stats.errors[0]['file'] == "file.md"
        assert stats.errors[0]['line'] == "line content"
        assert stats.errors[0]['reason'] == "error reason"
    
    def test_summary(self):
        """Test summary generation"""
        stats = ETLStats()
        stats.files_scanned = 5
        stats.items_inserted = 10
        stats.items_updated = 3
        stats.items_unchanged = 7
        stats.lines_failed = 2
        
        summary = stats.summary()
        
        assert "Files scanned: 5" in summary
        assert "Items inserted: 10" in summary
        assert "Items updated: 3" in summary
        assert "Items unchanged: 7" in summary
        assert "Lines failed: 2" in summary
