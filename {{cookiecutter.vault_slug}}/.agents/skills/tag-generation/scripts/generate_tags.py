#!/usr/bin/env python3
"""
generate_tags.py
Memo/ 配下などの Markdown ノートを走査し、Frontmatter の tags のチェック・補正・自動生成を行うスクリプト。
外部依存なし（Python 標準ライブラリのみ）で動作します。
"""

import argparse
import os
import re
import sys
from pathlib import Path


def parse_frontmatter(content: str) -> tuple[dict | None, str, str]:
    """
    Markdown 本文から YAML Frontmatter を簡易パースします。
    戻り値: (frontmatter_dict, frontmatter_raw_str, body)
    """
    match = re.match(r"^---\s*\r?\n(.*?)\r?\n---\s*\r?\n?(.*)$", content, re.DOTALL)
    if not match:
        return None, "", content

    raw_fm = match.group(1)
    body = match.group(2)
    fm_dict = {}

    # 簡易パース: type, date, tags などを抽出
    current_key = None
    for line in raw_fm.splitlines():
        line = line.rstrip()
        if not line or line.startswith("#"):
            continue

        # リスト項目 (- item)
        list_match = re.match(r"^\s*-\s+(.*)$", line)
        if list_match and current_key:
            val = list_match.group(1).strip().strip("'\"")
            if not isinstance(fm_dict.get(current_key), list):
                fm_dict[current_key] = []
            fm_dict[current_key].append(val)
            continue

        # key: value または key:
        kv_match = re.match(r"^([a-zA-Z0-9_\-]+)\s*:\s*(.*)$", line)
        if kv_match:
            key = kv_match.group(1)
            val = kv_match.group(2).strip()
            current_key = key
            if not val:
                fm_dict[key] = []
            elif val.startswith("[") and val.endswith("]"):
                # インライン配列 [a, b]
                items = [x.strip().strip("'\"") for x in val[1:-1].split(",") if x.strip()]
                fm_dict[key] = items
            else:
                fm_dict[key] = val.strip("'\"")
        else:
            current_key = None

    return fm_dict, raw_fm, body


def update_frontmatter_tags(content: str, new_tags: list[str]) -> str:
    """
    Frontmatter の tags フィールドを更新します。
    Frontmatter がない場合は新規作成します。
    """
    tags_formatted = "\n".join(f"  - {t}" for t in new_tags)
    match = re.match(r"^---\s*\r?\n(.*?)\r?\n---\s*\r?\n?(.*)$", content, re.DOTALL)

    if not match:
        # Frontmatter が存在しない場合は先頭に追加
        header = f"---\ntype: memo\ntags:\n{tags_formatted}\n---\n\n"
        return header + content

    raw_fm = match.group(1)
    body = match.group(2)

    # tags: が既に存在するかチェック
    if re.search(r"^tags\s*:", raw_fm, re.MULTILINE):
        # tags セクション（tags: から次のトップレベルキーまたは末尾まで）を置換
        lines = raw_fm.splitlines()
        new_lines = []
        skip_list = False
        for line in lines:
            if re.match(r"^tags\s*:", line):
                new_lines.append("tags:")
                for t in new_tags:
                    new_lines.append(f"  - {t}")
                skip_list = True
            elif skip_list:
                if re.match(r"^\s+-\s+", line) or re.match(r"^\s*$", line):
                    continue
                else:
                    skip_list = False
                    new_lines.append(line)
            else:
                new_lines.append(line)
        new_fm = "\n".join(new_lines)
    else:
        new_fm = raw_fm.rstrip() + f"\ntags:\n{tags_formatted}"

    return f"---\n{new_fm}\n---\n\n{body.lstrip()}"


def guess_tags_from_text(title: str, text: str) -> list[str]:
    """
    タイトルと本文のキーワードから推奨タグを簡易推定します。
    """
    full_text = f"{title}\n{text}".lower()
    guessed = set()

    # 技術系キーワード
    tech_keywords = {
        "python": "tech/python",
        "javascript": "tech/javascript",
        "typescript": "tech/typescript",
        "docker": "tech/docker",
        "git": "tech/git",
        "obsidian": "tech/obsidian",
        "api": "tech/api",
        "linux": "tech/linux",
        "markdown": "tech/markdown",
    }
    for kw, tag in tech_keywords.items():
        if kw in full_text:
            guessed.add(tag)

    # 属性・カテゴリ系
    if any(k in full_text for k in ["アイデア", "idea", "着想", "思いつき"]):
        guessed.add("idea")
    if any(k in full_text for k in ["tips", "ノウハウ", "設定方法", "使い方", "ハウツー"]):
        guessed.add("tips")
    if any(k in full_text for k in ["会議", "打ち合わせ", "mtg", "議事録", "meeting"]):
        guessed.add("work/meeting")
    if any(k in full_text for k in ["タスク", "todo", "task"]):
        guessed.add("work/task")
    if any(k in full_text for k in ["読書", "書籍", "book", "論文"]):
        guessed.add("reading")

    return sorted(list(guessed))


def scan_notes(target_dir: Path) -> list[dict]:
    """
    対象ディレクトリ内の Markdown ファイルを走査し、タグ状態を調べます。
    """
    results = []
    if not target_dir.exists():
        return results

    for root, _, files in os.walk(target_dir):
        for f in files:
            if not f.endswith(".md"):
                continue
            fp = Path(root) / f
            try:
                content = fp.read_text(encoding="utf-8")
            except Exception as e:
                print(f"Error reading {fp}: {e}", file=sys.stderr)
                continue

            fm, _, body = parse_frontmatter(content)
            tags = []
            if fm and "tags" in fm:
                v = fm["tags"]
                tags = v if isinstance(v, list) else [v]

            # タグ不完全判定: tags なし、または ['memo'] のみ
            is_incomplete = len(tags) == 0 or (len(tags) == 1 and tags[0] == "memo")

            results.append({
                "path": fp,
                "relative_path": fp.relative_to(target_dir.parent if target_dir.parent.exists() else target_dir),
                "tags": tags,
                "is_incomplete": is_incomplete,
                "content": content,
                "body": body,
                "title": f.removesuffix(".md"),
            })

    return results


def main():
    default_vault_dir = Path(__file__).resolve().parents[4]

    parser = argparse.ArgumentParser(description="Scan and generate tags for Obsidian vault notes.")
    parser.add_argument("--vault-dir", type=Path, default=default_vault_dir, help="Vault root directory")
    parser.add_argument("--dir", type=str, default="Memo", help="Subdirectory to scan (relative to vault root)")
    parser.add_argument("--check", action="store_true", help="Only check and list notes with missing/incomplete tags")
    parser.add_argument("--dry-run", action="store_true", help="Preview tag changes without writing")
    parser.add_argument("--apply", action="store_true", help="Apply tag changes to files")
    args = parser.parse_args()

    target_dir = args.vault_dir / args.dir
    if not target_dir.exists():
        print(f"Directory not found: {target_dir}")
        return 1

    notes = scan_notes(target_dir)
    incomplete_notes = [n for n in notes if n["is_incomplete"]]

    print(f"Scanned {len(notes)} note(s) in {target_dir.name}/.")
    print(f"Notes needing tags: {len(incomplete_notes)}\n")

    if args.check or (not args.dry_run and not args.apply):
        for item in incomplete_notes:
            print(f"  [Incomplete] {item['relative_path']} (Current tags: {item['tags']})")
        if incomplete_notes and not args.apply and not args.dry_run:
            print("\nRun with --dry-run or --apply to generate and update tags.")
        return 0

    # タグ生成・適用処理
    updated_count = 0
    for item in incomplete_notes:
        recommended = guess_tags_from_text(item["title"], item["body"])
        new_tags = list(dict.fromkeys(item["tags"] + (["memo"] if "memo" not in item["tags"] else []) + recommended))
        if new_tags == item["tags"]:
            continue

        print(f"{'[DRY RUN] ' if args.dry_run else ''}Updating {item['relative_path']}:")
        print(f"  Current: {item['tags']}")
        print(f"  New:     {new_tags}")

        if args.apply:
            new_content = update_frontmatter_tags(item["content"], new_tags)
            item["path"].write_text(new_content, encoding="utf-8")
            updated_count += 1

    if args.apply:
        print(f"\nSuccessfully updated {updated_count} file(s).")
    elif args.dry_run:
        print(f"\nDry run completed. {len(incomplete_notes)} file(s) would be updated.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
