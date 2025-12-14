"""
Export Pack: Generate extraction packs for blog authoring

This script:
1. Queries items from DB based on filters (tag, date range, type)
2. Generates a markdown file with source block references
3. Exports to exports/ directory for AI processing
"""
import argparse
import logging
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Tuple


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def query_items(
    conn: sqlite3.Connection,
    tag: str = None,
    from_date: str = None,
    to_date: str = None,
    item_type: str = None,
    order: str = 'asc'
) -> List[Tuple]:
    """
    Query items from database with filters
    
    Args:
        conn: Database connection
        tag: Filter by tag (e.g., "book:書籍名")
        from_date: Start date (YYYY-MM-DD)
        to_date: End date (YYYY-MM-DD)
        item_type: Filter by type (learning/experiment/idea/action/all)
        order: Sort order ('asc' or 'desc')
        
    Returns:
        List of tuples (date, source_path, block_id, type, text, tags)
    """
    cursor = conn.cursor()
    
    # Build query
    query = """
        SELECT i.date, i.source_path, i.block_id, i.type, i.text,
               GROUP_CONCAT(t.name, ' ') as tags
        FROM items i
        LEFT JOIN item_tags it ON i.id = it.item_id
        LEFT JOIN tags t ON it.tag_id = t.id
        WHERE 1=1
    """
    
    params = []
    
    # Add tag filter
    if tag:
        query += """
            AND i.id IN (
                SELECT i2.id FROM items i2
                JOIN item_tags it2 ON i2.id = it2.item_id
                JOIN tags t2 ON it2.tag_id = t2.id
                WHERE t2.name = ?
            )
        """
        params.append(tag)
    
    # Add date filters
    if from_date:
        query += " AND i.date >= ?"
        params.append(from_date)
    
    if to_date:
        query += " AND i.date <= ?"
        params.append(to_date)
    
    # Add type filter
    if item_type and item_type != 'all':
        query += " AND i.type = ?"
        params.append(item_type)
    
    # Group and order
    query += " GROUP BY i.id"
    
    if order == 'desc':
        query += " ORDER BY i.date DESC"
    else:
        query += " ORDER BY i.date ASC"
    
    cursor.execute(query, params)
    return cursor.fetchall()


def generate_export_pack(
    items: List[Tuple],
    title: str,
    filters: dict
) -> str:
    """
    Generate export pack markdown content
    
    Args:
        items: List of items from query
        title: Pack title
        filters: Applied filters for frontmatter
        
    Returns:
        Markdown content
    """
    # Build frontmatter
    lines = [
        "---",
        f"title: {title}",
        f"generated_at: {datetime.now().isoformat()}",
        f"source_count: {len(items)}",
        "filters:",
    ]
    
    for key, value in filters.items():
        if value:
            lines.append(f"  {key}: {value}")
    
    lines.extend([
        "---",
        "",
        f"# {title}",
        "",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        f"Total source blocks: {len(items)}",
        "",
        "## Source Blocks",
        "",
    ])
    
    # Add source blocks
    for date, source_path, block_id, item_type, text, tags in items:
        # Format: - 2025-12-13 [learning]: ![[daily/2025-12-13.md#^20251213-l1]]
        tag_str = ""
        if tags:
            tag_str = " " + " ".join(f"#{tag}" for tag in tags.split())
        
        lines.append(f"- {date} [{item_type}]: ![[{source_path}#{block_id}]]{tag_str}")
    
    lines.extend([
        "",
        "## Notes",
        "",
        "*(This section is for AI-generated synthesis, summaries, or blog draft content)*",
        "",
    ])
    
    return "\n".join(lines)


def sanitize_filename(name: str) -> str:
    """
    Sanitize string for use as filename
    
    Args:
        name: Input string
        
    Returns:
        Safe filename string
    """
    # Replace invalid characters
    safe = name.replace('/', '_').replace('\\', '_').replace(':', '_')
    safe = safe.replace(' ', '_').replace('|', '_')
    
    # Limit length
    if len(safe) > 100:
        safe = safe[:100]
    
    return safe


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(description='Generate export pack for blog authoring')
    parser.add_argument('--vault', default='.', help='Path to vault root (default: current directory)')
    parser.add_argument('--tag', required=True, help='Filter by tag (e.g., "book:書籍名")')
    parser.add_argument('--from', dest='from_date', help='Start date (YYYY-MM-DD)')
    parser.add_argument('--to', dest='to_date', help='End date (YYYY-MM-DD)')
    parser.add_argument('--type', dest='item_type', 
                       choices=['learning', 'experiment', 'idea', 'action', 'all'],
                       default='all',
                       help='Filter by item type (default: all)')
    parser.add_argument('--order', choices=['asc', 'desc'], default='asc',
                       help='Sort order by date (default: asc)')
    parser.add_argument('--output', help='Output filename (optional, auto-generated if not specified)')
    
    args = parser.parse_args()
    
    vault_path = os.path.abspath(args.vault)
    db_path = os.path.join(vault_path, '99.system', 'db', 'notes.sqlite')
    exports_dir = os.path.join(vault_path, '02.blog', 'drafts')
    
    if not os.path.exists(db_path):
        logger.error(f"Database not found: {db_path}")
        return 1
    
    # Create exports directory
    os.makedirs(exports_dir, exist_ok=True)
    
    # Query items
    conn = sqlite3.connect(db_path)
    
    try:
        logger.info(f"Querying items with filters: tag={args.tag}, "
                   f"from={args.from_date}, to={args.to_date}, type={args.item_type}")
        
        items = query_items(
            conn=conn,
            tag=args.tag,
            from_date=args.from_date,
            to_date=args.to_date,
            item_type=args.item_type,
            order=args.order
        )
        
        if not items:
            logger.warning("No items found matching the filters")
            return 0
        
        logger.info(f"Found {len(items)} items")
        
        # Generate title
        title_parts = [args.tag]
        if args.from_date or args.to_date:
            date_range = f"{args.from_date or '...'} to {args.to_date or '...'}"
            title_parts.append(date_range)
        if args.item_type != 'all':
            title_parts.append(args.item_type)
        
        title = " - ".join(title_parts)
        
        # Prepare filters dict for frontmatter
        filters = {
            'tag': args.tag,
            'from': args.from_date,
            'to': args.to_date,
            'type': args.item_type if args.item_type != 'all' else None,
            'order': args.order
        }
        
        # Generate content
        content = generate_export_pack(items, title, filters)
        
        # Determine output filename
        if args.output:
            output_filename = args.output
            if not output_filename.endswith('.md'):
                output_filename += '.md'
        else:
            # Auto-generate filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_tag = sanitize_filename(args.tag)
            output_filename = f"{timestamp}_{safe_tag}.md"
        
        output_path = os.path.join(exports_dir, output_filename)
        
        # Write file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"Export pack created: {output_path}")
        logger.info(f"Total items: {len(items)}")
        
    finally:
        conn.close()
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
