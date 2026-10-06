# Generated with GitHub Copilot - [Tracking ID: Hexure-Copilot]
"""Scrape the stores that block GitHub's servers from this PC and push the result to the repo.

The GitHub workflow merges data/local_stores.json into the site. Run every 10 minutes with
Task Scheduler (see install_local_task.ps1).

Usage:  python publish_local.py [--no-push]
"""
import json
import logging
import os
import subprocess
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("ENABLED_STORES", "amazon,reliance_digital")
os.environ["LOCAL_STORES_FILE"] = ""
os.environ["OUTPUT_DIR"] = tempfile.mkdtemp(prefix="phone_local_")

import config  # noqa: E402
from core.service import service  # noqa: E402

TARGET = config.BASE_DIR / "data" / "local_stores.json"


def git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-c", "user.name=home-pc", "-c", "user.email=home-pc@users.noreply.github.com", *args],
        cwd=config.BASE_DIR, capture_output=True, text=True,
    )


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    result = service.run()
    if not result or not result.get("products"):
        print(f"Nothing scraped: {service.last_error}")
        return 1
    previous = json.loads(TARGET.read_text(encoding="utf-8")) if TARGET.exists() else {}
    now = result["generated_at"]
    stores, products = {}, []
    for name, info in result["stores"].items():
        if info["count"]:
            stores[name] = {**info, "scraped_at": now}
            products += [p for p in result["products"] if p["store"] == name]
        elif previous.get("stores", {}).get(name, {}).get("count"):
            # Keep the last good data for a store that is blocked right now; it keeps its own timestamp.
            old = previous["stores"][name]
            stores[name] = {**old, "errors": (info["errors"] + old.get("errors", []))[:10]}
            products += [p for p in previous["products"] if p["store"] == name]
        else:
            stores[name] = {**info, "scraped_at": now}
    payload = {"generated_at": now, "stores": stores, "products": products}
    TARGET.parent.mkdir(exist_ok=True)
    TARGET.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    print({k: v["count"] for k, v in stores.items()})
    if "--no-push" in sys.argv:
        return 0

    pull = git("pull", "--rebase", "--autostash", "-q", "origin", "main")
    if pull.returncode:
        print(pull.stderr)
        return 1
    git("add", str(TARGET.relative_to(config.BASE_DIR)))
    if git("diff", "--cached", "--quiet").returncode == 0:
        return 0
    commit = git("commit", "-q", "-m", "chore(data): update home PC store prices [skip ci]")
    push = git("push", "-q", "origin", "main")
    print(commit.stderr or push.stderr or "pushed")
    return push.returncode


if __name__ == "__main__":
    sys.exit(main())
