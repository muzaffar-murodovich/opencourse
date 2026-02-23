import markdown
import bleach

_ALLOWED_TAGS = [
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'p', 'ul', 'ol', 'li', 'br', 'hr',
    'strong', 'em', 'b', 'i',
    'code', 'pre', 'blockquote', 'a',
]

_ALLOWED_ATTRS = {
    'a':    ['href', 'title'],
    'code': ['class'],   # preserves language-* class for Highlight.js
    'pre':  ['class'],
}


def render_markdown(text: str) -> str:
    """Render Markdown to sanitized HTML.

    Supports fenced code blocks (```python … ```).
    Output is stripped of any disallowed tags to prevent XSS.
    """
    if not text:
        return ''
    html = markdown.markdown(text, extensions=['fenced_code'])
    return bleach.clean(
        html,
        tags=_ALLOWED_TAGS,
        attributes=_ALLOWED_ATTRS,
        strip=True,
    )
