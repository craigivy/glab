---
name: markdown-to-codelab
description: >-
  Converts markdown lab documents (lab.md or README.md) into interactive, multi-step
  static websites in Google Codelabs format. Supports drawer navigation,
  progress bars, code copying, callout asides, and outputs to docs/ or custom directory.
---

# Markdown to Google Codelabs Static Site Generator

This skill converts GitHub-Flavored Markdown lab documents (such as `lab.md` or `README.md`) into fully interactive, multi-step static websites styled identically to official Google Codelabs (`codelabs.developers.google.com`).

---

## When to Use This Skill

Activate this skill when:
- Converting a `lab.md` or `README.md` into an interactive Google Codelabs static website.
- Generating documentation into `docs/` ready for GitHub Pages or static web hosting.
- Building a tutorial website with step-by-step drawer navigation, progress bars, and copy-to-clipboard code blocks.
- Transforming markdown callouts (`> [!NOTE]`, `> [!WARNING]`) into styled DevSite aside boxes.

---

## Core Components

- **Site Generator Script**: [`scripts/build_site.py`](./scripts/build_site.py)  
  Standalone Python CLI script that parses Markdown, renders the DevSite layout, copies media assets, and writes `docs/index.html`, `docs/styles.css`, and `docs/app.js`.
- **Template Reference**: [`references/template-guide.md`](./references/template-guide.md)  
  Detailed architecture and reference for the static HTML layout, CSS variables, and client-side JavaScript APIs.

---

## Quick Start Workflows

### 1. Default Conversion (lab.md -> docs/)
To convert `lab.md` in the current workspace and output to `docs/`:

```bash
python3 skills/markdown-to-codelab/scripts/build_site.py
```
*(If `lab.md` is absent, the script automatically falls back to `README.md`).*

### 2. Custom Markdown Input
To specify an explicit input file (e.g. `README.md` or `tutorial.md`):

```bash
python3 skills/markdown-to-codelab/scripts/build_site.py README.md --output-dir docs
```

### 3. Custom Output Directory
To output the static site to a custom destination (e.g. `site/` or `dist/`):

```bash
python3 skills/markdown-to-codelab/scripts/build_site.py lab.md --output-dir site
```

### 4. Overriding Metadata
You can explicitly override metadata such as title or author:

```bash
python3 skills/markdown-to-codelab/scripts/build_site.py lab.md \
  --output-dir docs \
  --title "Custom Codelab Title" \
  --author "Developer Name"
```

---

## CLI Options Reference

| Flag / Argument | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `input` (positional) | string | `lab.md` (or `README.md`) | Input Markdown file path |
| `-i`, `--input-file` | string | `None` | Alternative flag for input file |
| `-o`, `--output-dir` | string | `docs` | Target directory for generated website |
| `--title` | string | Auto-parsed | Overrides the codelab title |
| `--author` | string | Auto-parsed | Overrides the author name in the header card |

---

## Features & Generated Assets

1. **Output Structure in `docs/`**:
   - `docs/index.html`: Complete static HTML containing all steps, drawer navigation, and clean header.
   - `docs/styles.css`: Material & Google Sans styling, light/dark accents, code block themes, callouts.
   - `docs/app.js`: Interactive router, step history (`#0`, `#1`), local storage persistence, step filter, copy buttons.
   - `docs/images/`: Automatically copied images referenced in the markdown document.
2. **Interactive Navigation**:
   - Drawer sidebar with filter box and active step indicators.
   - Back / Next buttons with auto-disabling and step indicator (`Step 1 of N`).
   - Dynamic top progress bar indicating progress across steps.
   - Keyboard navigation using Left / Right arrow keys.
3. **Rich Element Support**:
   - Code blocks with syntax badge and copy-to-clipboard button.
   - GitHub Alerts (`> [!NOTE]`, `> [!WARNING]`, `> [!TIP]`, `> [!IMPORTANT]`) styled as DevSite `<aside>` callouts.
   - Clean tables with responsive overflow containers.
   - Screenshots centered with borders and drop shadows.

---

## Verification Checklist

After generating the site:
- [ ] Verify `docs/index.html`, `docs/styles.css`, and `docs/app.js` exist.
- [ ] Verify images referenced in markdown were copied to `docs/images/`.
- [ ] Check total steps and titles match the markdown headers.
- [ ] Open or serve `docs/index.html` to verify interactive navigation and drawer filtering.
