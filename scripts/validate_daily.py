"""
Validate Daily: Check daily notes for format compliance

This script:
1. Scans daily/*.md files
2. Validates INDEX section and format compliance
3. Reports violations for easy fixing
"""
import argparse
import logging
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple


# Add parent directory to path to import index_parser
sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.index_parser import extract_index_section, parse_index_line, IndexParseError


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ValidationError:
    """Represents a validation error"""
    
    def __init__(self, file_path: str, error_type: str, message: str, line: str = None):
        self.file_path = file_path
        self.error_type = error_type
        self.message = message
        self.line = line
    
    def __str__(self):
        result = f"{self.file_path}: [{self.error_type}] {self.message}"
        if self.line:
            result += f"\n  Line: {self.line}"
        return result


class ValidationStats:
    """Track validation statistics"""
    
    def __init__(self):
        self.files_scanned = 0
        self.files_valid = 0
        self.files_invalid = 0
        self.errors: List[ValidationError] = []
    
    def add_error(self, error: ValidationError):
        """Add validation error"""
        self.errors.append(error)
    
    def summary(self) -> str:
        """Return formatted summary"""
        return (
            f"\n=== Validation Summary ===\n"
            f"Files scanned: {self.files_scanned}\n"
            f"Files valid: {self.files_valid}\n"
            f"Files invalid: {self.files_invalid}\n"
            f"Total errors: {len(self.errors)}\n"
        )


def extract_date_from_filename(filename: str) -> str:
    """
    Extract date from daily filename (YYYY-MM-DD.md)
    
    Args:
        filename: Filename string
        
    Returns:
        Date string (YYYY-MM-DD) or None
    """
    match = re.match(r'(\d{4}-\d{2}-\d{2})\.md$', filename)
    if match:
        return match.group(1)
    return None


def validate_block_id_date(block_id: str, expected_date: str) -> bool:
    """
    Validate that block_id date matches file date
    
    Args:
        block_id: Block ID (e.g., ^20251213-t1)
        expected_date: Expected date (YYYY-MM-DD)
        
    Returns:
        True if valid, False otherwise
    """
    # Extract date from block_id (^YYYYMMDD-...)
    match = re.match(r'\^(\d{8})-', block_id)
    if not match:
        return False
    
    block_date = match.group(1)  # YYYYMMDD
    expected_date_compact = expected_date.replace('-', '')  # YYYY-MM-DD -> YYYYMMDD
    
    return block_date == expected_date_compact


def validate_tag_format(tag: str) -> bool:
    """
    Validate tag format (should be #prefix:value)
    
    Args:
        tag: Tag string
        
    Returns:
        True if valid, False otherwise
    """
    # Should match #prefix:value pattern
    return re.match(r'^[a-zA-Z0-9_]+:[^\s#]+$', tag) is not None


def validate_daily_file(file_path: str) -> List[ValidationError]:
    """
    Validate a single daily file
    
    Args:
        file_path: Path to daily file
        
    Returns:
        List of validation errors (empty if valid)
    """
    errors = []
    filename = os.path.basename(file_path)
    
    # Extract expected date from filename
    expected_date = extract_date_from_filename(filename)
    if not expected_date:
        errors.append(ValidationError(
            file_path,
            "FILENAME_FORMAT",
            f"Filename should be YYYY-MM-DD.md format: {filename}"
        ))
        return errors  # Can't validate further without proper date
    
    # Read file
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        errors.append(ValidationError(
            file_path,
            "FILE_READ",
            f"Failed to read file: {e}"
        ))
        return errors
    
    # Check for INDEX section
    try:
        index_lines = extract_index_section(content)
    except IndexParseError as e:
        errors.append(ValidationError(
            file_path,
            "INDEX_MISSING",
            str(e)
        ))
        return errors  # Can't validate INDEX lines without section
    
    # Validate each INDEX line
    for line in index_lines:
        line_errors = []
        
        # Try to parse line
        try:
            parsed = parse_index_line(line)
            
            # Validate block_id date matches file date
            if not validate_block_id_date(parsed['block_id'], expected_date):
                line_errors.append(ValidationError(
                    file_path,
                    "BLOCK_ID_DATE",
                    f"Block ID date doesn't match file date (expected {expected_date})",
                    line
                ))
            
            # Validate tag formats
            for tag in parsed['tags']:
                if not validate_tag_format(tag):
                    line_errors.append(ValidationError(
                        file_path,
                        "TAG_FORMAT",
                        f"Invalid tag format (should be prefix:value): #{tag}",
                        line
                    ))
            
            # Validate action metadata
            if parsed['type'] == 'action':
                if parsed['effort_min'] is None:
                    line_errors.append(ValidationError(
                        file_path,
                        "ACTION_EFFORT",
                        "Action missing effort= metadata",
                        line
                    ))
                if parsed['status'] is None:
                    line_errors.append(ValidationError(
                        file_path,
                        "ACTION_STATUS",
                        "Action missing status= metadata",
                        line
                    ))
        
        except IndexParseError as e:
            line_errors.append(ValidationError(
                file_path,
                "PARSE_ERROR",
                str(e),
                line
            ))
        
        errors.extend(line_errors)
    
    return errors


def get_daily_files(vault_path: str, since_days: int = None) -> List[str]:
    """
    Get list of daily files to validate
    
    Args:
        vault_path: Path to vault root
        since_days: If specified, only validate files from last N days
        
    Returns:
        List of file paths
    """
    daily_dir = os.path.join(vault_path, '00.daily')
    
    if not os.path.isdir(daily_dir):
        logger.error(f"Daily directory not found: {daily_dir}")
        return []
    
    all_files = []
    for filename in os.listdir(daily_dir):
        if filename.endswith('.md'):
            file_path = os.path.join(daily_dir, filename)
            all_files.append(file_path)
    
    # Filter by date if since_days is specified
    if since_days is not None:
        cutoff_date = (datetime.now() - timedelta(days=since_days)).strftime('%Y-%m-%d')
        filtered_files = []
        
        for file_path in all_files:
            filename = os.path.basename(file_path)
            file_date = extract_date_from_filename(filename)
            
            if file_date and file_date >= cutoff_date:
                filtered_files.append(file_path)
        
        return sorted(filtered_files)
    
    return sorted(all_files)


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(description='Validate daily notes format compliance')
    parser.add_argument('--vault', default='.', help='Path to vault root (default: current directory)')
    parser.add_argument('--since', type=int, help='Validate files from last N days')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    vault_path = os.path.abspath(args.vault)
    
    # Get files to validate
    files = get_daily_files(vault_path, args.since)
    
    if not files:
        logger.warning("No daily files found to validate")
        return 0
    
    logger.info(f"Validating {len(files)} daily files...")
    
    # Validate each file
    stats = ValidationStats()
    
    for file_path in files:
        stats.files_scanned += 1
        errors = validate_daily_file(file_path)
        
        if errors:
            stats.files_invalid += 1
            stats.errors.extend(errors)
        else:
            stats.files_valid += 1
            logger.debug(f"✓ {os.path.basename(file_path)}")
    
    # Print summary
    print(stats.summary())
    
    # Print errors
    if stats.errors:
        print("\n=== Validation Errors ===\n")
        for error in stats.errors:
            print(error)
            print()
    
    # Exit with error code if any validation errors
    return 1 if stats.files_invalid > 0 else 0


if __name__ == '__main__':
    sys.exit(main())
