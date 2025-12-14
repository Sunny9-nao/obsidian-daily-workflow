#!/usr/bin/env python3
"""
DB View Generator - SQLiteデータベースの内容をMarkdown形式で出力

Usage:
    python scripts/db_view.py [--vault VAULT_PATH]
"""

import argparse
import sqlite3
from pathlib import Path
from datetime import datetime


def generate_db_view(vault_path: Path) -> str:
    """Generate markdown view of database contents"""
    db_path = vault_path / "99.system" / "db" / "notes.sqlite"
    
    if not db_path.exists():
        return "# Database View\n\n⚠️ Database not found. Run `python scripts/etl.py` first.\n"
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    output = []
    output.append("# Database View")
    output.append(f"\n*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")
    output.append("---\n")
    
    # サマリー統計
    output.append("## 📊 Summary Statistics\n")
    
    cursor.execute("SELECT COUNT(*) as total FROM items")
    total = cursor.fetchone()["total"]
    output.append(f"**Total Items**: {total}\n")
    
    cursor.execute("""
        SELECT type, COUNT(*) as count 
        FROM items 
        GROUP BY type 
        ORDER BY count DESC
    """)
    output.append("\n**Items by Type**:\n")
    for row in cursor.fetchall():
        output.append(f"- {row['type']}: {row['count']}\n")
    
    cursor.execute("""
        SELECT name, COUNT(*) as count 
        FROM tags 
        JOIN item_tags ON tags.id = item_tags.tag_id 
        GROUP BY tags.id 
        ORDER BY count DESC 
        LIMIT 10
    """)
    output.append("\n**Top 10 Tags**:\n")
    for row in cursor.fetchall():
        output.append(f"- `{row['name']}`: {row['count']} items\n")
    
    # アクション統計
    cursor.execute("""
        SELECT status, COUNT(*) as count 
        FROM items 
        WHERE type = 'action' AND status IS NOT NULL
        GROUP BY status
    """)
    output.append("\n**Actions by Status**:\n")
    action_stats = cursor.fetchall()
    if action_stats:
        for row in action_stats:
            output.append(f"- {row['status']}: {row['count']}\n")
    else:
        output.append("- No actions yet\n")
    
    output.append("\n---\n")
    
    # 最近のアイテム
    output.append("## 🕐 Recent Items (Last 20)\n")
    cursor.execute("""
        SELECT 
            date,
            type,
            text,
            source_path,
            block_id,
            (SELECT GROUP_CONCAT(name, ', ') 
             FROM tags 
             JOIN item_tags ON tags.id = item_tags.tag_id 
             WHERE item_tags.item_id = items.id) as tags
        FROM items 
        ORDER BY date DESC, id DESC 
        LIMIT 20
    """)
    
    output.append("\n| Date | Type | Text | Tags | Source |\n")
    output.append("|------|------|------|------|--------|\n")
    for row in cursor.fetchall():
        date = row['date']
        type_ = row['type']
        text = row['text'][:50] + "..." if len(row['text']) > 50 else row['text']
        tags = row['tags'] if row['tags'] else ""
        source = f"[[{row['source_path']}#^{row['block_id']}]]"
        output.append(f"| {date} | {type_} | {text} | {tags} | {source} |\n")
    
    output.append("\n---\n")
    
    # タイプ別詳細
    output.append("## 📝 Items by Type\n")
    
    for item_type in ['idea', 'learning', 'action', 'experiment']:
        cursor.execute("""
            SELECT 
                date,
                text,
                source_path,
                block_id,
                effort_min,
                status,
                (SELECT GROUP_CONCAT(name, ', ') 
                 FROM tags 
                 JOIN item_tags ON tags.id = item_tags.tag_id 
                 WHERE item_tags.item_id = items.id) as tags
            FROM items 
            WHERE type = ?
            ORDER BY date DESC 
            LIMIT 10
        """, (item_type,))
        
        items = cursor.fetchall()
        if items:
            output.append(f"\n### {item_type.capitalize()}s (Last 10)\n")
            for row in items:
                text = row['text']
                source = f"[[{row['source_path']}#^{row['block_id']}]]"
                tags = row['tags'] if row['tags'] else ""
                meta = []
                if row['effort_min']:
                    meta.append(f"effort={row['effort_min']}")
                if row['status']:
                    meta.append(f"status={row['status']}")
                meta_str = f" ({', '.join(meta)})" if meta else ""
                tags_str = f" `{tags}`" if tags else ""
                
                output.append(f"- [{row['date']}] {text}{meta_str}{tags_str} - {source}\n")
    
    output.append("\n---\n")
    
    # 全タグ一覧
    output.append("## 🏷️ All Tags\n")
    cursor.execute("""
        SELECT name, COUNT(*) as count 
        FROM tags 
        JOIN item_tags ON tags.id = item_tags.tag_id 
        GROUP BY tags.id 
        ORDER BY name
    """)
    all_tags = cursor.fetchall()
    if all_tags:
        output.append("\n")
        for row in all_tags:
            output.append(f"- `{row['name']}` ({row['count']})\n")
    else:
        output.append("\n*No tags found*\n")
    
    output.append("\n---\n")
    
    # ETL実行ログ
    output.append("## 🔄 ETL Execution Log (Last 5 Runs)\n")
    cursor.execute("""
        SELECT 
            started_at,
            completed_at,
            files_scanned,
            items_inserted,
            items_updated,
            items_unchanged,
            lines_failed
        FROM etl_runs 
        ORDER BY started_at DESC 
        LIMIT 5
    """)
    
    runs = cursor.fetchall()
    if runs:
        output.append("\n| Started | Duration | Files | Inserted | Updated | Unchanged | Failed |\n")
        output.append("|---------|----------|-------|----------|---------|-----------|--------|\n")
        for row in runs:
            started = row['started_at'][:19]  # YYYY-MM-DD HH:MM:SS
            completed = row['completed_at'][:19] if row['completed_at'] else "In progress"
            files = row['files_scanned'] or 0
            inserted = row['items_inserted'] or 0
            updated = row['items_updated'] or 0
            unchanged = row['items_unchanged'] or 0
            failed = row['lines_failed'] or 0
            output.append(f"| {started} | - | {files} | {inserted} | {updated} | {unchanged} | {failed} |\n")
    else:
        output.append("\n*No ETL runs recorded*\n")
    
    output.append("\n---\n")
    output.append("\n*💡 Tip: Run `python scripts/db_view.py` to update this view*\n")
    
    conn.close()
    return "".join(output)


def main():
    parser = argparse.ArgumentParser(description="Generate database view in Markdown")
    parser.add_argument(
        "--vault",
        type=Path,
        default=Path("vault"),
        help="Path to vault directory (default: vault)",
    )
    args = parser.parse_args()
    
    # Generate view
    content = generate_db_view(args.vault)
    
    # Write to view.md
    output_path = args.vault / "view.md"
    output_path.write_text(content, encoding="utf-8")
    
    print(f"✅ Database view generated: {output_path}")
    print(f"📊 Open it in Obsidian to see database contents")


if __name__ == "__main__":
    main()
