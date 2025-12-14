"""
Tests for validate_daily script
"""
import os
import pytest
from pathlib import Path

from scripts.validate_daily import (
    extract_date_from_filename,
    validate_block_id_date,
    validate_tag_format,
    validate_daily_file,
    ValidationError
)


class TestExtractDateFromFilename:
    """Test date extraction"""
    
    def test_valid_filename(self):
        """Test valid filename format"""
        assert extract_date_from_filename("2025-12-13.md") == "2025-12-13"
    
    def test_invalid_filename(self):
        """Test invalid filename format"""
        assert extract_date_from_filename("invalid.md") is None
        assert extract_date_from_filename("2025-12-13.txt") is None


class TestValidateBlockIdDate:
    """Test block ID date validation"""
    
    def test_valid_block_id(self):
        """Test block ID with matching date"""
        assert validate_block_id_date("^20251213-i1", "2025-12-13") is True
    
    def test_invalid_block_id_date(self):
        """Test block ID with mismatched date"""
        assert validate_block_id_date("^20251214-i1", "2025-12-13") is False
    
    def test_invalid_block_id_format(self):
        """Test invalid block ID format"""
        assert validate_block_id_date("^invalid", "2025-12-13") is False


class TestValidateTagFormat:
    """Test tag format validation"""
    
    def test_valid_tag(self):
        """Test valid tag format"""
        assert validate_tag_format("topic:test") is True
        assert validate_tag_format("book:SomeBook") is True
        assert validate_tag_format("tech:python") is True
    
    def test_invalid_tag(self):
        """Test invalid tag format"""
        assert validate_tag_format("notag") is False
        assert validate_tag_format("has space") is False


class TestValidateDailyFile:
    """Test daily file validation"""
    
    def test_valid_file(self, tmp_path):
        """Test validation of valid daily file"""
        file_path = tmp_path / "2025-12-13.md"
        content = """---
date: 2025-12-13
---

## Summary

Test summary

## INDEX

- [idea] Test idea #topic:test ^20251213-i1
"""
        file_path.write_text(content)
        
        errors = validate_daily_file(str(file_path))
        
        assert len(errors) == 0
    
    def test_missing_index(self, tmp_path):
        """Test file without INDEX section"""
        file_path = tmp_path / "2025-12-13.md"
        content = """---
date: 2025-12-13
---

## Summary

Test summary
"""
        file_path.write_text(content)
        
        errors = validate_daily_file(str(file_path))
        
        assert len(errors) > 0
        assert any(e.error_type == "INDEX_MISSING" for e in errors)
    
    def test_block_id_date_mismatch(self, tmp_path):
        """Test block ID date doesn't match filename"""
        file_path = tmp_path / "2025-12-13.md"
        content = """---
date: 2025-12-13
---

## INDEX

- [idea] Test idea #topic:test ^20251214-i1
"""
        file_path.write_text(content)
        
        errors = validate_daily_file(str(file_path))
        
        assert len(errors) > 0
        assert any(e.error_type == "BLOCK_ID_DATE" for e in errors)
    
    def test_action_missing_meta(self, tmp_path):
        """Test action without metadata"""
        file_path = tmp_path / "2025-12-13.md"
        content = """---
date: 2025-12-13
---

## INDEX

- [action] Do something #topic:test ^20251213-a1
"""
        file_path.write_text(content)
        
        errors = validate_daily_file(str(file_path))
        
        assert len(errors) > 0
        assert any(e.error_type == "PARSE_ERROR" for e in errors)
