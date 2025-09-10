#!/usr/bin/env -S uv run -s
# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "markdown-it-py>=3.0.0",
#   "Pygments>=2.18.0",
#   "Pillow>=10.0.0",
# ]
# ///
"""
md2notion_html: Convert Markdown to HTML with code blocks rendered as base64 PNG images.
Usage:
  md2notion_html INPUT.md [-o OUTPUT.html] [--style monokai] [--font "DejaVu Sans Mono"] [--font-size 14] [--line-numbers]

Pipe to clipboard (macOS):
  md2notion_html input.md | pbcopy
Then paste into Notion.
"""
import argparse
import base64
import io
import sys
from pathlib import Path

from markdown_it import MarkdownIt
from markdown_it.renderer import RendererHTML
from markdown_it.token import Token
from pygments import highlight
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.lexers.special import TextLexer
from pygments.formatters.img import ImageFormatter


def make_img_formatter(font: str, font_size: int, style: str, line_numbers: bool) -> ImageFormatter:
    # Transparent background off; white looks better pasted in Notion
    return ImageFormatter(
        font_name=font,
        font_size=font_size,
        style=style,
        line_numbers=line_numbers,
        image_format="PNG",
        line_number_bg="#f7f7f7" if line_numbers else None,
        line_number_fg="#999999" if line_numbers else None,
        line_pad=2,
        hl_color="#fff7cc",  # subtle highlight
    )


def code_to_base64_png(
    code: str, lang: str | None, fmt: ImageFormatter
) -> str:
    if lang:
        try:
            lexer = get_lexer_by_name(lang, stripall=False)
        except Exception:
            lexer = None
    else:
        lexer = None
    if lexer is None:
        try:
            lexer = guess_lexer(code)
        except Exception:
            lexer = TextLexer()

    img_bytes = highlight(code, lexer, fmt)
    if isinstance(img_bytes, bytes):
        data = img_bytes
    else:
        # Some Pygments versions return a BytesIO-like object
        if hasattr(img_bytes, "getvalue"):
            data = img_bytes.getvalue()
        else:
            # Fallback: write through a buffer
            buf = io.BytesIO()
            buf.write(img_bytes)  # type: ignore[arg-type]
            data = buf.getvalue()
    b64 = base64.b64encode(data).decode("ascii")
    return f"data:image/png;base64,{b64}"


class HTMLWithImageCode(RendererHTML):
    def __init__(self, *args, **kwargs):
        self._fmt = kwargs.pop("_img_formatter")
        self._url_exceptions = kwargs.pop("_url_exceptions", [])
        super().__init__(*args, **kwargs)

    def render_fence(self, tokens, idx, options, env):
        tok: Token = tokens[idx]
        lang = (tok.info or "").strip().split()[0] or None
        code = tok.content.strip()
        
        # Check if this is a URL that should be rendered as text instead of image
        if self._is_url_content(code):
            return f'<p><code>{code}</code></p>\n'
        
        src = code_to_base64_png(code, lang, self._fmt)
        alt = (lang or "code")
        # Wrap image to keep it separated and full-width-friendly
        return (
            f'<figure class="code-image">'
            f'<img src="{src}" alt="{alt} code block" loading="lazy" />'
            f'</figure>'
        )

    def render_code_block(self, tokens, idx, options, env):
        # Indented code blocks (no language)
        tok: Token = tokens[idx]
        code = tok.content.strip()
        
        # Check if this is a URL that should be rendered as text instead of image
        if self._is_url_content(code):
            return f'<p><code>{code}</code></p>\n'
            
        src = code_to_base64_png(code, None, self._fmt)
        return (
            f'<figure class="code-image">'
            f'<img src="{src}" alt="code block" loading="lazy" />'
            f'</figure>'
        )
    
    def _is_url_content(self, content):
        """Check if content appears to be a URL or curl command with URL"""
        content = content.strip()
        
        # Check for direct URLs
        if content.startswith(('http://', 'https://', 'ftp://')) and '\n' not in content:
            return True
            
        # Check for curl commands (keep these as images since they're commands)
        if content.startswith('curl '):
            return False
            
        # Check for single line GitHub/raw URLs
        if ('github.com' in content or 'raw.githubusercontent.com' in content) and '\n' not in content:
            return True
            
        return False


def build_md(img_formatter: ImageFormatter, url_exceptions: list = None) -> MarkdownIt:
    md = MarkdownIt("commonmark")
    # Plug our custom renderer for fences and code blocks
    renderer = HTMLWithImageCode(_img_formatter=img_formatter, _url_exceptions=url_exceptions or [])
    md.renderer = renderer
    return md


BASE_CSS = """
/* Minimal sensible defaults for Notion paste */
:root { color-scheme: light; }
body { font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, Noto Sans, Arial, "Apple Color Emoji", "Segoe UI Emoji"; line-height:1.6; font-size:16px; }
h1,h2,h3,h4 { line-height:1.25; margin:1.2em 0 .5em; }
p,ul,ol,pre,figure,table,blockquote { margin: .7em 0; }
code,kbd,samp { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, "DejaVu Sans Mono", Consolas, "Liberation Mono", "Courier New", monospace; }
figure.code-image { display:block; margin: .75em 0; }
figure.code-image > img { max-width: 100%; height: auto; display: block; }
blockquote { padding-left: .9em; border-left: 3px solid #e5e7eb; color:#374151; }
hr { border:0; border-top:1px solid #e5e7eb; margin:1.5em 0; }
table { border-collapse: collapse; width: 100%; }
th, td { border: 1px solid #e5e7eb; padding: .4em .6em; text-align: left; }
a { color: #2563eb; text-decoration: none; }
a:hover { text-decoration: underline; }
"""


def wrap_html(body_html: str, title: str = "Document") -> str:
    return f"""<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <title>{title}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>{BASE_CSS}</style>
  </head>
  <body>
{body_html}
  </body>
</html>
"""


def main():
    ap = argparse.ArgumentParser(description="Render Markdown to HTML with code blocks as base64 PNG images (for Notion paste).")
    ap.add_argument("input", type=Path, help="Input Markdown file")
    ap.add_argument("-o", "--output", type=Path, help="Output HTML file (default: stdout)")
    ap.add_argument("--style", default="default", help="Pygments style (e.g., default, friendly, monokai, github-dark)")
    ap.add_argument("--font", default="DejaVu Sans Mono", help="Monospace font name for code images")
    ap.add_argument("--font-size", type=int, default=14, help="Font size for code images (px)")
    ap.add_argument("--line-numbers", action="store_true", help="Show line numbers in code images")
    args = ap.parse_args()

    src_text = args.input.read_text(encoding="utf-8")

    fmt = make_img_formatter(args.font, args.font_size, args.style, args.line_numbers)
    md = build_md(fmt, [])
    body_html = md.render(src_text)
    full_html = wrap_html(body_html, title=args.input.stem)

    if args.output:
        args.output.write_text(full_html, encoding="utf-8")
    else:
        sys.stdout.write(full_html)


if __name__ == "__main__":
    main()
