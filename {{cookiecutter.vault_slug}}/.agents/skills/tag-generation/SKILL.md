---
name: tag-generation
description: Memo/ 配下などの Markdown ノートに対し、内容を解析して YAML Frontmatter の tags を適切に生成・補正・付与するスキル。
---

## 概要と目的

`Memo/` ディレクトリ配下に保存されている作業メモ・アイデア・調査メモ等の Markdown ノートを走査し、タグが未設定または初期値（`memo` のみ）となっているノートに対して、本文内容に応じた適切なカテゴリ・トピックタグを付与・補正します。

## ルール規約

本Vaultの運用ルール（`AGENTS.md`）およびテンプレート（`_templates/memo.md`）に従い、タグは YAML Frontmatter 内の `tags:` フィールドにリスト形式（または配列）で記述します。

```markdown
---
type: memo
date: 2026-11-22
tags:
  - memo
  - tech/python
  - idea
---

# ノートタイトル

## 概要
-

## 詳細
-
```

### タグ命名規則の標準

- **基本タグ**: ノート種別に応じた基本タグ（例: `memo`）を保持します。
- **階層タグ（推奨）**: 大分類と小分類をスラッシュ `/` で繋ぎ、階層的な分類を行います。
  - `tech/python`, `tech/web`, `tech/docker`, `tech/obsidian` など
  - `work/project-a`, `work/meeting`, `work/task` など
  - `study/math`, `study/language` など
- **フラットタグ**: 単一の明確なトピックや属性を表すタグ。
  - `idea` (アイデア・着想)
  - `tips` (Tips・ノウハウ・便利技)
  - `reading` (読書録・文献メモ)
  - `draft` (下書き・執筆中)
- **フォーマット規則**:
  - 半角英小文字、数字、ハイフン `-`、スラッシュ `/` の使用を推奨。
  - 文脈に応じて日本語タグ（例: `議事録`, `レビュー` 等）も許容。
  - タグ内のスペースや特殊記号は避ける。

---

## ワークフロー

### 1. タグ不完全・未設定メモの検出

`Memo/` 配下の Markdown ファイルを走査し、以下のいずれかに該当するファイルを特定します：
1. YAML Frontmatter に `tags:` が存在しない、または空。
2. `tags:` に `memo` のみが指定されており、具体的なカテゴリやトピックタグが付与されていない。

### 2. ノート内容に応じたタグの選定

対象ノートのタイトル、見出し、本文からキーワードやトピックを読み取り、上記「タグ命名規則の標準」に則った適切なタグを選定します。

### 3. タグの適用・更新

1. 既存の Frontmatter を安全に読み取り、`type` や `date` などのメタデータを維持。
2. 選定したタグを既存の `tags:` リストに重複なく追加。
3. YAML Frontmatter を整形して保存。

### 4. 完了検証

タグ付与後のノートを開き、YAML Frontmatter の構文エラーがないこと、および意図したタグが正しく反映されていることを確認します。

---

## 使用方法・実行手順

### AI エージェントによるタグ付け
エージェントがノートを新規作成または整理する際、本スキルのルールおよび `AGENTS.md` に従って Frontmatter の `tags:` を生成・補正します。

### スクリプトによる検出・一括処理

付属の Python スクリプトを実行することで、`Memo/` 配下の未分類ノートの検出やタグ付けを自動化できます。

**未分類・タグ不足ノートの検出（チェックのみ）**:
```bash
python .agents/skills/tag-generation/scripts/generate_tags.py --check
```

**タグ付与の事前プレビュー（Dry Run）**:
```bash
python .agents/skills/tag-generation/scripts/generate_tags.py --dry-run
```

**タグを実際に適用**:
```bash
python .agents/skills/tag-generation/scripts/generate_tags.py --apply
```
