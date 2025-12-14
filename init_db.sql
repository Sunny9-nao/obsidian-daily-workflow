-- Daily Notes Index Database Schema
-- Purpose: Store minimal indexed information from daily notes for search and extraction

-- Main items table (indexed entries from daily notes)
CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,                    -- YYYY-MM-DD format from filename
    type TEXT NOT NULL,                    -- learning/experiment/idea/action
    text TEXT NOT NULL,                    -- Short label or link text
    ref_source_path TEXT,                  -- Referenced daily path (for LINK_BODY)
    ref_block_id TEXT,                     -- Referenced block ID (for LINK_BODY)
    source_path TEXT NOT NULL,             -- daily/YYYY-MM-DD.md
    block_id TEXT NOT NULL,                -- ^YYYYMMDD-...
    effort_min INTEGER,                    -- action only
    status TEXT,                           -- action only: inbox/doing/done/dropped
    content_hash TEXT NOT NULL,            -- For change detection
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(source_path, block_id)         -- Critical for idempotent upsert
);

-- Tags table (normalized tags)
CREATE TABLE IF NOT EXISTS tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE              -- Format: "prefix:value" (e.g., "tech:playwright")
);

-- Many-to-many relationship between items and tags
CREATE TABLE IF NOT EXISTS item_tags (
    item_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,
    PRIMARY KEY (item_id, tag_id),
    FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
);

-- ETL execution log (optional but recommended)
CREATE TABLE IF NOT EXISTS etl_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    files_scanned INTEGER,
    items_inserted INTEGER,
    items_updated INTEGER,
    items_unchanged INTEGER,
    lines_failed INTEGER,
    error_log TEXT
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_items_date ON items(date);
CREATE INDEX IF NOT EXISTS idx_items_type ON items(type);
CREATE INDEX IF NOT EXISTS idx_items_status ON items(status);
CREATE INDEX IF NOT EXISTS idx_items_source_path ON items(source_path);
