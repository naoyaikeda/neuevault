# Neuevault

Neuevault は、Obsidian の保管庫（Vault）をすばやく構築するための Cookiecutter テンプレートです。
日常のノート作成に適したディレクトリ構成や設定に加えて、AI エージェント向けの行動指針（`AGENTS.md`）と必須コミュニティプラグインの自動ダウンロード機能を備えています。

## 主な特徴

- **初期設定済みのディレクトリ構造**
  デイリーノート用の `Daily/`、新規ノート用の `Memo/`、添付ファイルや完了ノート用の `Archives/` があらかじめ設定されています。
- **プラグインの自動セットアップ**
  保管庫の生成時にフックスクリプトが実行され、GitHub Releases から最新版プラグイン（Dataview、Templater、Smart Connections、Smart Lookup）を直接取得して有効化します。
- **AI エージェント運用への配慮**
  リポジトリ内に `AGENTS.md` や `CLAUDE.md` を配置し、AI エージェント（Claude Code 等）が Wikilink や Frontmatter を適切に扱えるよう指針を明記しています。
- **実用的なテンプレート**
  日々の記録に使えるデイリーノート用と、汎用的なメモ用のテンプレートを同梱しています。
- **タグ生成スキルの同梱**
  メモの内容を解析して適切な階層タグ（`tech/python` など）を付与するエージェントスキルおよび自動化スクリプトを同梱しています。

## 前提条件

- Python 3.10 以降
- Cookiecutter（`uvx` や `pipx` を使う場合は事前インストール不要）
- インターネット接続（プラグインのダウンロード時に使用）

## 使い方

端末で以下のコマンドを実行します。

```sh
cookiecutter gh:naoyaikeda/neuevault
```

`uvx` や `pipx` を使うと、Cookiecutter を個別にインストールすることなく直接実行できます。

```sh
# uvx を使う場合
uvx cookiecutter gh:naoyaikeda/neuevault

# pipx を使う場合
pipx run cookiecutter gh:naoyaikeda/neuevault
```

実行すると、保管庫名などの入力を求められます。

```text
vault_name [My Vault]: Personal Notes
vault_slug [personal-notes]:
vault_description [My Obsidian Vault]: 個人の日次ログと技術メモ
author_name [Your Name]: Taro Yamada
```

プロンプト入力が終わると、指定したスラッグ名のフォルダが生成され、プラグインのダウンロードが順次実行されます。
完了したら、Obsidian の「Open folder as vault」から生成されたディレクトリを開いてください。

## 生成されるディレクトリ構成

```text
<vault_slug>/
├── .agents/                 # AI エージェント用リソース
│   └── skills/
│       └── tag-generation/  # メモ用タグ自動生成スキル・スクリプト
├── .gitignore
├── .obsidian/               # Obsidian 設定ファイル
│   ├── app.json             # 添付ファイルや新規ノートの保存先設定
│   ├── community-plugins.json # 有効化プラグイン一覧
│   ├── core-plugins.json
│   ├── daily-notes.json     # デイリーノート設定
│   ├── plugins/             # 自動ダウンロードされたプラグイン
│   └── templates.json       # テンプレートプラグイン設定
├── _templates/              # ノートテンプレート
│   ├── daily.md             # デイリーノート用
│   └── memo.md              # メモ用
├── Archives/                # 添付ファイルおよびアーカイブ保存用
├── Daily/                   # デイリーノート保存用
├── Memo/                    # 新規メモ保存用
├── AGENTS.md                # AI エージェント向け運用ガイドライン
└── CLAUDE.md                # Claude Code 向け設定ファイル（AGENTS.md 参照）
```

## タグ生成スキル（tag-generation）

`Memo/` 配下のノートを解析し、内容に応じたタグ（`tech/python` や `work/project-a` など）を YAML Frontmatter に付与・補正するエージェントスキルを同梱しています。

AI エージェントがノート整理の指針として参照するほか、付属の Python スクリプトで未分類ノートの検出やタグ付けを一括実行できます。

```sh
# 未分類・タグ不足ノートの確認
python .agents/skills/tag-generation/scripts/generate_tags.py --check

# タグ付与結果の事前プレビュー
python .agents/skills/tag-generation/scripts/generate_tags.py --dry-run

# タグを実際に適用
python .agents/skills/tag-generation/scripts/generate_tags.py --apply
```

## 自動インストールされるプラグイン

生成時のフックスクリプトによって、以下のプラグインが `.obsidian/plugins/` 配下に自動でダウンロードされます。

| プラグイン名 | リポジトリ | 用途 |
| :--- | :--- | :--- |
| **Dataview** | `blacksmithgu/obsidian-dataview` | メタデータを利用したクエリ・一覧表示 |
| **Templater** | `SilentVoid13/Templater` | 動的テンプレート作成・挿入 |
| **Smart Connections** | `brianpetro/obsidian-smart-connections` | AI によるノート間の関連性探索・チャット |
| **Smart Lookup** | `brianpetro/smart-lookup-obsidian` | セマンティック検索・情報抽出 |
