# Google Codelabs Format Reference

This reference document outlines the structural conventions, HTML custom elements, and styling patterns used by Google Codelabs (DevSite). Use this specification when building or extending converters for Google Codelabs.

---

## 1. Top-Level Container & Metadata

Google Codelabs are served within a `<google-codelab>` custom element containing global metadata:

```html
<google-codelab
  title="Getting Started with Google Antigravity"
  id="getting-started-google-antigravity"
  category="antigravity,googleantigravity,developertools"
  feedback-link="https://github.com/..."
  environment="web"
  layout="paginated">
  ...
</google-codelab>
```

### Key Attributes:
- **`title`**: Human-readable title of the codelab.
- **`id`**: URL slug identifier (e.g., `getting-started-google-antigravity`).
- **`category`**: Comma-separated category tags.
- **`feedback-link`**: URL to the GitHub issues or feedback tracker.

### Metadata Component (`<google-codelab-about>`)
Located within Step 1 (Introduction):
```html
<google-codelab-about
  codelab-title="Getting Started with Google Antigravity"
  authors="Romin Irani &amp; Mete Atamel"
  last-updated="2026-10-05T16:35:10Z"
  duration="55">
</google-codelab-about>
```
- **`authors`**: Primary authors / contributors.
- **`last-updated`**: ISO timestamp of the last revision.
- **`duration`**: Total estimated completion time in minutes.

---

## 2. Step Structure (`<google-codelab-step>`)

Each page/step is enclosed in a `<google-codelab-step>` element:

```html
<google-codelab-step label="Installation" duration="10" step="1">
  <h2 class="step-title">2. Installation</h2>
  ...
</google-codelab-step>
```

### Attributes:
- **`label`**: The title displayed in the drawer navigation list.
- **`duration`**: Estimated time for this specific step in minutes.
- **`step`**: 0-based step index (`0` for Step 1, `1` for Step 2, etc.).

### Section Headings Inside Steps:
- Top Step Header: `<h2 class="step-title">` -> Converted to `## {step_number}. {label}`
- Major Subsections: `<h2 is-upgraded>` or `<h3>` -> Converted to `### {title}`
- Sub-subsections: `<h4>` -> Converted to `#### {title}`

---

## 3. Code Blocks & Syntax Tagging

DevSite renders code snippets using either `<devsite-code>` wrapper or direct `<pre>` tags:

```html
<devsite-code>
  <pre class="devsite-click-to-copy" syntax="Python"><code>def my_function():
    pass</code></pre>
</devsite-code>
```

### Syntax Normalization:
DevSite often marks code snippets with generic or mismatched syntax tags (e.g., `Transact-SQL` for JSON, `Text only` or `scdoc` for shell commands). Normalize these tags into standard GitHub fence identifiers:
| DevSite Declared Syntax | Inferred / Output Syntax |
|-------------------------|--------------------------|
| `Python`, `py`          | `python`                 |
| `Text only`, `scdoc` (CLI commands) | `bash` |
| `Transact-SQL` (starts with `{` or `[`) | `json` |
| Starts with `---` (frontmatter) | `yaml` |
| Shell commands (`mkdir`, `gcloud`, `npm`) | `bash` |
| Default / unformatted text | `text` |

---

## 4. Callouts & Asides

Google Codelabs uses `<aside>` elements for callout blocks:

```html
<aside class="special">
  <p>Standard note or informational content.</p>
</aside>

<aside class="warning">
  <p>Critical warnings or important gotchas.</p>
</aside>

<aside class="special tip">
  <p>Helpful shortcuts or best practices.</p>
</aside>
```

### Mapping to GitHub Flavored Markdown (GFM) Alerts:
| Aside CSS Class | GFM Alert Syntax |
|-----------------|------------------|
| `special` (default) | `> [!NOTE]` |
| `warning` / `caution` | `> [!WARNING]` or `> [!IMPORTANT]` |
| `special tip` / `tip` | `> [!TIP]` |
| `important` | `> [!IMPORTANT]` |

---

## 5. Assets & Image Resolution

### URL Patterns:
Content images in DevSite typically use relative root paths:
```html
<img src="/static/getting-started-google-antigravity/img/f02932e53a440101.png" alt="f02932e53a440101.png">
```

### Resolution Rules:
1. **Base Domain**: Resolve relative `/static/...` URLs against `https://codelabs.developers.google.com`.
2. **Local Storage**: Save to `images/<filename>` (e.g., `images/f02932e53a440101.png`).
3. **Filter Chrome**: Exclude DevSite UI assets such as `lockup.svg` (Google Codelabs header logo), navigation button icons, and feedback icons.
4. **Markdown Reference**: Render locally as `![alt](images/<filename>)`.

---

## 6. Chrome Elements to Strip

When converting a Codelab, remove non-content navigational and tracking elements:
- `<google-codelab-about>` (captured in top metadata)
- `<devsite-credits-banner>` (DevSite branding)
- `<devsite-survey>`, `<devsite-thumb-rating>` (Feedback widgets)
- Drawer navigation and next/previous button chrome
- Script tags (`<script>`) and tracking pixels
