# クイックスタートガイド

このガイドでは、Obsidian Daily Workflow を最初から動かすまでの手順を説明します。

## 前提条件

- macOS
- Python 3.11 以上
- SQLite3
- Obsidian（閲覧用、オプション）

## セットアップ手順

### 1. 仮想環境のセットアップ

```bash
cd /Users/takatonaoto/Documents/obsidian-daily-workflow
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. データベースの初期化

```bash
mkdir -p vault/99.system/db
sqlite3 vault/99.system/db/notes.sqlite < init_db.sql
```

### 3. テストの実行（オプションだが推奨）

```bash
python -m pytest tests/ -v
```

全テストが成功すれば、セットアップは完了です。

## 基本的な使い方

### Day1: サンプルで動作確認

既存のテストフィクスチャを使って動作確認：

```bash
# 1. テストフィクスチャを00.dailyにコピー
cp tests/fixtures/2025-12-13.md vault/00.daily/
cp tests/fixtures/2025-12-14.md vault/00.daily/

# 2. ETL実行（00.daily -> DB）
python -m scripts.etl --vault vault --full

# 3. インデックス生成（DB -> 01.index/*.md）
python -m scripts.build_index --vault vault

# 4. 生成されたファイルを確認
ls -la vault/01.index/
cat vault/01.index/ideas.md
cat vault/01.index/actions.md
```

### 毎日の運用

1. **日次ノートの作成**

   - `vault/00.daily/YYYY-MM-DD.md` を作成
   - テンプレートに従って記述（詳細は `vault/99.system/docs/ai-instructions.md` を参照）

2. **ETL の実行**

   ```bash
   # 直近7日分のみ処理（デフォルト）
   python -m scripts.etl --vault vault

   # または全ファイルを処理
   python -m scripts.etl --vault vault --full
   ```

3. **インデックス更新**

   ```bash
   python -m scripts.build_index --vault vault
   ```

4. **Obsidian で確認**
   - `vault/01.index/actions.md` で未処理のアクションを確認
   - `vault/01.index/ideas.md` でアイデア一覧を閲覧
   - バックリンクやグラフビューで関連を発見

### バリデーション（推奨）

日次ノートがフォーマットに従っているか確認：

```bash
python -m scripts.validate_daily --vault vault --since 7
```

エラーがあれば修正して ETL を再実行。

### ブログ化の準備

特定のタグ（例：書籍）で抽出パックを作成：

```bash
python -m scripts.export_pack \
  --vault vault \
  --tag "book:開発生産性の教科書" \
  --from 2025-11-01 \
  --to 2025-12-31 \
  --type learning
```

生成されたファイル（`vault/02.blog/drafts/*.md`）を AI に渡してブログ下書きを作成。

## トラブルシューティング

### ETL でエラーが出る

```bash
# エラーログを確認
cat vault/99.system/logs/etl_errors.log

# バリデーションで詳細確認
python -m scripts.validate_daily --vault vault -v
```

### データベースをリセットしたい

```bash
rm vault/99.system/db/notes.sqlite
sqlite3 vault/99.system/db/notes.sqlite < init_db.sql
python -m scripts.etl --vault vault --full
```

### タグの揺れを解消したい

1. `vault/taxonomy/tags.yml` を編集
   - `approved` に正式なタグを追加
   - `aliases` で同義語を設定
2. ETL を再実行
   ```bash
   python -m scripts.etl --vault vault --full
   ```

## テストについて

### 単体テスト

```bash
# 全テスト実行
python -m pytest tests/ -v

# 特定のテストのみ
python -m pytest tests/test_etl.py -v
python -m pytest tests/test_index_parser.py -v
```

### 統合テスト

```bash
# 完全なワークフローをテスト
python -m pytest tests/test_integration.py -v
```

## ディレクトリ構造

```
vault/
  00.daily/        # 日次ノート（運用中）
  01.index/        # 自動生成される索引ノート
    ideas.md
    actions.md
    books/
  02.blog/         # ブログ関連
    drafts/        # AI生成の下書き
    published/     # 公開済み（Zenn等）
  99.system/       # システム設定
    taxonomy/      # タグ辞書
    db/            # SQLiteデータベース
    logs/          # エラーログ
    docs/          # 設計ドキュメント

scripts/           # Pythonスクリプト
  etl.py           # ETL処理
  build_index.py   # インデックス生成
  export_pack.py   # 抽出パック生成
  validate_daily.py # バリデーション
  index_parser.py  # INDEXパーサー

tests/             # テストコード
```

## 次のステップ

1. `vault/docs/ai-instructions.md` を読んで、日次ノートのフォーマットを理解
2. `vault/docs/detailed_design.md` で設計の詳細を確認
3. 実際の日次ノートを作成して運用開始
4. GitHub Copilot などに `ai-instructions.md` を参照させて規約遵守率を向上

## コマンドリファレンス

### etl.py

```bash
# 全ファイル処理
python -m scripts.etl --vault vault --full

# 直近N日のみ
python -m scripts.etl --vault vault --since 7

# ドライラン（DBに書き込まない）
python -m scripts.etl --vault vault --dry-run
```

### build_index.py

```bash
# 全インデックス生成
python -m scripts.build_index --vault vault

# 特定のインデックスのみ
python -m scripts.build_index --vault vault --only ideas
python -m scripts.build_index --vault vault --only actions
python -m scripts.build_index --vault vault --only books
```

### export_pack.py

```bash
# タグで抽出
python -m scripts.export_pack --vault vault --tag "book:書籍名"

# 期間指定
python -m scripts.export_pack --vault vault \
  --tag "topic:workflow" \
  --from 2025-11-01 \
  --to 2025-12-31

# タイプ指定
python -m scripts.export_pack --vault vault \
  --tag "tech:python" \
  --type learning

# 出力ファイル名指定
python -m scripts.export_pack --vault vault \
  --tag "book:書籍名" \
  --output my-book-notes.md
```

### validate_daily.py

```bash
# 全ファイル検証
python -m scripts.validate_daily --vault vault

# 直近N日のみ
python -m scripts.validate_daily --vault vault --since 7

# 詳細出力
python -m scripts.validate_daily --vault vault -v
```
