"""
ETL Script: Extract INDEX data from daily notes into SQLite DB

This script:
1. Scans daily/*.md files
2. Extracts INDEX sections
3. Parses each INDEX line
4. Upserts into SQLite DB with tag normalization
5. Logs errors for failed lines without stopping the process
"""
import argparse
import hashlib
import json
import logging
import os
import re
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import yaml

# Add parent directory to path to import index_parser
sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.index_parser import extract_index_section, parse_index_line, IndexParseError


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TagNormalizer:
    """Handles tag normalization using taxonomy/tags.yml"""
    
    def __init__(self, taxonomy_path: str):
        self.taxonomy_path = taxonomy_path
        self.approved: Dict[str, List[str]] = {}
        self.aliases: Dict[str, str] = {}
        self.allow_new_prefix: List[str] = []
        
        self._load_taxonomy()
    
    def _load_taxonomy(self):
        """Load taxonomy from YAML file"""
        if not os.path.exists(self.taxonomy_path):
            logger.warning(f"Taxonomy file not found: {self.taxonomy_path}")
            logger.warning("Tag normalization will treat all tags as 'new'")
            self.allow_new_prefix = ['new', 'tmp']
            return
        
        try:
            with open(self.taxonomy_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
            
            self.approved = data.get('approved', {})
            self.aliases = data.get('aliases', {})
            self.allow_new_prefix = data.get('rules', {}).get('allow_new_prefix', ['new', 'tmp'])
            
            logger.info(f"Loaded taxonomy: {len(self.aliases)} aliases, "
                       f"{sum(len(v) for v in self.approved.values())} approved tags")
        except Exception as e:
            logger.error(f"Failed to load taxonomy: {e}")
            self.allow_new_prefix = ['new', 'tmp']
    
    def normalize(self, tag: str) -> str:
        """
        Normalize a tag according to taxonomy rules
        
        Args:
            tag: Raw tag in format "prefix:value" or alias
            
        Returns:
            Normalized tag in format "prefix:value"
        """
        # Check if it's an alias
        if tag in self.aliases:
            return self.aliases[tag]
        
        # Check if it's already in prefix:value format
        if ':' not in tag:
            # Not in expected format, prefix with 'new:'
            return f"new:{tag}"
        
        prefix, value = tag.split(':', 1)
        
        # Check if prefix is in approved prefixes
        if prefix in self.approved:
            # Check if specific value is approved
            if value in self.approved[prefix]:
                return tag
            else:
                # Prefix is known but value is new
                # For now, allow it (could be changed to prefix with 'new:')
                return tag
        
        # Check if prefix is in allow_new_prefix
        if prefix in self.allow_new_prefix:
            return tag
        
        # Unknown prefix, treat as new
        return f"new:{tag}"


class ETLStats:
    """Track ETL execution statistics"""
    
    def __init__(self):
        self.files_scanned = 0
        self.index_lines_total = 0
        self.items_inserted = 0
        self.items_updated = 0
        self.items_unchanged = 0
        self.lines_failed = 0
        self.errors: List[Dict] = []
    
    def add_error(self, file_path: str, line: str, reason: str):
        """Record an error"""
        self.lines_failed += 1
        self.errors.append({
            'file': file_path,
            'line': line.strip(),
            'reason': reason,
            'timestamp': datetime.now().isoformat()
        })
    
    def summary(self) -> str:
        """Return formatted summary"""
        return (
            f"\n=== ETL Summary ===\n"
            f"Files scanned: {self.files_scanned}\n"
            f"INDEX lines total: {self.index_lines_total}\n"
            f"Items inserted: {self.items_inserted}\n"
            f"Items updated: {self.items_updated}\n"
            f"Items unchanged: {self.items_unchanged}\n"
            f"Lines failed: {self.lines_failed}\n"
        )


def compute_content_hash(item_data: Dict) -> str:
    """
    Compute hash for change detection
    
    Args:
        item_data: Parsed item dictionary
        
    Returns:
        SHA256 hash string
    """
    # Create deterministic string from key fields
    tags_sorted = sorted(item_data.get('tags', []))
    hash_input = (
        f"{item_data['type']}|"
        f"{item_data['body']}|"
        f"{item_data.get('effort_min', '')}|"
        f"{item_data.get('status', '')}|"
        f"{'|'.join(tags_sorted)}"
    )
    return hashlib.sha256(hash_input.encode('utf-8')).hexdigest()


def get_or_create_tag_id(conn: sqlite3.Connection, tag_name: str) -> int:
    """
    Get tag ID, creating if necessary
    
    Args:
        conn: Database connection
        tag_name: Normalized tag name (prefix:value)
        
    Returns:
        Tag ID
    """
    cursor = conn.cursor()
    
    # Try to get existing
    cursor.execute("SELECT id FROM tags WHERE name = ?", (tag_name,))
    row = cursor.fetchone()
    
    if row:
        return row[0]
    
    # Create new
    cursor.execute("INSERT INTO tags (name) VALUES (?)", (tag_name,))
    conn.commit()
    return cursor.lastrowid


def upsert_item(
    conn: sqlite3.Connection,
    date: str,
    item_type: str,
    body: str,
    ref_source_path: Optional[str],
    ref_block_id: Optional[str],
    source_path: str,
    block_id: str,
    effort_min: Optional[int],
    status: Optional[str],
    content_hash: str,
    tag_ids: List[int]
) -> str:
    """
    Upsert item into database
    
    Args:
        conn: Database connection
        date: Date string (YYYY-MM-DD)
        item_type: Type (learning/experiment/idea/action)
        body: Text content
        ref_source_path: Referenced source path (for link body)
        ref_block_id: Referenced block ID (for link body)
        source_path: Source daily file path
        block_id: Block ID
        effort_min: Effort in minutes (action only)
        status: Status (action only)
        content_hash: Content hash for change detection
        tag_ids: List of tag IDs
        
    Returns:
        'inserted', 'updated', or 'unchanged'
    """
    cursor = conn.cursor()
    
    # Check if exists
    cursor.execute(
        "SELECT id, content_hash FROM items WHERE source_path = ? AND block_id = ?",
        (source_path, block_id)
    )
    existing = cursor.fetchone()
    
    now = datetime.now().isoformat()
    
    if existing:
        item_id, old_hash = existing
        
        # Check if content changed
        if old_hash == content_hash:
            # No change, don't update
            return 'unchanged'
        
        # Update existing item
        cursor.execute(
            """
            UPDATE items SET
                date = ?,
                type = ?,
                text = ?,
                ref_source_path = ?,
                ref_block_id = ?,
                effort_min = ?,
                status = ?,
                content_hash = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (date, item_type, body, ref_source_path, ref_block_id,
             effort_min, status, content_hash, now, item_id)
        )
        
        # Update tags (delete old, insert new)
        cursor.execute("DELETE FROM item_tags WHERE item_id = ?", (item_id,))
        for tag_id in tag_ids:
            cursor.execute(
                "INSERT INTO item_tags (item_id, tag_id) VALUES (?, ?)",
                (item_id, tag_id)
            )
        
        conn.commit()
        return 'updated'
    else:
        # Insert new item
        cursor.execute(
            """
            INSERT INTO items (
                date, type, text, ref_source_path, ref_block_id,
                source_path, block_id, effort_min, status,
                content_hash, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (date, item_type, body, ref_source_path, ref_block_id,
             source_path, block_id, effort_min, status,
             content_hash, now, now)
        )
        
        item_id = cursor.lastrowid
        
        # Insert tags
        for tag_id in tag_ids:
            cursor.execute(
                "INSERT INTO item_tags (item_id, tag_id) VALUES (?, ?)",
                (item_id, tag_id)
            )
        
        conn.commit()
        return 'inserted'


def extract_date_from_filename(filename: str) -> Optional[str]:
    """
    Extract date from daily filename (YYYY-MM-DD.md)
    
    Args:
        filename: Filename string
        
    Returns:
        Date string (YYYY-MM-DD) or None if invalid format
    """
    match = re.match(r'(\d{4}-\d{2}-\d{2})\.md$', filename)
    if match:
        return match.group(1)
    return None


def process_daily_file(
    file_path: str,
    conn: sqlite3.Connection,
    normalizer: TagNormalizer,
    stats: ETLStats
):
    """
    Process a single daily file
    
    Args:
        file_path: Path to daily file
        conn: Database connection
        normalizer: Tag normalizer
        stats: Statistics tracker
    """
    stats.files_scanned += 1
    
    # Extract date from filename
    filename = os.path.basename(file_path)
    date = extract_date_from_filename(filename)
    
    if not date:
        logger.warning(f"Skipping file with invalid name format: {file_path}")
        return
    
    # Read file content
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        logger.error(f"Failed to read file {file_path}: {e}")
        stats.add_error(file_path, '', f"File read error: {e}")
        return
    
    # Extract INDEX section
    try:
        index_lines = extract_index_section(content)
    except IndexParseError as e:
        logger.warning(f"No INDEX section in {file_path}: {e}")
        stats.add_error(file_path, '', str(e))
        return
    
    stats.index_lines_total += len(index_lines)
    
    # Process each INDEX line
    for line in index_lines:
        try:
            # Parse line
            parsed = parse_index_line(line)
            
            # Normalize tags
            normalized_tags = [normalizer.normalize(tag) for tag in parsed['tags']]
            
            # Get or create tag IDs
            tag_ids = [get_or_create_tag_id(conn, tag) for tag in normalized_tags]
            
            # Compute content hash
            parsed['tags'] = normalized_tags  # Use normalized tags for hash
            content_hash = compute_content_hash(parsed)
            
            # Build relative source path
            source_path = f"00.daily/{filename}"
            
            # Upsert item
            result = upsert_item(
                conn=conn,
                date=date,
                item_type=parsed['type'],
                body=parsed['body'],
                ref_source_path=parsed['ref_source_path'],
                ref_block_id=parsed['ref_block_id'],
                source_path=source_path,
                block_id=parsed['block_id'],
                effort_min=parsed['effort_min'],
                status=parsed['status'],
                content_hash=content_hash,
                tag_ids=tag_ids
            )
            
            # Update stats
            if result == 'inserted':
                stats.items_inserted += 1
            elif result == 'updated':
                stats.items_updated += 1
            elif result == 'unchanged':
                stats.items_unchanged += 1
                
        except IndexParseError as e:
            logger.debug(f"Parse error in {file_path}: {e}")
            stats.add_error(file_path, line, str(e))
        except Exception as e:
            logger.error(f"Unexpected error processing line in {file_path}: {e}")
            stats.add_error(file_path, line, f"Unexpected error: {e}")


def get_daily_files(vault_path: str, since_days: Optional[int] = None) -> List[str]:
    """
    Get list of daily files to process
    
    Args:
        vault_path: Path to vault root
        since_days: If specified, only process files from last N days
        
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


def save_error_log(vault_path: str, stats: ETLStats):
    """
    Save error log to logs/etl_errors.log
    
    Args:
        vault_path: Path to vault root
        stats: Statistics with errors
    """
    if not stats.errors:
        return
    
    logs_dir = os.path.join(vault_path, '99.system', 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    
    log_file = os.path.join(logs_dir, 'etl_errors.log')
    
    try:
        with open(log_file, 'a', encoding='utf-8') as f:
            for error in stats.errors:
                f.write(json.dumps(error, ensure_ascii=False) + '\n')
        
        logger.info(f"Saved {len(stats.errors)} errors to {log_file}")
    except Exception as e:
        logger.error(f"Failed to save error log: {e}")


def main():
    """Main ETL execution"""
    parser = argparse.ArgumentParser(description='ETL: Extract daily notes INDEX to database')
    parser.add_argument('--vault', default='.', help='Path to vault root (default: current directory)')
    parser.add_argument('--full', action='store_true', help='Full scan of all daily files')
    parser.add_argument('--since', type=int, help='Process files from last N days')
    parser.add_argument('--dry-run', action='store_true', help='Parse only, do not write to DB')
    
    args = parser.parse_args()
    
    vault_path = os.path.abspath(args.vault)
    
    # Determine scan mode
    since_days = None
    if not args.full and args.since:
        since_days = args.since
    elif not args.full:
        # Default to last 7 days if neither --full nor --since is specified
        since_days = 7
        logger.info("No --full or --since specified, defaulting to last 7 days")
    
    # Setup paths
    db_path = os.path.join(vault_path, '99.system', 'db', 'notes.sqlite')
    taxonomy_path = os.path.join(vault_path, '99.system', 'taxonomy', 'tags.yml')
    
    # Check if DB exists
    if not os.path.exists(db_path):
        logger.error(f"Database not found: {db_path}")
        logger.error("Please run: sqlite3 vault/99.system/db/notes.sqlite < init_db.sql")
        return 1
    
    # Initialize components
    normalizer = TagNormalizer(taxonomy_path)
    stats = ETLStats()
    
    # Get files to process
    files = get_daily_files(vault_path, since_days)
    
    if not files:
        logger.warning("No daily files found to process")
        return 0
    
    logger.info(f"Processing {len(files)} daily files...")
    
    if args.dry_run:
        logger.info("DRY RUN mode - no database writes")
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    
    try:
        # Process each file
        for file_path in files:
            if args.dry_run:
                # In dry run, just parse without DB operations
                # For now, skip dry-run detailed implementation
                pass
            else:
                process_daily_file(file_path, conn, normalizer, stats)
        
        # Print summary
        print(stats.summary())
        
        # Save error log
        if stats.errors:
            save_error_log(vault_path, stats)
            logger.warning(f"{stats.lines_failed} lines failed - see logs/etl_errors.log")
        
    finally:
        conn.close()
    
    return 0 if stats.lines_failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
