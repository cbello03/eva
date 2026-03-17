"""XSS sanitization utilities using bleach."""

import bleach

# Allowed safe tags and attributes for user-generated content.
ALLOWED_TAGS = [
    "a", "abbr", "acronym", "b", "blockquote", "code",
    "em", "i", "li", "ol", "strong", "ul", "p", "br",
    "h1", "h2", "h3", "h4", "h5", "h6", "pre", "span",
]

ALLOWED_ATTRIBUTES: dict[str, list[str]] = {
    "a": ["href", "title", "rel"],
    "abbr": ["title"],
    "acronym": ["title"],
}


def sanitize_html(text: str) -> str:
    """Strip dangerous HTML tags and attributes from *text*.

    Returns a safe string with only whitelisted tags/attributes preserved.
    """
    return bleach.clean(
        text,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        strip=True,
    )
