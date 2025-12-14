""""
Test fixtures for INDEX parser testing
"""

# Valid INDEX lines (OK examples from ai-instructions.md)
VALID_LINES = [
    # learning with link
    "- [learning] ![[daily/2025-12-13.md#^20251213-t1]] #book:開発生産性の教科書 #topic:reading ^20251213-l1",
    # idea with text
    "- [idea] メトリクスの週次レビューを自動化する #topic:workflow #new:automation ^20251213-i1",
    # action with meta
    "- [action] 週次で指標を1つ決める effort=30 status=inbox #topic:productivity ^20251213-a1",
    # experiment
    "- [experiment] Playwright で E2E テスト実装 #tech:playwright #topic:testing ^20251214-e1",
    # learning without tags
    "- [learning] ![[daily/2025-12-14.md#^20251214-t1]] ^20251214-l1",
    # action with doing status
    "- [action] CI/CD パイプラインに Playwright テストを組み込む effort=60 status=doing #tech:playwright #src:work ^20251214-a1",
]

# Invalid INDEX lines (NG examples)
INVALID_LINES = [
    # Missing type
    "- ![[daily/2025-12-13.md#^20251213-t1]] #book:開発生産性の教科書 ^20251213-l1",
    # Missing block ID
    "- [learning] ![[daily/2025-12-13.md#^20251213-t1]] #book:開発生産性の教科書",
    # action without meta
    "- [action] 週次レビュー実施 #topic:productivity ^20251213-a1",
    # Invalid block ID format
    "- [idea] アイデア #topic:workflow ^idea1",
    # Invalid tag format (no prefix:value)
    "- [learning] ![[daily/2025-12-13.md#^20251213-t1]] #開発生産性の教科書 ^20251213-l1",
    # Invalid type
    "- [unknown] something #topic:test ^20251213-u1",
]

# Expected parsed results for valid lines
EXPECTED_PARSED = [
    {
        "type": "learning",
        "body": "![[daily/2025-12-13.md#^20251213-t1]]",
        "ref_source_path": "daily/2025-12-13.md",
        "ref_block_id": "^20251213-t1",
        "tags": ["book:開発生産性の教科書", "topic:reading"],
        "block_id": "^20251213-l1",
        "effort_min": None,
        "status": None,
    },
    {
        "type": "idea",
        "body": "メトリクスの週次レビューを自動化する",
        "ref_source_path": None,
        "ref_block_id": None,
        "tags": ["topic:workflow", "new:automation"],
        "block_id": "^20251213-i1",
        "effort_min": None,
        "status": None,
    },
    {
        "type": "action",
        "body": "週次で指標を1つ決める",
        "ref_source_path": None,
        "ref_block_id": None,
        "tags": ["topic:productivity"],
        "block_id": "^20251213-a1",
        "effort_min": 30,
        "status": "inbox",
    },
    {
        "type": "experiment",
        "body": "Playwright で E2E テスト実装",
        "ref_source_path": None,
        "ref_block_id": None,
        "tags": ["tech:playwright", "topic:testing"],
        "block_id": "^20251214-e1",
        "effort_min": None,
        "status": None,
    },
    {
        "type": "learning",
        "body": "![[daily/2025-12-14.md#^20251214-t1]]",
        "ref_source_path": "daily/2025-12-14.md",
        "ref_block_id": "^20251214-t1",
        "tags": [],
        "block_id": "^20251214-l1",
        "effort_min": None,
        "status": None,
    },
    {
        "type": "action",
        "body": "CI/CD パイプラインに Playwright テストを組み込む",
        "ref_source_path": None,
        "ref_block_id": None,
        "tags": ["tech:playwright", "src:work"],
        "block_id": "^20251214-a1",
        "effort_min": 60,
        "status": "doing",
    },
]
