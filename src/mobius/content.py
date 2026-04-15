from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from osmium import parse_frontmatter
from markdown import Markdown

from .models import Page

LOGGER = logging.getLogger(__name__)


def discover_markdown_files(content_dir: Path) -> list[Path]:
    return sorted(path for path in content_dir.rglob("*.md") if path.is_file())


def _slug_for(path: Path, content_dir: Path) -> str:
    relative = path.relative_to(content_dir).with_suffix("")
    if relative.name == "index":
        return "index"
    return "/".join(relative.parts)


def _output_path_for(slug: str, output_dir: Path) -> Path:
    if slug == "index":
        return output_dir / "index.html"
    return output_dir / slug / "index.html"


def _title_from_metadata(metadata: dict[str, Any], source_path: Path) -> str:
    title = metadata.get("title")
    if isinstance(title, str) and title.strip():
        return title.strip()
    return source_path.stem.replace("-", " ").title()


def markdown_to_html(text: str) -> str:
    markdown = Markdown(extensions=["fenced_code", "tables", "toc", "codehilite"])
    return markdown.convert(text)


def load_pages(content_dir: Path, output_dir: Path) -> list[Page]:
    pages: list[Page] = []
    for path in discover_markdown_files(content_dir):
        raw_text = path.read_text(encoding="utf-8")
        metadata, body = parse_frontmatter(raw_text)
        slug = _slug_for(path, content_dir)
        output_path = _output_path_for(slug, output_dir)
        title = _title_from_metadata(metadata, path)
        page = Page(
            source_path=path,
            output_path=output_path,
            slug=slug,
            title=title,
            metadata=metadata,
            body=body,
            html=markdown_to_html(body),
        )
        page.url = "/" if slug == "index" else f"/{slug}/"
        pages.append(page)
        LOGGER.debug("Loaded page %s", path)
    return pages


def sort_pages(pages: list[Page]) -> list[Page]:
    def sort_key(page: Page) -> tuple[int, str]:
        order = page.metadata.get("order", 1000)
        try:
            order_value = int(order)
        except (TypeError, ValueError):
            order_value = 1000
        return order_value, page.title.lower()

    return sorted(pages, key=sort_key)
