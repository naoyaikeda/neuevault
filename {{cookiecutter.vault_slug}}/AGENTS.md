# {{ cookiecutter.vault_name }} - Agent Guidelines

このファイルは、AIエージェントが本Obsidian保管庫（Vault）を操作・編集する際の行動指針です。

## Vault概要
- **保管庫名**: {{ cookiecutter.vault_name }}
- **説明**: {{ cookiecutter.vault_description }}

## ディレクトリ構成
- `Daily/`: デイリーノート（日報・日次ログ）
- `Memo/`: 一時メモ・作業メモ・アイデア
- `Archives/`: 完了したタスク・プロジェクトや保管用ノート
- `_templates/`: ノート作成用のテンプレート
- `.obsidian/`: Obsidian設定ファイル（原則として直接編集禁止）

## エージェントの運用ルール
1. **ファイル形式**: Obsidian Flavored Markdown に準拠し、内部リンクには Wikilink 形式（`[[ノート名]]`）を使用してください。
2. **テンプレートの利用**: ノートを新規作成する際は、`_templates/` 配下のテンプレート構造を参考にしてください。
3. **Frontmatter (プロパティ)**: ノート冒頭の YAML Frontmatter（メタデータ）の整合性を保ってください。
4. **破壊的変更の抑止**: 既存の記録やノートの意図しない削除・大幅な改変は避けてください。
