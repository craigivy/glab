# Google Codelabs Static Site Template Guide

This document details the architecture, design components, CSS variables, and JavaScript APIs utilized by the `markdown-to-codelab` site generator.

---

## 1. Directory Structure

The generator produces a standalone, self-contained static website within the destination directory (default `docs/`):

```text
docs/
├── index.html       # Primary HTML document containing all steps, drawer, and headers
├── styles.css       # Complete DevSite & Google Codelabs styles
├── app.js           # Client-side router, progress calculation, drawer filter, copy engine
└── images/          # Locally copied image assets referenced in the markdown
```

---

## 2. HTML Layout Architecture

The page layout consists of four major regions:

1. **Header (`<header class="devsite-header">`)**:
   - Google Codelabs SVG emblem and label
   - Lab title heading (`.header-title`)
   - Top progress bar fill (`#progress-bar-fill`)

2. **Navigation Drawer (`<nav class="devsite-book-nav" id="drawer">`)**:
   - Real-time step filter input (`#step-filter`)
   - Ordered step list (`#step-list`) with `.step-item` elements containing:
     - `.step-number` (circle badge displaying step index)
     - `.step-label` (title of the step)

3. **Content Area (`<main class="codelab-content" id="main-content">`)**:
   - Multi-step container where each step is a `.codelab-step` div (`#step-0`, `#step-1`, etc.)
   - Active step has `.active` class (`display: block`), inactive steps are hidden (`display: none`)
   - Step 1 displays `.codelab-meta-card` containing authors if provided.

4. **Footer Actions (`<footer class="devsite-actions">`)**:
   - Back button (`#btn-prev`) with auto-disable on Step 1
   - Step counter badge (`#step-indicator`: "Step 1 of N")
   - Next / Done button (`#btn-next`)

---

## 3. Supported Markdown Features & DevSite Mapping

| Markdown Element | HTML / DevSite Output | Description |
| :--- | :--- | :--- |
| `## 1. Step Title` | `<div class="codelab-step"> <h2 class="step-title">` | Top-level step delimiter |
| `### Subheading` | `<h3>Subheading</h3>` | Major subsection inside a step |
| ```` ```bash ... ``` ```` | `<devsite-code>` wrapper + `<button class="copy-button">` | Pre-formatted code with syntax banner and copy-to-clipboard |
| `> [!NOTE]` / `> [!TIP]` | `<aside class="special">` | Blue informational callout |
| `> [!WARNING]` / `> [!IMPORTANT]` | `<aside class="special warning">` | Orange/amber warning callout |
| `\| Col 1 \| Col 2 \|` | `<div class="table-container"><table class="devsite-table">` | Responsive styled table |
| `![alt](images/pic.png)` | `<div class="image-container"><img class="devsite-screenshot">` | Centered image with shadow and border |
| `[link](url)` | `<a href="url" target="_blank" rel="noopener">` | Secure external hyperlink |

---

## 4. Client-Side Features (`app.js`)

- **Deep Linking / Routing**: Tracks active step in URL hash (`#0`, `#1`, etc.). Reloading or sharing URLs preserves step state.
- **LocalStorage State Memory**: Remembers last visited step in `localStorage.getItem('codelab_step')`.
- **Keyboard Navigation**:
  - `ArrowRight`: Advances to next step (unless focusing an input)
  - `ArrowLeft`: Returns to previous step
- **Live Search / Filter**: Typing into `#step-filter` dynamically hides non-matching steps in drawer navigation.
- **Progress Tracking**: Top progress bar dynamically scales to `(currentStep / (totalSteps - 1)) * 100%`.
- **Copy-to-Clipboard**: Clickable copy button with "Copied!" checkmark feedback.
