# Generated with GitHub Copilot - [Tracking ID: Hexure-Copilot]
"""Build a static copy of the web page plus the latest Excel/JSON for GitHub Pages.

Usage:  python build_static.py [output_dir]   (default: site)
"""
import os
import shutil
import sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

import config


def build(out_dir: Path) -> Path:
    if not (config.LATEST_EXCEL.exists() and config.LATEST_JSON.exists()):
        sys.exit("No report found. Run `python run_scraper.py` first.")
    out_dir.mkdir(parents=True, exist_ok=True)

    repo = os.getenv("GITHUB_REPOSITORY")
    repo_url = f"{os.getenv('GITHUB_SERVER_URL', 'https://github.com')}/{repo}" if repo else ""
    env = Environment(loader=FileSystemLoader(config.BASE_DIR / "templates"), autoescape=select_autoescape(["html"]))
    html = env.get_template("index.html").render(
        static=True,
        interval=int(os.getenv("STATIC_INTERVAL_MINUTES", "10")),
        repo_url=repo_url,
    )
    (out_dir / "index.html").write_text(html, encoding="utf-8")
    shutil.copy2(config.LATEST_EXCEL, out_dir / config.LATEST_EXCEL.name)
    shutil.copy2(config.LATEST_JSON, out_dir / config.LATEST_JSON.name)
    (out_dir / ".nojekyll").touch()
    return out_dir


if __name__ == "__main__":
    target = build(Path(sys.argv[1] if len(sys.argv) > 1 else "site"))
    print(f"Static site written to {target.resolve()}")
