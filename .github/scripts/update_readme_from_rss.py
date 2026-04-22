import os
from pathlib import Path
import html
import re
from collections import defaultdict
import feedparser

RSS_URL = os.getenv("RSS_URL", "").strip()
MAX_PER_CATEGORY = int(os.getenv("MAX_PER_CATEGORY", "2"))

README_PATH = Path("README.md")

START_MARKER = "<!-- RSS:START -->"
END_MARKER = "<!-- RSS:END -->"


def clean_text(text: str) -> str:
    text = html.unescape(text or "")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def detect_category(entry) -> str:
    # 1) Prefer RSS/Atom categories if present
    tags = getattr(entry, "tags", []) or []
    for tag in tags:
        term = clean_text(getattr(tag, "term", ""))
        if term:
            return normalize_category(term)

    # 2) Fallback: infer from title
    title = clean_text(getattr(entry, "title", ""))
    return infer_category_from_title(title)


def normalize_category(cat: str) -> str:
    c = cat.lower()

    if "lego" in c:
        return "🧱 LEGO"
    if "pokemon" in c or "pokémon" in c:
        return "🃏 Pokémon Cards"
    if "baseball" in c:
        return "⚾ Baseball Cards"
    if "funko" in c:
        return "🧸 Funko Pops"
    if "video game" in c or "gaming" in c or "game" in c:
        return "🎮 Video Games"

    return f"🔥 {cat.strip()}"


def infer_category_from_title(title: str) -> str:
    t = title.lower()

    if "lego" in t:
        return "🧱 LEGO"
    if "pokemon" in t or "pokémon" in t:
        return "🃏 Pokémon Cards"
    if "baseball" in t:
        return "⚾ Baseball Cards"
    if "funko" in t:
        return "🧸 Funko Pops"
    if "video game" in t or "gaming" in t or "game" in t:
        return "🎮 Video Games"

    return "🔥 Other Finds"


def build_section(feed_url: str, max_per_category: int) -> str:
    feed = feedparser.parse(feed_url)

    grouped = defaultdict(list)

    # feed.entries is already in feed order, usually newest first
    for entry in feed.entries:
        title = clean_text(getattr(entry, "title", "Untitled"))
        link = getattr(entry, "link", "").strip()
        if not link:
            continue

        category = detect_category(entry)

        if len(grouped[category]) < max_per_category:
            grouped[category].append((title, link))

    preferred_order = [
        "⚾ Baseball Cards",
        "🧸 Funko Pops",
        "🧱 LEGO",
        "🃏 Pokémon Cards",
        "🎮 Video Games",
        "🔥 Other Finds",
    ]

    ordered_categories = [c for c in preferred_order if c in grouped]
    ordered_categories += sorted(c for c in grouped if c not in preferred_order)

    lines = ["## Latest from BestDeals4U.trade", ""]

    if not ordered_categories:
        lines.append("- No posts found.")
    else:
        for category in ordered_categories:
            lines.append(f"### {category}")
            for title, link in grouped[category]:
                lines.append(f"- [{title}]({link})")
            lines.append("")

    lines.append(f"_Auto-updated from RSS feed: {feed_url}_")
    return "\n".join(lines)


def main() -> None:
    if not RSS_URL:
        raise ValueError("RSS_URL is not set")

    if not README_PATH.exists():
        raise FileNotFoundError("README.md not found")

    readme = README_PATH.read_text(encoding="utf-8")
    new_section = build_section(RSS_URL, MAX_PER_CATEGORY)

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
