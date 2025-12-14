# ディレクトリ構造ガイド

## 📁 新しいディレクトリ構造（2025-12-14 更新）

vault 内のフォルダを番号付き接頭辞で整理し、用途を明確にしました。

### 全体構造

```
vault/
├── 00.daily/          # 日次ノート（運用中）
├── 01.index/          # 自動生成される索引ノート
├── 02.blog/           # ブログ関連
└── 99.system/         # システム設定（通常は触らない）
```

---

## 📝 00.daily/ - 日次ノート

**用途**: 日々の振り返り・メモ・学びを記録

**ファイル形式**: `YYYY-MM-DD.md`

**操作**:

- ✍️ 手動作成（VS Code で編集）
- 🤖 AI で整形（GitHub Copilot 等）
- 📖 Obsidian で閲覧

**テンプレート**: `vault/99.system/docs/ai-instructions.md` を参照

**例**:

```
00.daily/
├── 2025-12-13.md
├── 2025-12-14.md
└── 2025-12-15.md
```

---

## 🔍 01.index/ - 自動生成索引

**用途**: データベースから自動生成される索引ノート

**操作**:

- 🚫 手動編集不要（スクリプトが自動生成）
- 📖 Obsidian で閲覧・検索
- 🔗 ブロック参照で原本にジャンプ

**生成されるファイル**:

```
01.index/
├── ideas.md           # アイデア一覧
├── actions.md         # 未処理アクション一覧
└── books/             # 書籍別の学び
    ├── 開発生産性の教科書.md
    └── The_Pragmatic_Programmer.md
```

**生成コマンド**:

```bash
python -m scripts.build_index --vault vault
```

---

## 📰 02.blog/ - ブログ関連

**用途**: ブログ執筆のワークフロー管理

### 02.blog/drafts/ - 下書き

**内容**: AI が生成したブログ下書き（旧 `exports/`）

**操作**:

1. `export_pack.py` で素材を抽出
2. AI に渡してブログ下書き生成
3. `02.blog/drafts/` に保存
4. 編集・推敲
5. `02.blog/published/` に移動

**生成コマンド**:

```bash
python -m scripts.export_pack \
  --vault vault \
  --tag "book:書籍名" \
  --type learning
```

### 02.blog/published/ - 公開済み

**内容**: 公開済みブログ記事（旧 `01.zenn/`）

**操作**:

- Zenn、Qiita、個人ブログ等で公開した記事を保存
- アーカイブとして保管

**例**:

```
02.blog/
├── drafts/
│   └── 20251214_123456_book_開発生産性の教科書.md
└── published/
    └── アーカイブ/
        ├── 2025-09-21-dataskillforqa-idea.md
        └── 2025-09-21-fst-manualexploratorytesting.md
```

---

## ⚙️ 99.system/ - システム設定

**用途**: スクリプトが使用する設定・データ（通常は触らない）

### 99.system/taxonomy/ - タグ辞書

**ファイル**: `tags.yml`

**内容**:

- approved: 承認済みタグリスト
- aliases: タグの別名
- rules: タグ正規化ルール

**編集**:

```bash
vim vault/99.system/taxonomy/tags.yml
python -m scripts.etl --vault vault --full  # 反映
```

### 99.system/db/ - データベース

**ファイル**: `notes.sqlite`

**内容**: 日次ノートから抽出した索引データ

**操作**:

```bash
# リセット
rm vault/99.system/db/notes.sqlite
sqlite3 vault/99.system/db/notes.sqlite < init_db.sql
python -m scripts.etl --vault vault --full
```

### 99.system/logs/ - ログ

**ファイル**: `etl_errors.log`

**内容**: ETL 処理のエラーログ（JSON Lines 形式）

**確認**:

```bash
cat vault/99.system/logs/etl_errors.log | jq
```

### 99.system/docs/ - 設計ドキュメント

**内容**:

- `ai-instructions.md` - AI 向け規約
- `requirements.md` - 要件定義
- `detailed_design.md` - 詳細設計
- `impl_steps.md` - 実装ステップ

---

## 🔄 ワークフロー

### 日次運用

```
1. 00.daily/YYYY-MM-DD.md を作成
   ↓
2. python -m scripts.etl --vault vault
   ↓
3. python -m scripts.build_index --vault vault
   ↓
4. 01.index/*.md で確認（Obsidian）
```

### ブログ化

```
1. python -m scripts.export_pack --tag "book:xxx"
   ↓
2. 02.blog/drafts/*.md が生成される
   ↓
3. AIで下書き作成・編集
   ↓
4. 公開後、02.blog/published/ に移動
```

---

## 🎯 移行履歴

### 変更内容（2025-12-14）

| 旧パス      | 新パス                | 理由                   |
| ----------- | --------------------- | ---------------------- |
| `daily/`    | `00.daily/`           | 番号で整理・検索性向上 |
| `index/`    | `01.index/`           | 番号で整理             |
| `exports/`  | `02.blog/drafts/`     | 用途を明確化           |
| `01.zenn/`  | `02.blog/published/`  | ブログ層の統合         |
| `taxonomy/` | `99.system/taxonomy/` | システム系を隔離       |
| `db/`       | `99.system/db/`       | システム系を隔離       |
| `logs/`     | `99.system/logs/`     | システム系を隔離       |
| `docs/`     | `99.system/docs/`     | システム系を隔離       |

### 影響範囲

✅ **スクリプト**: すべて更新済み
✅ **テスト**: すべて成功（40 tests）
✅ **ドキュメント**: README、QUICKSTART 更新済み

---

## 💡 設計思想

1. **番号接頭辞**: フォルダの並び順を制御し、重要度・利用頻度順に配置
2. **用途の明確化**: `exports` → `02.blog/drafts` で何のためのフォルダか一目瞭然
3. **ブログ層の統合**: 下書きと公開済みを同じ階層に集約
4. **システム隔離**: 設定・DB・ログを `99.system/` に集約し、日常的に触らないようにする
5. **Obsidian 最適化**: 番号付きで自然な並び順、バックリンクも機能

---

## 📚 参考

- [QUICKSTART.md](QUICKSTART.md) - セットアップガイド
- [README.md](README.md) - プロジェクト概要
- [vault/99.system/docs/ai-instructions.md](vault/99.system/docs/ai-instructions.md) - 日次ノート書き方
