---
type: idea
stage: idea # idea | design | done
src: [[00.daily/2025-12-16#^20251216-i1]]
owner:
last-updated: 2025-12-16
tags: [idea]
---
# README

<!-- 必要に応じて、このノート内で自由にセクション（見出し）を追加・改名してOK -->

## Summary
- 

## Problem / Why
- 

## Notes
- 関連:
- デイリー: [[00.daily/2025-12-16#^20251216-i1]]

## 設計メモ（必要になったら追記）
- 方針:
- アーキ/フロー:
- データ/I/F:
- 論点・リスク:
- マイルストーン: Draft → Review → Implement → Done

## 決定事項 / TODO
- 決定:
- TODO: [ ]
# Daily Note Templates

Obsidian のデイリーノート機能で使用するテンプレート集です。

## 📝 テンプレートの設計思想

### 🌟 推奨: Daily Note.md（和集合型）

すべての記録タイプに対応した包括的テンプレート。使わないセクションを削除して運用します。

### 📂 用途別テンプレート

最初から特定用途に絞ったシンプルなテンプレート。セクション削除の手間を省きたい場合に。

---

## 📋 テンプレート一覧

### 1. Daily Note.md（包括的・推奨）

すべてのユースケースに対応できる統合テンプレートです。

**含まれるセクション**:

- **Summary** - 今日のハイライト
- **Tasks Today** - タスクリスト（チェックボックス）
- **Reading Notes** - 読書・記事のメモ
- **Ideas** - アイデア記録
- **Experiments** - 技術実験・試行錯誤
- **Key Takeaways (indexed)** - 重要なポイント
- **INDEX** - インデックス化するアイテム（learning/idea/action/experiment）
- **Reflection** - 振り返り・気づき
- **Notes** - 自由記述
- **RAW** - 入力原文・メモ

**運用のコツ**:

1. テンプレートから新規ノート作成
2. その日使わないセクションを削除
3. 使うセクションだけ残して記録

**例**:

- 読書だけした日 → Reading Notes と INDEX（learning）だけ残す
- タスク消化の日 → Tasks Today と Reflection だけ残す
- アイデア出しの日 → Ideas と INDEX（idea）だけ残す

---

### 2. Daily with Reading.md（読書・学習用）

読書や記事のメモに特化したシンプルなテンプレート。

**含まれるセクション**:

- Summary
- Reading Notes（読書メモ）
- Key Takeaways (indexed)
- INDEX（learning 雛形入り）
- Log
- RAW

**用途**:

- 書籍を読んだ日
- 技術記事を読んだ日
- 学習記録

---

### 3. Daily with Action.md（タスク管理用）

タスク管理・アクションプランに特化したテンプレート。

**含まれるセクション**:

- Summary
- Tasks Today（チェックボックス）
- Key Takeaways (indexed)
- INDEX（action 雛形入り）
- Reflection
- RAW

**用途**:

- タスクが多い日
- プロジェクト進行日
- やることリスト

---

### 4. Daily with Experiment.md（技術実験用）

技術検証・実験に特化したテンプレート。

**含まれるセクション**:

- Summary
- Experiments（目的・手順・結果・考察）
- Key Takeaways (indexed)
- INDEX（experiment 雛形入り）
- Notes
- RAW

**用途**:

- 新技術の検証
- ツールの試用
- プロトタイプ開発
- A/B テスト

---

### 5. Daily with Idea.md（アイデア出し用）

アイデア出し・企画に特化したテンプレート。

**含まれるセクション**:

- Summary
- Ideas（背景・概要・効果・次のステップ）
- Key Takeaways (indexed)
- INDEX（idea 雛形入り）
- Reflection
- RAW

**用途**:

- ブレインストーミング
- 企画立案
- 改善案出し
- プロダクトアイデア

---

## 🔧 Obsidian での設定方法

### 1. デイリーノートプラグインの設定

1. Settings → Core plugins → Daily notes を有効化
2. Daily notes 設定を開く
3. 以下を設定:
   - **New file location**: `00.daily`
   - **Template file location**: `00.daily/Templates/Daily Note.md`
   - **Date format**: `YYYY-MM-DD`

### 2. テンプレートプラグインの設定（推奨）

1. Settings → Core plugins → Templates を有効化
2. Templates 設定を開く
3. 以下を設定:
   - **Template folder location**: `00.daily/Templates`
   - **Date format**: `YYYY-MM-DD`
   - **Time format**: `HH:mm`

### 3. 使い方

#### 方法 A: デイリーノート自動作成（推奨）

1. 左サイドバーのカレンダーアイコンをクリック
2. 自動的に今日の日付でノートが作成される
3. 使わないセクションを削除して記録開始

#### 方法 B: 手動でテンプレート挿入

1. `Cmd+N` で新規ノート作成
2. `00.daily/YYYY-MM-DD.md` として保存
3. `Cmd+P` → "Templates: Insert template"
4. Daily Note を選択
5. 使わないセクションを削除

---

## ✍️ Block ID の付け方

テンプレートの `{{date:YYYYMMDD}}` は実際の日付に置き換えられます。

**例**: 2025-12-14 に作成した場合

- `^{{date:YYYYMMDD}}-t1` → `^20251214-t1`
- `^{{date:YYYYMMDD}}-l1` → `^20251214-l1`
- `^{{date:YYYYMMDD}}-a1` → `^20251214-a1`

### Block ID の種類

| kind | 用途               | 例             |
| ---- | ------------------ | -------------- |
| `t`  | takeaway（要点）   | `^20251214-t1` |
| `l`  | learning（学び）   | `^20251214-l1` |
| `e`  | experiment（実験） | `^20251214-e1` |
| `i`  | idea（アイデア）   | `^20251214-i1` |
| `a`  | action（行動）     | `^20251214-a1` |

---

## 🏷️ タグの使い方

### 推奨タグプレフィックス

設定済みのタグ辞書（`vault/99.system/taxonomy/tags.yml`）を参照。

**主要なプレフィックス**:

- `book:` - 書籍名（例: `#book:開発生産性の教科書`）
- `tech:` - 技術（例: `#tech:python`, `#tech:playwright`）
- `topic:` - トピック（例: `#topic:workflow`, `#topic:productivity`）
- `src:` - ソース（例: `#src:work`, `#src:personal`）

### 新しいタグを使いたい場合

- `#new:タグ名` として一時的に使用 OK
- 週次棚卸しで `tags.yml` に追加する

---

## 📋 INDEX セクションの書き方

### learning（学び）

```markdown
- [learning] ![[00.daily/2025-12-14.md#^20251214-t1]] #book:書籍名 #topic:reading ^20251214-l1
```

### idea（アイデア）

```markdown
- [idea] アイデアの短い説明 #topic:workflow ^20251214-i1
```

### action（次にやること）

```markdown
- [action] タスクの説明 effort=30 status=inbox #topic:productivity ^20251214-a1
```

**action のメタデータ**:

- `effort=` : 所要時間（分）- 15, 30, 60, 90 等
- `status=` : 状態 - `inbox`, `doing`, `done`, `dropped`

### experiment（試したこと）

```markdown
- [experiment] 試したことの説明 #tech:技術名 ^20251214-e1
```

---

## 🔗 参考ドキュメント

- [vault/99.system/docs/ai-instructions.md](5.ai-instructions.md) - 詳細な規約
- [vault/99.system/docs/detailed_design.md](2.detailed_design.md) - 設計仕様
- [DIRECTORY_STRUCTURE.md](../../../DIRECTORY_STRUCTURE.md) - ディレクトリ構造ガイド

---

## セクションの削除パターン例

**読書だけの日**:

```markdown
## Summary

今日は『開発生産性の教科書』を読んだ

## Reading Notes

### 📚 開発生産性の教科書 第 3 章

...

## Key Takeaways (indexed)

- プロダクティビティとは... ^20251214-t1

## INDEX

- [learning] ![[00.daily/2025-12-14.md#^20251214-t1]] #book:開発生産性の教科書 ^20251214-l1

## RAW

（メモ）
```

**タスク消化の日**:

```markdown
## Summary

プロジェクトタスクを 3 つ完了

## Tasks Today

- [x] データベース設計
- [x] API 実装
- [ ] テスト作成（明日へ）

## Reflection

データベース設計で悩んだが、正規化の考え方を再確認できた

## INDEX

- [action] テスト作成を完了する effort=60 status=inbox #tech:testing ^20251214-a1
```

**アイデア出しの日**:

```markdown
## Summary

新しいワークフローのアイデアを 3 つ考えた

## Ideas

### 💡 デイリーノートの自動 ETL

毎日のノートを DB に自動登録する仕組み...

## INDEX

- [idea] デイリーノートの自動 ETL 化 #topic:workflow ^20251214-i1

## Notes

既存のスクリプトを改善する方向で検討
```

**技術実験の日**:

```markdown
## Summary

Playwright でのテスト自動化を試した

## Experiments

### 🧪 Playwright E2E テスト導入検証

**目的**: E2E テストの自動化環境構築

**手順**:

1. Playwright インストール
2. サンプルテスト作成
3. CI/CD 連携検証

**結果**:

- 問題なく動作
- 既存の Jest と共存可能

## Key Takeaways (indexed)

- Playwright は簡単にセットアップできる ^20251214-t1
- CI/CD との連携も容易 ^20251214-t2

## INDEX

- [experiment] Playwright E2E テスト導入検証 #tech:playwright #tech:testing ^20251214-e1
- [learning] ![[00.daily/2025-12-14.md#^20251214-t1]] #tech:playwright ^20251214-l1
- [action] 本番環境に Playwright 導入 effort=90 status=inbox #tech:testing ^20251214-a1
```

**読書+アイデアの複合パターン**:

```markdown
## Summary

『エンジニアリング組織論への招待』を読み、チーム改善のアイデアを得た

## Reading Notes

### 📚 エンジニアリング組織論への招待 第 2 章

不確実性のマネジメント...

## Ideas

### 💡 週次振り返り MTG の導入

本で学んだ内容をチームに適用するアイデア...

## Key Takeaways (indexed)

- 不確実性を下げることが重要 ^20251214-t1

## INDEX

- [learning] ![[00.daily/2025-12-14.md#^20251214-t1]] #book:エンジニアリング組織論への招待 ^20251214-l1
- [idea] 週次振り返り MTG の導入 #topic:team-building ^20251214-i1
- [action] MTG フォーマット作成 effort=30 status=inbox #topic:team-building ^20251214-a1
```

**シンプルな振り返りの日**:

```markdown
## Summary

特に何もなかった平穏な一日

## Reflection

最近忙しかったので、今日はゆっくり休めて良かった。
明日からまたタスクに取り組む。

## RAW

体調良好。明日の準備 OK。
```

### テンプレート自体のカスタマイズ

Daily Note.md を直接編集して、自分の好みに合わせることができます。

**よくあるカスタマイズ**:

- 不要なセクションを最初から削除
- セクションの順番を変更
- 新しいセクションを追加（例: Mood, Weather, etc.）
- コメント行を削除してシンプルに
- [experiment] #tech: ^{{date:YYYYMMDD}}-e1

```

### ホットキーの設定

Settings → Hotkeys で以下を設定すると便利:
- "Open today's daily note": `Cmd+Shift+D`
- "Insert template": `Cmd+Shift+T`

### 過去の日付のノート作成

カレンダープラグインを使うと過去の日付のデイリーノートも簡単に作成できます。
```
