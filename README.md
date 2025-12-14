# Obsidian Daily Workflow

AI 経由で日次ノートを整形し、ブログ化・索引化する仕組み。

## ✨ 特徴

- **VS Code 中心の運用**: 編集・AI 利用・スクリプト実行は VS Code で
- **Obsidian で閲覧・探索**: バックリンク/グラフで関連発見
- **何日サボっても OK**: 冪等な ETL 設計で安心
- **シンプルな設計**: Markdown + SQLite + Python
- **テスト完備**: 40 のテストで品質保証

## 🚀 クイックスタート

```bash
# 1. 仮想環境セットアップ
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. データベース初期化
mkdir -p vault/db
sqlite3 vault/db/notes.sqlite < init_db.sql

# 3. テスト実行（推奨）
python -m pytest tests/ -v

# 4. サンプルで動作確認
cp tests/fixtures/*.md vault/daily/
python -m scripts.etl --vault vault --full
python -m scripts.build_index --vault vault

# 5. 生成されたインデックスを確認
cat vault/index/ideas.md
cat vault/index/actions.md
```

**詳細は [QUICKSTART.md](QUICKSTART.md) を参照してください。**

**Obsidian の設定は [vault/99.system/docs/OBSIDIAN_SETUP.md](vault/99.system/docs/OBSIDIAN_SETUP.md) を参照してください。**

## 📁 プロジェクト構成

```
vault/
  daily/           # 日次ノート（手動作成）
  index/           # 自動生成される索引ノート
    ideas.md
    actions.md
    books/
  exports/         # ブログ化用の抽出パック
  taxonomy/        # タグ辞書
    tags.yml
  db/              # SQLiteデータベース
    notes.sqlite
  logs/            # エラーログ
  docs/            # 設計ドキュメント

scripts/           # Pythonスクリプト
  etl.py           # ETL処理（daily -> DB）
  build_index.py   # インデックス生成（DB -> index）
  export_pack.py   # 抽出パック生成
  validate_daily.py # バリデーション
  index_parser.py  # INDEXパーサー

tests/             # テストコード（40 tests）
  test_index_parser.py
  test_etl.py
  test_build_index.py
  test_validate_daily.py
  test_integration.py
```

## 🔄 基本ワークフロー

1. **日次ノート作成**: `vault/00.daily/YYYY-MM-DD.md`
2. **ETL 実行**: `python -m scripts.etl --vault vault`
3. **インデックス更新**: `python -m scripts.build_index --vault vault`
4. **Obsidian で閲覧**: `vault/01.index/*.md`

## 📝 主要コマンド

### ETL（daily -> DB）

```bash
# 全ファイル処理
python -m scripts.etl --vault vault --full

# 直近7日のみ（デフォルト）
python -m scripts.etl --vault vault

# バリデーション
python -m scripts.validate_daily --vault vault --since 7
```

### インデックス生成（DB -> index）

```bash
# 全インデックス生成
python -m scripts.build_index --vault vault

# 特定のインデックスのみ
python -m scripts.build_index --vault vault --only ideas
```

### エクスポートパック生成

```bash
python -m scripts.export_pack \
  --vault vault \
  --tag "book:書籍名" \
  --type learning
```

## 🧪 テスト

```bash
# 全テスト実行（40 tests）
python -m pytest tests/ -v

# カバレッジ付き
python -m pytest tests/ --cov=scripts --cov-report=html

# 統合テスト
python -m pytest tests/test_integration.py -v
```

すべてのテストが成功することを確認済み ✅

## 📚 ドキュメント

- **[QUICKSTART.md](QUICKSTART.md)** - セットアップと基本操作
- [要件定義](vault/docs/requirements.md) - プロジェクトの目的と要件
- [詳細設計](vault/docs/detailed_design.md) - 技術仕様
- [AI 向け規約](vault/docs/ai-instructions.md) - 日次ノートの書き方
- [実装ステップ](vault/docs/impl_steps.md) - 運用手順

## 🛠️ トラブルシューティング

### ETL でエラーが出る

```bash
# エラーログ確認
cat vault/99.system/logs/etl_errors.log

# バリデーションで詳細確認
python -m scripts.validate_daily --vault vault -v
```

### データベースをリセット

```bash
rm vault/99.system/db/notes.sqlite
sqlite3 vault/99.system/db/notes.sqlite < init_db.sql
python -m scripts.etl --vault vault --full
```

## 📄 ライセンス

MIT
