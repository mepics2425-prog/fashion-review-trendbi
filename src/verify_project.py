"""Verify local Markdown/HTML links, SVG XML and static data contracts."""
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import struct
from urllib.parse import unquote, urlsplit
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.ids = set()
        self.stack = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            if attrs["id"] in self.ids:
                raise ValueError(f"Duplicate HTML id: {attrs['id']}")
            self.ids.add(attrs["id"])
        for key in ("href", "src"):
            if key in attrs:
                self.links.append(attrs[key])
        if tag not in {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if not self.stack or self.stack.pop() != tag:
            raise ValueError(f"Unbalanced HTML closing tag: {tag}")


def main() -> None:
    errors = []
    count = 0
    for path in [ROOT / "README.md", *sorted((ROOT / "docs").glob("*.md")), ROOT / "docs/index.html"]:
        text = path.read_text(encoding="utf-8")
        if path.suffix == ".html":
            page = Page()
            page.feed(text)
            if page.stack:
                errors.append(f"Unclosed tags: {page.stack}")
            links, anchors = page.links, page.ids
        else:
            links = re.findall(r"!?\[[^\]]*\]\(([^\s)]+)\)", text)
            links += re.findall(r'<img[^>]+src="([^"]+)"', text)
            anchors = set()
            for heading in re.findall(r"^#{1,6} (.+)$", text, re.M):
                anchors.add(re.sub(r"[^\w\- ]", "", heading.lower()).replace(" ", "-"))
            if text.count("```") % 2:
                errors.append(f"Unclosed Markdown code fence: {path.name}")
        for link in links:
            parsed = urlsplit(link)
            if parsed.scheme or parsed.netloc:
                continue
            count += 1
            if parsed.path:
                if parsed.path.startswith("/"):
                    errors.append(f"Root-relative URL unsafe for project Pages: {link}")
                target = (path.parent / unquote(parsed.path)).resolve()
                if not target.is_relative_to(ROOT) or not target.exists():
                    errors.append(f"Broken local link in {path.name}: {link}")
            elif parsed.fragment and unquote(parsed.fragment) not in anchors:
                errors.append(f"Missing anchor in {path.name}: {link}")
    for svg in (ROOT / "docs/assets").glob("*.svg"):
        ET.parse(svg)
    for png in (ROOT / "docs/assets").glob("*.png"):
        header = png.read_bytes()[:24]
        if len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
            errors.append(f"PNG extension/encoding mismatch: {png.name}")
        elif not all(struct.unpack(">II", header[16:24])):
            errors.append(f"Invalid PNG dimensions: {png.name}")
    data = json.loads((ROOT / "docs/data/demo.json").read_text(encoding="utf-8"))
    if data.get("synthetic") is not True:
        errors.append("Data must declare synthetic=true")
    if errors:
        raise SystemExit("\n".join(errors))
    print(f"PASS: {count} internal references, HTML nesting, Markdown fences/anchors, SVG XML, PNG encoding, synthetic JSON")


if __name__ == "__main__":
    main()
