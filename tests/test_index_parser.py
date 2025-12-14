""""
Tests for INDEX line parser
"""
import pytest
from scripts.index_parser import parse_index_line, IndexParseError
from tests.test_fixtures import VALID_LINES, INVALID_LINES, EXPECTED_PARSED


class TestIndexLineParser:
    """"Test INDEX line parsing functionality"""

    def test_valid_lines_parsing(self):
        """"Test that valid INDEX lines are parsed correctly"""
        for line, expected in zip(VALID_LINES, EXPECTED_PARSED):
            result = parse_index_line(line)
            assert result is not None, f"Failed to parse valid line: {line}"
            assert result["type"] == expected["type"], f"Type mismatch for: {line}"
            assert result["body"] == expected["body"], f"Body mismatch for: {line}"
            assert result["block_id"] == expected["block_id"], f"Block ID mismatch for: {line}"
            assert result["tags"] == expected["tags"], f"Tags mismatch for: {line}"
            assert result["effort_min"] == expected["effort_min"], f"Effort mismatch for: {line}"
            assert result["status"] == expected["status"], f"Status mismatch for: {line}"
            assert result["ref_source_path"] == expected["ref_source_path"], f"Ref source path mismatch for: {line}"
            assert result["ref_block_id"] == expected["ref_block_id"], f"Ref block ID mismatch for: {line}"

    def test_invalid_lines_raise_errors(self):
        """"Test that invalid INDEX lines raise appropriate errors"""
        for line in INVALID_LINES:
            with pytest.raises(IndexParseError):
                parse_index_line(line)

    def test_link_body_extraction(self):
        """"Test that LINK_BODY is correctly parsed for source_path and block_id"""
        line = "- [learning] ![[00.daily/2025-12-13.md#^20251213-t1]] #topic:test ^20251213-l1"
        result = parse_index_line(line)
        assert result["ref_source_path"] == "00.daily/2025-12-13.md"
        assert result["ref_block_id"] == "^20251213-t1"

    def test_text_body_no_refs(self):
        """"Test that TEXT_BODY does not populate ref fields"""
        line = "- [idea] Simple idea text #topic:test ^20251213-i1"
        result = parse_index_line(line)
        assert result["ref_source_path"] is None
        assert result["ref_block_id"] is None
        assert result["body"] == "Simple idea text"

    def test_action_meta_parsing(self):
        """"Test that action metadata (effort and status) is correctly parsed"""
        line = "- [action] Do something effort=45 status=done #topic:test ^20251213-a1"
        result = parse_index_line(line)
        assert result["effort_min"] == 45
        assert result["status"] == "done"

    def test_action_without_meta_raises_error(self):
        """"Test that action without metadata raises error"""
        line = "- [action] Do something #topic:test ^20251213-a1"
        with pytest.raises(IndexParseError, match="action.*effort"):
            parse_index_line(line)

    def test_multiple_tags_parsing(self):
        """"Test that multiple tags are correctly extracted"""
        line = "- [idea] Test #tag1:value1 #tag2:value2 #tag3:value3 ^20251213-i1"
        result = parse_index_line(line)
        assert len(result["tags"]) == 3
        assert "tag1:value1" in result["tags"]
        assert "tag2:value2" in result["tags"]
        assert "tag3:value3" in result["tags"]

    def test_no_tags_allowed(self):
        """"Test that lines without tags are valid"""
        line = "- [idea] No tags idea ^20251213-i1"
        result = parse_index_line(line)
        assert result["tags"] == []

    def test_block_id_format_validation(self):
        """"Test that block_id must follow ^YYYYMMDD-<kind><n> format"""
        # Valid format
        line = "- [idea] Test ^20251213-i1"
        result = parse_index_line(line)
        assert result["block_id"] == "^20251213-i1"

        # Invalid formats should raise error
        invalid_block_ids = [
            "- [idea] Test ^idea1",
            "- [idea] Test ^2025-12-13-i1",
            "- [idea] Test ^20251213i1",
        ]
        for invalid_line in invalid_block_ids:
            with pytest.raises(IndexParseError):
                parse_index_line(invalid_line)
