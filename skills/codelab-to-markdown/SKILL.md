---
name: codelab-to-markdown
description: >-
  Converts Google Codelabs (from live URLs or local HTML files) into high-fidelity
  GitHub-Flavored Markdown documents (lab.md or README.md) with locally downloaded
  images, syntax-tagged code fences, GitHub alert callouts, and an original codelab reference note.
---

# Google Codelab to Markdown Converter

This skill provides a complete automated workflow to convert Google Codelabs (`codelabs.developers.google.com`) into structured, clean GitHub-Flavored Markdown (GFM) documents with local media assets.

---

## When to Use This Skill

Activate this skill when:
- Converting a Google Codelab URL (e.g., `https://codelabs.developers.google.com/...`) into a `lab.md` or `README.md`.
- Downloading all media/images referenced in a codelab to a local folder and rewriting image paths to relative links.
- Recreating a codelab format locally while preserving step structure, callouts, and code blocks without unnecessary frontmatter sections.
- Parsing an offline DevSite HTML export into readable Markdown.

---

## Core Components

- **Converter Script**: [`scripts/convert_codelab.py`](./scripts/convert_codelab.py)
  Standalone CLI tool that fetches the codelab, parses DevSite custom HTML elements, downloads images concurrently, normalizes syntax, and generates the markdown document.
- **Format Reference**: [`references/codelab-format.md`](./references/codelab-format.md)
  Specification of DevSite HTML custom elements (`<google-codelab>`, `<google-codelab-step>`, `<devsite-code>`, `<aside>`), syntax tag normalization rules, and heading hierarchy.

---

## Quick Start Workflows

### 1. Convert from a Live URL
To convert a live Google Codelab and save images locally:

```bash
python3 skills/codelab-to-markdown/scripts/convert_codelab.py \
  "https://codelabs.developers.google.com/getting-started-google-antigravity" \
  --output lab.md \
  --images-dir images
```

### 2. Convert from a Local HTML File
If the codelab HTML was already fetched (e.g. via `curl` or saved in `scratch/`):

```bash
python3 skills/codelab-to-markdown/scripts/convert_codelab.py \
  scratch/ref_codelab.html \
  --output lab.md \
  --images-dir images \
  --base-url "https://codelabs.developers.google.com"
```

### 3. Generate README.md in a Specific Target Folder
To create a README in a subfolder (e.g. `docs/`):

```bash
python3 skills/codelab-to-markdown/scripts/convert_codelab.py \
  "https://codelabs.developers.google.com/<slug>" \
  --output docs/README.md \
  --images-dir docs/images
```

---

## CLI Options Reference

| Option | Flag | Default | Description |
| :--- | :--- | :--- | :--- |
| **Source** | positional | *required* | Codelab live HTTPS URL or path to a local `.html` file |
| **Output Path** | `-o`, `--output` | `lab.md` | Target markdown file destination |
| **Images Directory** | `--images-dir` | `./images` | Local directory where images will be downloaded |
| **Base URL** | `--base-url` | `https://codelabs.developers.google.com` | Base URL used to resolve relative `/static/...` assets |
| **Skip Images** | `--skip-images` | `false` | Keeps remote image URLs instead of downloading locally |

---

## Conversion Rules & Behavior

1. **Step Structure & Headings**:
   - Each `<google-codelab-step>` becomes a top-level step header: `## {index}. {Step Title}`.
   - Internal step headings (`<h2 is-upgraded>`, `<h3>`) are down-ranked to `###` to maintain clear document hierarchy.
2. **Reference Note in First Section**:
   - No frontmatter sections or metadata header blocks are generated.
   - At the beginning of the first section (Step 1), a clean note (`> [!NOTE]`) states which codelab the document is based on, linking directly to the original lab URL.
3. **Syntax Tag Normalization**:
   - Fixes common DevSite syntax misattributions (e.g. `Transact-SQL` for JSON, `Text only` or `scdoc` for shell commands).
   - In-content heuristics accurately tag `bash`, `json`, `python`, `yaml`, `javascript`, and `markdown`.
4. **Callouts / Alerts**:
   - DevSite `<aside class="special">` and `<aside class="warning">` elements are converted into GitHub alert syntax:
     - Informational: `> [!NOTE]`
     - Warning: `> [!WARNING]`
5. **Asset Downloading**:
   - Content images (`/static/.../img/...`) are downloaded in parallel using a thread pool.
   - DevSite UI chrome (drawer icons, feedback buttons, logos) is automatically filtered out.
   - Image references in markdown are updated to relative local paths (e.g., `![alt](images/<hash>.<ext>)`).

---

## Verification Checklist

After running the conversion:
- [ ] Verify the output markdown exists and is non-empty (`head -n 25 <output.md>`).
- [ ] Verify total step count matches the original codelab.
- [ ] Verify images are present in the designated `--images-dir` directory.
- [ ] Check code fences to ensure CLI commands are fenced as ```` ```bash ```` and configurations as ```` ```json ```` or ```` ```yaml ````.
- [ ] Verify callouts are rendered as standard `> [!NOTE]` or `> [!WARNING]` blocks.
