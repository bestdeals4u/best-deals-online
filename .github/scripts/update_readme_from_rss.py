import os
from pathlib import Path
import html
import re
import feedparser

RSS_URL = os.getenv("RSS_URL", "").strip()
MAX_ITEMS = int(os.getenv("MAX_ITEMS", "25"))

README_PATH = Path("README.md")

START_MARKER = "<!-- RSS:START -->"
END_MARKER = "<!-- RSS:END -->"


def clean_text(text: str) -> str:
    text = html.unescape(text or "")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def build_section(feed_url: str, max_items: int) -> str:
    feed = feedparser.parse(feed_url)

    items = []
    for entry in feed.entries[:max_items]:
        title = clean_text(getattr(entry, "title", "Untitled"))
        link = getattr(entry, "link", "").strip()
        if not link:
            continue
        items.append(f"- 🔥 [{title}]({link})")

    if not items:
        items = ["- No posts found."]

    lines = [
        "## Latest from BestDeals4U.trade",
        "",
        *items,
        "",
        f"_Auto-updated from RSS feed: {feed_url}_",
    ]
    return "\n".join(lines)


def main() -> None:
    if not RSS_URL:
        raise ValueError("RSS_URL is not set")

    if not README_PATH.exists():
        raise FileNotFoundError("README.md not found")

    readme = README_PATH.read_text(encoding="utf-8")
    new_section = build_section(RSS_URL, MAX_ITEMS)

    replacement = f"{START_MARKER}\n{new_section}\n{END_MARKER}"

    if START_MARKER in readme and END_MARKER in readme:
        pattern = re.compile(
            re.escape(START_MARKER) + r".*?" + re.escape(END_MARKER),
            re.DOTALL,
        )
        updated = pattern.sub(replacement, readme)
    else:
        updated = readme.rstrip() + "\n\n" + replacement + "\n"

    README_PATH.write_text(updated, encoding="utf-8")


if __name__ == "__main__":
    main()
