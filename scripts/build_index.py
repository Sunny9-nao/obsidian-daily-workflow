"""
Build Index: Generate index markdown files from database

This script:
1. Reads items from SQLite DB
2. Generates index notes (ideas.md, actions.md, books/*.md)
3. Uses atomic write (tmp -> rename) to avoid corruption
"""
import argparse
import logging
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def atomic_write(file_path: str, content: str):
    """
    Write file atomically using tmp file + rename
    
    Args:
        file_path: Target file path
        content: Content to write
    """
    tmp_path = file_path + '.tmp'
    
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Write to tmp file
        with open(tmp_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Atomic rename
        os.replace(tmp_path, file_path)
        
    except Exception as e:
        # Clean up tmp file on error
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise e


def build_ideas_index(conn: sqlite3.Connection) -> str:
    """
    Build ideas.md content
    
    Args:
        conn: Database connection
        
    Returns:
        Markdown content
    """
    cursor = conn.cursor()
    
    # Get all ideas, newest first
    cursor.execute(
        """
        SELECT i.date, i.source_path, i.block_id, GROUP_CONCAT(t.name, ' ') as tags
        FROM items i
        LEFT JOIN item_tags it ON i.id = it.item_id
        LEFT JOIN tags t ON it.tag_id = t.id
        WHERE i.type = 'idea'
        GROUP BY i.id
        ORDER BY i.date DESC
        """
    )
    
    rows = cursor.fetchall()
    
    # Build content
    lines = [
        "# Ideas Index",
        "",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        f"Total: {len(rows)} ideas",
        "",
    ]
    
    for date, source_path, block_id, tags in rows:
        # Format: - 2025-12-13: ![[daily/2025-12-13.md#^20251213-i1]] #topic:workflow
        tag_str = ""
        if tags:
            tag_str = " " + " ".join(f"#{tag}" for tag in tags.split())
        
        lines.append(f"- {date}: ![[{source_path}#{block_id}]]{tag_str}")
    
    lines.append("")  # Trailing newline
    
    return "\n".join(lines)


def build_actions_index(conn: sqlite3.Connection) -> str:
    """
    Build actions.md content
    
    Args:
        conn: Database connection
        
    Returns:
        Markdown content
    """
    cursor = conn.cursor()
    
    # Get active actions (inbox or doing)
    # Sort by: status (doing first), effort_min ASC, date DESC
    cursor.execute(
        """
        SELECT i.date, i.source_path, i.block_id, i.status, i.effort_min, 
               GROUP_CONCAT(t.name, ' ') as tags
        FROM items i
        LEFT JOIN item_tags it ON i.id = it.item_id
        LEFT JOIN tags t ON it.tag_id = t.id
        WHERE i.type = 'action' AND i.status IN ('inbox', 'doing')
        GROUP BY i.id
        ORDER BY 
            CASE i.status 
                WHEN 'doing' THEN 0 
                WHEN 'inbox' THEN 1 
            END,
            i.effort_min ASC,
            i.date DESC
        """
    )
    
    rows = cursor.fetchall()
    
    # Build content
    lines = [
        "# Actions Index",
        "",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        f"Total: {len(rows)} active actions",
        "",
    ]
    
    for date, source_path, block_id, status, effort_min, tags in rows:
        # Format: - [inbox|30m] 2025-12-13: ![[daily/2025-12-13.md#^20251213-a1]] #topic:productivity
        tag_str = ""
        if tags:
            tag_str = " " + " ".join(f"#{tag}" for tag in tags.split())
        
        effort_str = f"{effort_min}m" if effort_min else "?m"
        lines.append(f"- [{status}|{effort_str}] {date}: ![[{source_path}#{block_id}]]{tag_str}")
    
    lines.append("")  # Trailing newline
    
    return "\n".join(lines)


def get_book_list(conn: sqlite3.Connection) -> List[str]:
    """
    Get list of unique book tags
    
    Args:
        conn: Database connection
        
    Returns:
        List of book names (without "book:" prefix)
    """
    cursor = conn.cursor()
    
    cursor.execute(
        """
        SELECT DISTINCT name FROM tags 
        WHERE name LIKE 'book:%'
        ORDER BY name
        """
    )
    
    books = []
    for (tag_name,) in cursor.fetchall():
        # Extract book name (remove "book:" prefix)
        book_name = tag_name.replace('book:', '', 1)
        books.append(book_name)
    
    return books


def get_course_list(conn: sqlite3.Connection) -> List[str]:
    """
    Get list of unique course tags
    
    Args:
        conn: Database connection
        
    Returns:
        List of course names (without "course:" prefix)
    """
    cursor = conn.cursor()
    
    cursor.execute(
        """
        SELECT DISTINCT name FROM tags 
        WHERE name LIKE 'course:%'
        ORDER BY name
        """
    )
    
    courses = []
    for (tag_name,) in cursor.fetchall():
        # Extract course name (remove "course:" prefix)
        course_name = tag_name.replace('course:', '', 1)
        courses.append(course_name)
    
    return courses


def build_book_index(conn: sqlite3.Connection, book_name: str) -> str:
    """
    Build index for a specific book
    
    Args:
        conn: Database connection
        book_name: Book name (without "book:" prefix)
        
    Returns:
        Markdown content
    """
    cursor = conn.cursor()
    
    tag_name = f"book:{book_name}"
    
    # Get all items tagged with this book, oldest first (reading timeline)
    cursor.execute(
        """
        SELECT i.date, i.source_path, i.block_id, i.type,
               GROUP_CONCAT(t.name, ' ') as tags
        FROM items i
        JOIN item_tags it ON i.id = it.item_id
        JOIN tags t ON it.tag_id = t.id
        LEFT JOIN item_tags it2 ON i.id = it2.item_id
        LEFT JOIN tags t2 ON it2.tag_id = t2.id
        WHERE t.name = ?
        GROUP BY i.id
        ORDER BY i.date ASC
        """,
        (tag_name,)
    )
    
    rows = cursor.fetchall()
    
    # Build content
    lines = [
        f"# Book: {book_name}",
        "",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        f"Total: {len(rows)} items",
        "",
    ]
    
    for date, source_path, block_id, item_type, tags in rows:
        # Format: - 2025-12-13 [learning]: ![[daily/2025-12-13.md#^20251213-l1]]
        tag_str = ""
        if tags:
            # Show all tags except the current book tag
            other_tags = [tag for tag in tags.split() if tag != tag_name]
            if other_tags:
                tag_str = " " + " ".join(f"#{tag}" for tag in other_tags)
        
        lines.append(f"- {date} [{item_type}]: ![[{source_path}#{block_id}]]{tag_str}")
    
    lines.append("")  # Trailing newline
    
    return "\n".join(lines)


def build_course_index(conn: sqlite3.Connection, course_name: str) -> str:
    """
    Build index for a specific course
    
    Args:
        conn: Database connection
        course_name: Course name (without "course:" prefix)
        
    Returns:
        Markdown content
    """
    cursor = conn.cursor()
    
    tag_name = f"course:{course_name}"
    
    # Get all items tagged with this course, oldest first (learning timeline)
    cursor.execute(
        """
        SELECT i.date, i.source_path, i.block_id, i.type,
               GROUP_CONCAT(t.name, ' ') as tags
        FROM items i
        JOIN item_tags it ON i.id = it.item_id
        JOIN tags t ON it.tag_id = t.id
        LEFT JOIN item_tags it2 ON i.id = it2.item_id
        LEFT JOIN tags t2 ON it2.tag_id = t2.id
        WHERE t.name = ?
        GROUP BY i.id
        ORDER BY i.date ASC
        """,
        (tag_name,)
    )
    
    rows = cursor.fetchall()
    
    # Build content
    lines = [
        f"# Course: {course_name}",
        "",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        f"Total: {len(rows)} items",
        "",
    ]
    
    for date, source_path, block_id, item_type, tags in rows:
        # Format: - 2025-12-14 [learning]: ![[00.daily/2025-12-14.md#^20251214-l1]]
        tag_str = ""
        if tags:
            # Show all tags except the current course tag
            other_tags = [tag for tag in tags.split() if tag != tag_name]
            if other_tags:
                tag_str = " " + " ".join(f"#{tag}" for tag in other_tags)
        
        lines.append(f"- {date} [{item_type}]: ![[{source_path}#{block_id}]]{tag_str}")
    
    lines.append("")  # Trailing newline
    
    return "\n".join(lines)


def build_all_indexes(vault_path: str, only: str = None) -> Tuple[int, int]:
    """
    Build all index files
    
    Args:
        vault_path: Path to vault root
        only: If specified, only build 'ideas', 'actions', or 'books'
        
    Returns:
        Tuple of (files_generated, errors)
    """
    db_path = os.path.join(vault_path, '99.system', 'db', 'notes.sqlite')
    index_dir = os.path.join(vault_path, '01.index')
    
    if not os.path.exists(db_path):
        logger.error(f"Database not found: {db_path}")
        return 0, 1
    
    conn = sqlite3.connect(db_path)
    files_generated = 0
    errors = 0
    
    try:
        # Build ideas.md
        if only is None or only == 'ideas':
            try:
                logger.info("Building ideas.md...")
                content = build_ideas_index(conn)
                ideas_path = os.path.join(index_dir, 'ideas.md')
                atomic_write(ideas_path, content)
                files_generated += 1
                logger.info(f"Created {ideas_path}")
            except Exception as e:
                logger.error(f"Failed to build ideas.md: {e}")
                errors += 1
        
        # Build actions.md
        if only is None or only == 'actions':
            try:
                logger.info("Building actions.md...")
                content = build_actions_index(conn)
                actions_path = os.path.join(index_dir, 'actions.md')
                atomic_write(actions_path, content)
                files_generated += 1
                logger.info(f"Created {actions_path}")
            except Exception as e:
                logger.error(f"Failed to build actions.md: {e}")
                errors += 1
        
        # Build book indexes
        if only is None or only == 'books':
            try:
                logger.info("Building book indexes...")
                books = get_book_list(conn)
                books_dir = os.path.join(index_dir, 'books')
                
                for book_name in books:
                    try:
                        content = build_book_index(conn, book_name)
                        # Sanitize book name for filename
                        safe_name = book_name.replace('/', '_').replace('\\', '_')
                        book_path = os.path.join(books_dir, f"{safe_name}.md")
                        atomic_write(book_path, content)
                        files_generated += 1
                    except Exception as e:
                        logger.error(f"Failed to build index for book '{book_name}': {e}")
                        errors += 1
                
                logger.info(f"Created {len(books)} book indexes in {books_dir}")
                
            except Exception as e:
                logger.error(f"Failed to build book indexes: {e}")
                errors += 1
        
        # Build course indexes
        if only is None or only == 'courses':
            try:
                logger.info("Building course indexes...")
                courses = get_course_list(conn)
                courses_dir = os.path.join(index_dir, 'courses')
                
                for course_name in courses:
                    try:
                        content = build_course_index(conn, course_name)
                        # Sanitize course name for filename
                        safe_name = course_name.replace('/', '_').replace('\\', '_')
                        course_path = os.path.join(courses_dir, f"{safe_name}.md")
                        atomic_write(course_path, content)
                        files_generated += 1
                    except Exception as e:
                        logger.error(f"Failed to build index for course '{course_name}': {e}")
                        errors += 1
                
                logger.info(f"Created {len(courses)} course indexes in {courses_dir}")
                
            except Exception as e:
                logger.error(f"Failed to build course indexes: {e}")
                errors += 1
        
    finally:
        conn.close()
    
    return files_generated, errors


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(description='Build index markdown files from database')
    parser.add_argument('--vault', default='.', help='Path to vault root (default: current directory)')
    parser.add_argument('--only', choices=['ideas', 'actions', 'books'], 
                       help='Only build specific index type')
    
    args = parser.parse_args()
    
    vault_path = os.path.abspath(args.vault)
    
    logger.info("Building indexes...")
    
    files_generated, errors = build_all_indexes(vault_path, args.only)
    
    logger.info(f"\n=== Summary ===")
    logger.info(f"Files generated: {files_generated}")
    logger.info(f"Errors: {errors}")
    
    return 0 if errors == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
