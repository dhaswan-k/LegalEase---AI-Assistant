"""Plain-text export."""

from document.formatter import DISCLAIMER, FOOTER_TEXT, sanitize_text, strip_markdown


def generate_txt(text: str) -> bytes:
    """Return clean UTF-8 bytes. Markdown markers are removed; structure is preserved."""
    body = sanitize_text(text)
    lines = []
    for raw in body.split("\n"):
        line = strip_markdown(raw) if raw.strip().startswith("#") or "**" in raw else raw
        lines.append(line)
    out = "\n".join(lines).strip()
    out += f"\n\n{'-' * 60}\n{DISCLAIMER}\n{FOOTER_TEXT}\n"
    return out.encode("utf-8")
