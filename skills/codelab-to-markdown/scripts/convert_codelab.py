#!/usr/bin/env python3
"""
Google Codelab to Markdown Converter
Fetches a Google Codelab (from live URL or local HTML) and converts it to
high-fidelity GitHub-Flavored Markdown with locally downloaded assets.

Features:
- Extracts lab metadata (Title, Authors, Duration, Categories, Original URL).
- Converts all <google-codelab-step> into sequential Markdown headers (## 1. Intro, etc.).
- Normalizes DevSite code blocks with intelligent language detection (bash, json, yaml, python, etc.).
- Converts <aside> callouts into GitHub Flavored Markdown alerts (> [!NOTE], > [!TIP], > [!WARNING]).
- Downloads all content images to a local directory (default: images/) and rewrites relative links.
- Strips DevSite UI chrome, surveys, and navigation widgets.
"""

import os
import sys
import re
import html
import json
import argparse
import urllib.request
import urllib.parse
import ssl
from concurrent.futures import ThreadPoolExecutor, as_completed

# Unverified SSL context to handle environments with proxy/corporate certs
SSL_CONTEXT = ssl._create_unverified_context()

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

SYNTAX_MAP = {
    'python': 'python',
    'py': 'python',
    'bash': 'bash',
    'sh': 'bash',
    'shell': 'bash',
    'zsh': 'bash',
    'json': 'json',
    'yaml': 'yaml',
    'yml': 'yaml',
    'sql': 'sql',
    'transact-sql': 'sql',
    'markdown': 'markdown',
    'md': 'markdown',
    'javascript': 'javascript',
    'js': 'javascript',
    'typescript': 'typescript',
    'ts': 'typescript',
    'html': 'html',
    'xml': 'xml',
    'css': 'css',
    'text only': 'text',
    'text': 'text',
    'scdoc': 'text',
}

BASH_COMMANDS = (
    'mkdir', 'cd', 'ls', 'curl', 'wget', 'gcloud', 'npm', 'pip', 'pip3',
    'python', 'python3', 'git', 'export', 'source', 'docker', 'kubectl',
    'agy', 'cat', 'echo', 'rm', 'cp', 'mv', 'chmod', 'chown', 'brew'
)

def infer_language(code_str, declared_syntax):
    """Refine code block language based on content and declared syntax."""
    s = code_str.strip()
    declared_clean = declared_syntax.lower().strip() if declared_syntax else "text"
    mapped = SYNTAX_MAP.get(declared_clean, declared_clean)

    # Check if JSON
    if s.startswith(('{', '[')):
        try:
            json.loads(s)
            return 'json'
        except Exception:
            pass

    # Check if YAML frontmatter or config
    if s.startswith('---') and ('name:' in s or 'description:' in s or 'apiVersion:' in s):
        return 'yaml'

    # Check if bash commands
    first_word = s.split()[0] if s else ""
    if first_word in BASH_COMMANDS or s.startswith(('$', '#!/bin/bash', '#!/bin/sh', 'lsof', 'grep')):
        return 'bash'

    # Return mapped or text
    return mapped

def clean_html_text(text):
    """Strip tags and unescape html entities."""
    text = re.sub(r'<[^>]+>', '', text)
    return html.unescape(text).strip()

def inline_format_html(text):
    """Convert common inline HTML tags to Markdown."""
    # Replace inline code
    def code_repl(m):
        code_content = html.unescape(m.group(1))
        return f"`{code_content}`"
    text = re.sub(r'<code\b[^>]*>(.*?)</code>', code_repl, text, flags=re.DOTALL)

    # Replace bold
    text = re.sub(r'<(?:strong|b)\b[^>]*>(.*?)</(?:strong|b)>', r'**\1**', text, flags=re.DOTALL)

    # Replace italic
    text = re.sub(r'<(?:em|i)\b[^>]*>(.*?)</(?:em|i)>', r'*\1*', text, flags=re.DOTALL)

    # Replace links
    def link_repl(m):
        href = m.group(1).strip()
        label = html.unescape(m.group(2)).strip()
        if not label:
            label = href
        return f"[{label}]({href})"
    text = re.sub(r'<a\b[^>]*href="([^"]+)"[^>]*>(.*?)</a>', link_repl, text, flags=re.DOTALL)

    # Clean leftover span/div/font tags
    text = re.sub(r'</?(?:span|div|font|var|kbd)[^>]*>', '', text)
    return text

def parse_metadata(html_content, source_url):
    """Extract codelab metadata."""
    title_m = re.search(r'<google-codelab\s+[^>]*title="([^"]+)"', html_content)
    id_m = re.search(r'<google-codelab\s+[^>]*id="([^"]+)"', html_content)
    cat_m = re.search(r'<google-codelab\s+[^>]*category="([^"]+)"', html_content)
    feedback_m = re.search(r'<google-codelab\s+[^>]*feedback-link="([^"]+)"', html_content)

    title = html.unescape(title_m.group(1)) if title_m else ""
    codelab_id = id_m.group(1) if id_m else ""
    categories = cat_m.group(1) if cat_m else ""
    feedback_link = feedback_m.group(1) if feedback_m else ""

    # Check google-codelab-about for authors and last-updated
    about_authors_m = re.search(r'<google-codelab-about\s+[^>]*authors="([^"]+)"', html_content)
    about_updated_m = re.search(r'<google-codelab-about\s+[^>]*last-updated="([^"]+)"', html_content)
    about_title_m = re.search(r'<google-codelab-about\s+[^>]*codelab-title="([^"]+)"', html_content)

    authors = html.unescape(about_authors_m.group(1)) if about_authors_m else ""
    last_updated = about_updated_m.group(1).split('T')[0] if about_updated_m else ""
    if not title and about_title_m:
        title = html.unescape(about_title_m.group(1))

    # Calculate total duration
    durations = re.findall(r'<google-codelab-step\s+[^>]*duration="([^"]+)"', html_content)
    total_minutes = sum(int(d) for d in durations if d.isdigit())

    # Fallback to page <title> if still empty
    if not title:
        head_title = re.search(r'<title>(.*?)</title>', html_content)
        if head_title:
            clean_t = head_title.group(1).split('|')[0].strip()
            if clean_t:
                title = html.unescape(clean_t)

    if not title:
        title = "Google Codelab"

    if codelab_id and (not source_url or source_url.rstrip('/') == 'https://codelabs.developers.google.com'):
        source_url = f"https://codelabs.developers.google.com/{codelab_id}"

    return {
        'title': title,
        'id': codelab_id,
        'authors': authors,
        'last_updated': last_updated,
        'categories': categories,
        'feedback_link': feedback_link,
        'total_duration': total_minutes,
        'source_url': source_url,
    }

def extract_image_urls(html_content, base_url):
    """Find all image URLs in the codelab content, ignoring header lockup and chrome."""
    img_matches = re.findall(r'<img\b[^>]*src="([^"]+)"[^>]*>', html_content)
    urls = []
    for src in img_matches:
        if 'lockup.svg' in src or 'favicon' in src or 'button' in src:
            continue
        full_url = urllib.parse.urljoin(base_url, src)
        urls.append((src, full_url))
    return urls

def download_image(url, target_path):
    """Download single image."""
    try:
        req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
        with urllib.request.urlopen(req, context=SSL_CONTEXT, timeout=20) as resp:
            data = resp.read()
            with open(target_path, 'wb') as f:
                f.write(data)
        return True
    except Exception as e:
        print(f"  [Warning] Failed to download {url}: {e}", file=sys.stderr)
        return False

def download_all_images(img_url_pairs, images_dir):
    """Download all images and return mapping from original src to local relative path."""
    os.makedirs(images_dir, exist_ok=True)
    mapping = {}
    tasks = []

    with ThreadPoolExecutor(max_workers=8) as executor:
        for original_src, full_url in img_url_pairs:
            parsed_path = urllib.parse.urlparse(full_url).path
            filename = os.path.basename(parsed_path)
            if not filename or '.' not in filename:
                filename = f"img_{abs(hash(full_url)):x}.png"

            target_path = os.path.join(images_dir, filename)
            rel_path = f"images/{filename}"
            mapping[original_src] = rel_path

            if not os.path.exists(target_path):
                tasks.append(executor.submit(download_image, full_url, target_path))

        for future in as_completed(tasks):
            future.result()

    return mapping

def convert_table_to_markdown(table_html):
    """Convert HTML table to Markdown table."""
    rows = re.findall(r'<tr\b[^>]*>(.*?)</tr>', table_html, flags=re.DOTALL)
    if not rows:
        return ""

    table_data = []
    for r in rows:
        headers = re.findall(r'<th\b[^>]*>(.*?)</th>', r, flags=re.DOTALL)
        if headers:
            table_data.append([inline_format_html(clean_html_text(c)) for c in headers])
        else:
            cells = re.findall(r'<td\b[^>]*>(.*?)</td>', r, flags=re.DOTALL)
            table_data.append([inline_format_html(clean_html_text(c)) for c in cells])

    if not table_data:
        return ""

    max_cols = max(len(r) for r in table_data)
    for r in table_data:
        while len(r) < max_cols:
            r.append("")

    lines = []
    lines.append("| " + " | ".join(table_data[0]) + " |")
    lines.append("| " + " | ".join(["---"] * max_cols) + " |")
    for r in table_data[1:]:
        lines.append("| " + " | ".join(r) + " |")

    return "\n" + "\n".join(lines) + "\n"

def convert_step_body(body_html, image_map):
    """Convert the HTML body of a single step to Markdown."""
    # Strip codelab-about, credit banner, survey widgets
    body = re.sub(r'<google-codelab-about\b[^>]*>.*?</google-codelab-about>', '', body_html, flags=re.DOTALL)
    body = re.sub(r'<devsite-credits-banner\b[^>]*>.*?</devsite-credits-banner>', '', body, flags=re.DOTALL)
    body = re.sub(r'<devsite-survey\b[^>]*>.*?</devsite-survey>', '', body, flags=re.DOTALL)
    body = re.sub(r'<devsite-thumb-rating\b[^>]*>.*?</devsite-thumb-rating>', '', body, flags=re.DOTALL)

    # 1. Protect & convert code blocks
    code_blocks = []
    def code_repl(m):
        full_tag = m.group(0)
        syntax_m = re.search(r'syntax="([^"]+)"', full_tag, re.IGNORECASE)
        declared_syntax = syntax_m.group(1) if syntax_m else "text"

        code_match = re.search(r'<code\b[^>]*>(.*?)</code>', full_tag, flags=re.DOTALL)
        if code_match:
            raw_code = code_match.group(1)
        else:
            inner = re.sub(r'^<pre[^>]*>', '', full_tag, flags=re.IGNORECASE)
            raw_code = re.sub(r'</pre>$', '', inner, flags=re.IGNORECASE)

        clean_code = re.sub(r'<[^>]+>', '', raw_code)
        unescaped_code = html.unescape(clean_code).rstrip()
        lang = infer_language(unescaped_code, declared_syntax)

        idx = len(code_blocks)
        fence = f"```{lang}\n{unescaped_code}\n```"
        code_blocks.append(fence)
        return f"\n\n__CODE_PLACEHOLDER_{idx}__\n\n"

    body = re.sub(r'<devsite-code>.*?</devsite-code>', code_repl, body, flags=re.DOTALL)
    body = re.sub(r'<pre\b[^>]*>.*?</pre>', code_repl, body, flags=re.DOTALL)

    # 2. Protect & convert tables
    tables = []
    def table_repl(m):
        tbl = m.group(0)
        md_table = convert_table_to_markdown(tbl)
        idx = len(tables)
        tables.append(md_table)
        return f"\n\n__TABLE_PLACEHOLDER_{idx}__\n\n"

    body = re.sub(r'<table\b[^>]*>.*?</table>', table_repl, body, flags=re.DOTALL)

    # 3. Convert asides / callout blocks
    asides = []
    def aside_repl(m):
        full_tag = m.group(0)
        class_m = re.search(r'class="([^"]+)"', full_tag)
        cls = class_m.group(1).lower() if class_m else ""

        alert_type = "NOTE"
        if "warning" in cls:
            alert_type = "WARNING"
        elif "tip" in cls:
            alert_type = "TIP"
        elif "important" in cls:
            alert_type = "IMPORTANT"

        inner_content = re.sub(r'^<aside[^>]*>', '', full_tag, flags=re.IGNORECASE)
        inner_content = re.sub(r'</aside>$', '', inner_content, flags=re.IGNORECASE)
        inner_content = re.sub(r'<div class="aside-header"[^>]*>.*?</div>', '', inner_content, flags=re.DOTALL)

        paras = re.findall(r'<p\b[^>]*>(.*?)</p>', inner_content, flags=re.DOTALL)
        if not paras:
            paras = [inner_content]

        aside_lines = [f"> [!{alert_type}]"]
        for p in paras:
            p_text = clean_html_text(inline_format_html(p))
            if p_text:
                for line in p_text.split('\n'):
                    line_s = line.strip()
                    if line_s:
                        aside_lines.append(f"> {line_s}")

        idx = len(asides)
        asides.append("\n".join(aside_lines))
        return f"\n\n__ASIDE_PLACEHOLDER_{idx}__\n\n"

    body = re.sub(r'<aside\b[^>]*>.*?</aside>', aside_repl, body, flags=re.DOTALL)

    # 4. Images
    def img_repl(m):
        full_tag = m.group(0)
        src_m = re.search(r'src="([^"]+)"', full_tag)
        alt_m = re.search(r'alt="([^"]*)"', full_tag)
        if not src_m:
            return ""
        src = src_m.group(1)
        if 'lockup.svg' in src or 'favicon' in src:
            return ""
        alt = alt_m.group(1) if alt_m else os.path.basename(src)
        local_src = image_map.get(src, src)
        return f"\n\n![{alt}]({local_src})\n\n"

    body = re.sub(r'<img\b[^>]*>', img_repl, body)

    # 5. Headings
    # Remove the top step title (rendered separately)
    body = re.sub(r'<h2\b[^>]*class="step-title"[^>]*>.*?</h2>', '', body, flags=re.DOTALL)

    # Convert upgraded h2 or h3 to ###
    body = re.sub(r'<h2\b[^>]*>(.*?)</h2>', r'\n\n### \1\n\n', body, flags=re.DOTALL)
    body = re.sub(r'<h3\b[^>]*>(.*?)</h3>', r'\n\n### \1\n\n', body, flags=re.DOTALL)
    body = re.sub(r'<h4\b[^>]*>(.*?)</h4>', r'\n\n#### \1\n\n', body, flags=re.DOTALL)

    # 6. Lists
    def list_repl(m):
        list_html = m.group(0)
        is_ol = list_html.startswith('<ol')
        items = re.findall(r'<li\b[^>]*>(.*?)</li>', list_html, flags=re.DOTALL)
        md_items = []
        for i, item in enumerate(items):
            clean_item = clean_html_text(inline_format_html(item))
            prefix = f"{i+1}." if is_ol else "-"
            md_items.append(f"{prefix} {clean_item}")
        return "\n\n" + "\n".join(md_items) + "\n\n"

    body = re.sub(r'<(?:ul|ol)\b[^>]*>.*?</(?:ul|ol)>', list_repl, body, flags=re.DOTALL)

    # 7. Paragraphs
    def p_repl(m):
        p_html = m.group(1)
        clean_p = inline_format_html(p_html).strip()
        clean_p = re.sub(r'<[^>]+>', '', clean_p)
        clean_p = html.unescape(clean_p)
        return f"\n\n{clean_p}\n\n"

    body = re.sub(r'<p\b[^>]*>(.*?)</p>', p_repl, body, flags=re.DOTALL)

    # 8. Clean up stray HTML containers
    body = re.sub(r'</?(?:div|span|section|article|header|footer|button|iframe)[^>]*>', '', body)
    body = inline_format_html(body)

    # 9. Clean multiple blank lines
    blocks = [b.strip() for b in re.split(r'\n{2,}', body) if b.strip()]
    cleaned_body = "\n\n".join(blocks)

    # 10. Restore placeholders
    for idx, cb in enumerate(code_blocks):
        cleaned_body = cleaned_body.replace(f"__CODE_PLACEHOLDER_{idx}__", cb)
    for idx, tb in enumerate(tables):
        cleaned_body = cleaned_body.replace(f"__TABLE_PLACEHOLDER_{idx}__", tb)
    for idx, ab in enumerate(asides):
        cleaned_body = cleaned_body.replace(f"__ASIDE_PLACEHOLDER_{idx}__", ab)

    return cleaned_body

def convert_codelab(source, output_path="lab.md", images_dir=None, base_url="https://codelabs.developers.google.com", skip_images=False):
    """Main conversion pipeline."""
    # 1. Fetch content
    source_url = source if source.startswith(('http://', 'https://')) else ""
    if source_url:
        print(f"Fetching codelab from {source_url}...")
        req = urllib.request.Request(source_url, headers={'User-Agent': USER_AGENT})
        with urllib.request.urlopen(req, context=SSL_CONTEXT, timeout=30) as resp:
            raw_html = resp.read().decode('utf-8', errors='replace')
        base_url = source_url
    else:
        print(f"Reading local HTML file from {source}...")
        with open(source, 'r', encoding='utf-8') as f:
            raw_html = f.read()
        source_url = base_url

    # Output directories
    output_dir = os.path.dirname(os.path.abspath(output_path)) or os.getcwd()
    if not images_dir:
        images_dir = os.path.join(output_dir, "images")

    # 2. Extract metadata
    metadata = parse_metadata(raw_html, source_url)
    print(f"Found codelab: '{metadata['title']}' ({metadata['total_duration']} min total)")

    # 3. Process images
    image_map = {}
    if not skip_images:
        img_pairs = extract_image_urls(raw_html, base_url)
        print(f"Found {len(img_pairs)} content images. Downloading to {images_dir}...")
        image_map = download_all_images(img_pairs, images_dir)
        print(f"Successfully processed {len(image_map)} images.")

    # 4. Extract steps
    step_matches = list(re.finditer(r'<google-codelab-step\s+([^>]+)>(.*?)</google-codelab-step>', raw_html, flags=re.DOTALL))
    print(f"Found {len(step_matches)} steps.")

    md_sections = []
    for i, sm in enumerate(step_matches):
        attrs = sm.group(1)
        body = sm.group(2)
        label_m = re.search(r'label="([^"]+)"', attrs)
        dur_m = re.search(r'duration="([^"]+)"', attrs)

        label = html.unescape(label_m.group(1)) if label_m else f"Step {i+1}"
        duration = dur_m.group(1) if dur_m else "0"

        print(f"  Parsing step {i+1}: '{label}' ({duration} min)...")
        step_body_md = convert_step_body(body, image_map)

        # Header for the step
        step_header = f"## {i+1}. {label}\n"
        if i == 0:
            note = f"> [!NOTE]\n> This lab is based on [{metadata['title']}]({metadata['source_url']}).\n"
            md_sections.append(f"{step_header}\n{note}\n{step_body_md}")
        else:
            md_sections.append(f"{step_header}\n{step_body_md}")

    # 5. Assemble final document without frontmatter sections
    full_markdown = "\n\n---\n\n".join(md_sections) + "\n"

    # Write output
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(full_markdown)

    print(f"\nDone! Markdown saved to {output_path} ({len(full_markdown)} characters).")
    return output_path

def main():
    parser = argparse.ArgumentParser(description="Convert Google Codelab to Markdown")
    parser.add_argument("source", help="Codelab URL or local HTML file")
    parser.add_argument("-o", "--output", default="lab.md", help="Output markdown path (default: lab.md)")
    parser.add_argument("--images-dir", help="Directory for downloaded images (default: ./images)")
    parser.add_argument("--base-url", default="https://codelabs.developers.google.com", help="Base URL for relative assets")
    parser.add_argument("--skip-images", action="store_true", help="Skip downloading images, keep remote URLs")
    args = parser.parse_args()

    convert_codelab(
        source=args.source,
        output_path=args.output,
        images_dir=args.images_dir,
        base_url=args.base_url,
        skip_images=args.skip_images
    )

if __name__ == "__main__":
    main()
