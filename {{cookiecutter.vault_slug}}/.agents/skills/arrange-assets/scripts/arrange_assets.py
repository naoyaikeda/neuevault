#!/usr/bin/env python3
"""
arrange_assets.py
Vault 内に散乱している添付ファイル（画像・PDF等）を検出し、
指定または設定された添付ファイルフォルダ（デフォルト: .obsidian/app.json の attachmentFolderPath、または Archives/）へ
安全に集約・移動し、衝突防止リネームおよび Markdown 内のリンク追従更新を一括実行するスクリプト。
外部依存なし（Python 標準ライブラリのみ）で動作します。
"""

import argparse
import filecmp
import json
import os
import re
import shutil
import sys
from pathlib import Path

# 対象とする添付ファイルの拡張子
ATTACHMENT_EXTENSIONS = {
    # 画像
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".svg",
    ".bmp",
    ".ico",
    # ドキュメント
    ".pdf",
    # 音声・動画
    ".mp3",
    ".wav",
    ".m4a",
    ".ogg",
    ".mp4",
    ".webm",
    ".mov",
}

# 走査対象外とするベースディレクトリ名
DEFAULT_EXCLUDED_DIRS = {".obsidian", ".git", ".agents", "_templates"}


def get_default_attachment_folder(vault_dir: Path) -> str:
    """
    .obsidian/app.json から attachmentFolderPath を読み取ります。
    設定されていない場合は 'Archives' をデフォルトとします。
    """
    app_json = vault_dir / ".obsidian" / "app.json"
    if app_json.exists():
        try:
            data = json.loads(app_json.read_text(encoding="utf-8"))
            folder = data.get("attachmentFolderPath")
            if folder and folder.strip():
                # 先頭や末尾のスラッシュを除去して正規化
                return folder.strip().strip("/\\")
        except Exception as e:
            print(f"Warning: Failed to parse {app_json}: {e}", file=sys.stderr)
    return "Archives"


def sanitize_filename(name: str) -> str:
    """
    ファイル名として使えない禁止文字（Windows/Obsidian記法等）を置換・除去します。
    """
    # Windows / Unix / Obsidian の禁則文字: \ / : * ? " < > | # ^ [ ]
    sanitized = re.sub(r'[\\/:*?"<>|#\^\[\]]', "_", name)
    # 連続するアンダースコアや空白を整理
    sanitized = re.sub(r"\s+", " ", sanitized).strip()
    # 先頭・末尾のドットやアンダースコアを除去
    sanitized = sanitized.strip("._ ")
    return sanitized or "note"


def should_rename_collision(
    filename: str, target_dir: Path, referencing_count: int = 1
) -> bool:
    """
    衝突の危険性があるファイル名かどうかを判定します。
    """
    path = Path(filename)
    stem = path.stem
    dest_path = target_dir / filename

    # 1. すでに target_dir 内に同名ファイルが存在する場合
    if dest_path.exists():
        return True

    # 2. 数字のみ（例: 01.png, 1017.jpg, 20260817030204.jpg）
    if stem.isdigit():
        return True

    # 3. 'Image', 'Image 1', 'Image (1)', 'Pasted image 2026...' 等の汎用キャプチャ名
    if re.match(r"^image(\s+\d+|\s*\(\d+\))?$", stem, re.IGNORECASE):
        return True

    # 4. 4文字以下の極端に短い英数字名（単一ノートからのみ参照されている場合）
    if len(stem) <= 4 and re.match(r"^[a-zA-Z0-9_\-]+$", stem):
        if referencing_count <= 1:
            return True

    return False


def find_scattered_assets(vault_dir: Path, excluded_dirs: set[str]) -> list[Path]:
    """
    excluded_dirs 以外の場所に散乱している添付ファイルを再帰走査して検出します。
    """
    assets = []
    for root, dirs, files in os.walk(vault_dir):
        # 走査対象外ディレクトリを除外
        dirs[:] = [
            d
            for d in dirs
            if d not in excluded_dirs and not d.startswith(".")
        ]
        rel_root = Path(root).relative_to(vault_dir)
        if any(part in excluded_dirs for part in rel_root.parts):
            continue

        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in ATTACHMENT_EXTENSIONS:
                assets.append(Path(root) / f)
    return sorted(assets)


def get_all_markdown_files(vault_dir: Path, excluded_dirs: set[str]) -> list[Path]:
    """
    Vault 内のすべての Markdown ファイルを取得します。
    """
    md_files = []
    for root, dirs, files in os.walk(vault_dir):
        dirs[:] = [
            d
            for d in dirs
            if d not in excluded_dirs and not d.startswith(".")
        ]
        rel_root = Path(root).relative_to(vault_dir)
        if any(part in excluded_dirs for part in rel_root.parts):
            continue

        for f in files:
            if f.endswith(".md"):
                md_files.append(Path(root) / f)
    return sorted(md_files)


def update_markdown_links(
    md_file: Path, old_name: str, new_name: str, target_dir_name: str
) -> bool:
    """
    Markdown ファイル内のリンク参照を追従更新します。
    Wikilink、標準 Markdown リンク、YAML Frontmatter などをカバーします。
    """
    try:
        content = md_file.read_text(encoding="utf-8")
    except Exception as e:
        print(f"Error reading {md_file}: {e}", file=sys.stderr)
        return False

    original_content = content
    escaped_old = re.escape(old_name)

    # 1. Obsidian Wikilinks: ![[old_name]] or [[old_name]] (エイリアス |... も保持)
    pattern_wiki = re.compile(
        r"(!?\[\[\s*)(?:[^\]|\r\n]*/)?(" + escaped_old + r")(\s*(?:\|[^\]\r\n]*)?\]\])"
    )
    content = pattern_wiki.sub(r"\g<1>" + new_name + r"\g<3>", content)

    # 2. 標準 Markdown リンク: [alt](.../old_name) or ![alt](.../old_name)
    pattern_md = re.compile(
        r"(!?\[.*?\]\()(?:[^\)\r\n]*/)?(" + escaped_old + r")(\))"
    )
    content = pattern_md.sub(r"\g<1>" + new_name + r"\g<3>", content)

    # 3. リモート画像リンクでローカル名に一致するもの（例: ![alt](https://.../old_name) -> ![[new_name|alt]]）
    pattern_url = re.compile(
        r"!\[(.*?)\]\(https?://[^\)\s\r\n]+/(?:[^/\)\s\r\n]+/)*"
        + escaped_old
        + r"\)"
    )
    content = pattern_url.sub(
        lambda m: f"![[{new_name}|{m.group(1)}]]" if m.group(1) else f"![[{new_name}]]",
        content,
    )

    # 4. YAML Frontmatter の画像参照（image: "old_name", cover: "old_name", etc.）
    pattern_yaml = re.compile(
        r"((?:image|cover|thumbnail|banner):\s*[\"']?(?:\[\[)?)(?:[^\"'\r\n\]]*/)?("
        + escaped_old
        + r")((?:\]\])?[\"']?)"
    )
    content = pattern_yaml.sub(r"\g<1>" + new_name + r"\g<3>", content)

    if content != original_content:
        md_file.write_text(content, encoding="utf-8")
        return True
    return False


def arrange_assets(
    vault_dir: Path,
    target_dir_name: str,
    dry_run: bool = False,
    check_only: bool = False,
) -> int:
    """
    添付ファイルの検出、リネーム、移動、リンク更新を実行します。
    """
    target_dir = vault_dir / target_dir_name
    excluded_dirs = DEFAULT_EXCLUDED_DIRS | {target_dir_name}

    scattered = find_scattered_assets(vault_dir, excluded_dirs)
    print(f"Target attachment folder: {target_dir_name}/")

    if not scattered:
        print("No scattered assets found. Vault is tidy!")
        return 0

    print(f"Found {len(scattered)} scattered asset(s) outside {target_dir_name}/:\n")
    for asset in scattered:
        print(f"  - {asset.relative_to(vault_dir)}")

    if check_only:
        print(
            f"\nRun with --dry-run to preview changes, or --apply to arrange assets into {target_dir_name}/."
        )
        return 0

    if not dry_run:
        target_dir.mkdir(parents=True, exist_ok=True)

    md_files = get_all_markdown_files(vault_dir, excluded_dirs)
    md_cache: dict[Path, str] = {}
    for mf in md_files:
        try:
            md_cache[mf] = mf.read_text(encoding="utf-8")
        except Exception:
            pass

    print(f"\nProcessing {len(scattered)} asset(s)...")
    processed_count = 0
    moved_count = 0

    for asset_path in scattered:
        orig_name = asset_path.name
        dest_file = target_dir / orig_name

        # 1. ターゲットフォルダ内に同一内容のファイルが既に存在する場合は重複除去
        if dest_file.exists():
            if filecmp.cmp(asset_path, dest_file, shallow=False):
                print(
                    f"  [Duplicate] {asset_path.relative_to(vault_dir)} already exists identically in {target_dir_name}/."
                )
                if not dry_run:
                    asset_path.unlink()
                    print("    Removed redundant copy.")
                continue

        # 2. 参照元ノートの探索
        referencing_notes: list[Path] = []
        for mf, txt in md_cache.items():
            if orig_name in txt:
                # Wikilink, 通常リンク, クォート囲みなど
                if (
                    f"[[{orig_name}" in txt
                    or f"]({orig_name})" in txt
                    or f"]({target_dir_name}/{orig_name})" in txt
                    or f'"{orig_name}"' in txt
                    or f"'{orig_name}'" in txt
                    or f"/{orig_name}" in txt
                ):
                    referencing_notes.append(mf)

        # 3. 衝突防止リネームの要否判定
        needs_rename = should_rename_collision(
            orig_name, target_dir, len(referencing_notes)
        )
        if needs_rename:
            if referencing_notes:
                note_stem = sanitize_filename(referencing_notes[0].stem)
                new_name = f"{note_stem}_{orig_name}"
            else:
                new_name = f"unused_{orig_name}"
        else:
            new_name = orig_name

        # 同名衝突回避のための連番付与（もしリネーム後も既存ファイルと被る場合）
        final_dest_file = target_dir / new_name
        counter = 1
        stem = Path(new_name).stem
        suffix = Path(new_name).suffix
        while final_dest_file.exists() and not (
            filecmp.cmp(asset_path, final_dest_file, shallow=False)
        ):
            new_name = f"{stem}_{counter}{suffix}"
            final_dest_file = target_dir / new_name
            counter += 1

        prefix = "[DRY RUN] " if dry_run else ""
        print(
            f"  {prefix}{asset_path.relative_to(vault_dir)} -> {target_dir_name}/{new_name}"
        )

        if not dry_run:
            # 参照元ノートのリンク更新
            updated_notes = 0
            for mf in referencing_notes:
                if update_markdown_links(mf, orig_name, new_name, target_dir_name):
                    updated_notes += 1
                    try:
                        md_cache[mf] = mf.read_text(encoding="utf-8")
                    except Exception:
                        pass
            if updated_notes > 0:
                print(f"    Updated links in {updated_notes} note(s).")

            # ファイル移動
            shutil.move(str(asset_path), str(final_dest_file))
            moved_count += 1

        processed_count += 1

    if dry_run:
        print(f"\nDry run complete. {processed_count} asset(s) would be organized.")
    else:
        print(f"\nSuccessfully arranged {moved_count} asset(s) into {target_dir_name}/.")

        # 検証
        remaining = find_scattered_assets(vault_dir, excluded_dirs)
        if remaining:
            print(
                f"Warning: {len(remaining)} scattered asset(s) still remaining outside {target_dir_name}/.",
                file=sys.stderr,
            )
            return 1
        print("Verification: All assets are neatly gathered in designated folder.")

    return 0


def main() -> int:
    # テンプレート構造における Vault ルートの解決:
    # arrange_assets.py -> scripts -> arrange-assets -> skills -> .agents -> <vault_root> (parents[4])
    default_vault_dir = Path(__file__).resolve().parents[4]

    parser = argparse.ArgumentParser(
        description="Arrange scattered vault assets (images, PDFs, etc.) into designated attachment folder."
    )
    parser.add_argument(
        "--vault-dir",
        type=Path,
        default=default_vault_dir,
        help="Path to the Vault root directory (default: parent directory containing .obsidian)",
    )
    parser.add_argument(
        "--target-dir",
        type=str,
        default=None,
        help="Target folder for attachments (default: read from .obsidian/app.json, or 'Archives')",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check and list scattered assets without moving",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview movements and link updates without modifying files",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Execute movement and link updates",
    )

    args = parser.parse_args()

    vault_dir = args.vault_dir.resolve()
    if not vault_dir.exists():
        print(f"Error: Vault directory not found: {vault_dir}", file=sys.stderr)
        return 1

    target_dir_name = args.target_dir or get_default_attachment_folder(vault_dir)

    # 引数なしで実行された場合はヘルプと検出のみの案内
    check_only = args.check or (not args.dry_run and not args.apply)

    return arrange_assets(
        vault_dir=vault_dir,
        target_dir_name=target_dir_name,
        dry_run=args.dry_run,
        check_only=check_only,
    )


if __name__ == "__main__":
    sys.exit(main())
