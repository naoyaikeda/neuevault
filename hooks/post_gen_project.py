import json
import urllib.request
from pathlib import Path

# 取得対象: { "プラグインID": "GitHubのowner/repo" }
PLUGINS = {
    "dataview": "blacksmithgu/obsidian-dataview",
    "templater-obsidian": "SilentVoid13/Templater",
    "smart-connections": "brianpetro/obsidian-smart-connections",
    "smart-lookup": "brianpetro/obsidian-smart-lookup",
}

ASSETS = ("main.js", "manifest.json", "styles.css")


def fetch_plugin(plugin_id: str, repo: str, base_dir: Path) -> None:
    plugin_dir = base_dir / plugin_id
    plugin_dir.mkdir(parents=True, exist_ok=True)

    headers = {"User-Agent": "Mozilla/5.0 (Cookiecutter-Neuevault)"}

    for asset in ASSETS:
        url = f"https://github.com/{repo}/releases/latest/download/{asset}"
        dest = plugin_dir / asset
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req) as resp, open(dest, "wb") as f:
                f.write(resp.read())
            print(f"[OK] {plugin_id}: {asset}")
        except Exception:
            # styles.css が存在しないプラグインはスキップ
            if asset != "styles.css":
                print(f"[WARN] {plugin_id}: failed to download {asset}")


def main() -> None:
    plugins_dir = Path(".obsidian/plugins")
    for plugin_id, repo in PLUGINS.items():
        fetch_plugin(plugin_id, repo, plugins_dir)


if __name__ == "__main__":
    main()
