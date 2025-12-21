# Obsidian Daily Workflow

AI 経由で日次ノートを整形し、ブログ化・索引化する仕組み。

## ✨ 特徴

- **VS Code + AI で編集**: GitHub Copilot で日次ノートを効率的に作成
- **Obsidian で閲覧・探索**: Dataview で動的索引、バックリンク/グラフで関連発見
- **スクリプト不要**: Obsidian の機能だけで完結
- **シンプルな設計**: Markdown のみ

## 🚀 クイックスタート

### 1. Obsidian で vault フォルダを開く

### 2. Dataview プラグインをインストール

1. 設定 → コミュニティプラグイン → 「制限モードを無効化」
2. 「閲覧」から "Dataview" を検索してインストール
3. 有効化

### 3. Daily Note を作成

`vault/00.daily/YYYY-MM-DD.md` を作成（テンプレートは `Templates/Daily Note Simple.md`）

### 4. インデックスを確認

`vault/01.index/dashboard.md` を開くと、自動的に一覧が表示される

## 📁 プロジェクト構成

```
vault/
  00.daily/          # 日次ノート
    Templates/       # テンプレート
  01.index/          # Dataview による動的索引
    dashboard.md     # ダッシュボード
    learnings.md     # 学び一覧
    ideas.md         # アイデア一覧
    actions.md       # タスク一覧
    experiments.md   # 実験一覧
  02.blog/           # ブログ記事
  03.ideas/          # アイデア詳細
  99.system/         # システム設定・ドキュメント
```

## 🔄 基本ワークフロー

1. **日次ノート作成**: `vault/00.daily/YYYY-MM-DD.md`
2. **セクションに記入**: Learnings / Ideas / Actions / Experiments
3. **Obsidian で閲覧**: `01.index/dashboard.md` で自動集計

## 📝 Daily Note フォーマット

```markdown
---
date: YYYY-MM-DD
---

## Summary

（今日のハイライト）

## Learnings

- 学んだこと #tag1 #tag2

## Ideas

- アイデア #tag

## Actions

- [ ] やること（時間） #tag

## Experiments

（実験の詳細）

## Notes

（自由記述）
```

## 🔌 必要なプラグイン

- **Dataview**（必須）: 動的索引の表示
- **Tasks**（推奨）: タスク管理の強化

## ライセンス

MIT
