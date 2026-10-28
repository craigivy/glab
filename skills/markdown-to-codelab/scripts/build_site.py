#!/usr/bin/env python3
"""
build_site.py

Converts a GitHub-Flavored Markdown lab/tutorial document (e.g., lab.md or README.md)
into an interactive, responsive static website following the Google Codelabs format
(modeled after https://codelabs.developers.google.com/getting-started-google-antigravity).

Outputs to docs/ by default:
  - docs/index.html
  - docs/styles.css
  - docs/app.js
  - docs/images/ (copied from referenced media assets)
"""

import argparse
import html
import math
import os
import re
import shutil
import sys
from pathlib import Path


# -----------------------------------------------------------------------------
# Embedded Assets: CSS Stylesheet
# -----------------------------------------------------------------------------
DEFAULT_STYLES_CSS = """/* Google Codelabs Theme & Layout Stylesheet */
:root {
  --google-blue: #1a73e8;
  --google-blue-hover: #1557d0;
  --google-blue-light: #e8f0fe;
  --google-blue-surface: #f1f3f4;
  --google-red: #ea4335;
  --google-yellow: #fbbc04;
  --google-green: #34a853;
  --google-grey-50: #f8f9fa;
  --google-grey-100: #f1f3f4;
  --google-grey-200: #e8eaed;
  --google-grey-300: #dadce0;
  --google-grey-400: #bdc1c6;
  --google-grey-500: #9aa0a6;
  --google-grey-600: #80868b;
  --google-grey-700: #5f6368;
  --google-grey-800: #3c4043;
  --google-grey-900: #202124;
  
  --drawer-width: 320px;
  --header-height: 64px;
  --footer-height: 68px;
}

* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  font-family: 'Roboto', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
  color: var(--google-grey-900);
  background-color: #ffffff;
  line-height: 1.6;
  font-size: 15px;
  overflow-x: hidden;
  -webkit-font-smoothing: antialiased;
}

/* Typography */
h1, h2, h3, h4, h5, h6 {
  font-family: 'Google Sans', -apple-system, BlinkMacSystemFont, sans-serif;
  color: var(--google-grey-900);
  font-weight: 500;
  line-height: 1.3;
}

h1 { font-size: 28px; margin-bottom: 20px; }
h2 { font-size: 22px; margin-top: 32px; margin-bottom: 16px; }
h3 { font-size: 18px; margin-top: 24px; margin-bottom: 12px; }
h4 { font-size: 16px; margin-top: 20px; margin-bottom: 8px; }

p {
  margin-bottom: 16px;
  color: var(--google-grey-800);
}

a {
  color: var(--google-blue);
  text-decoration: none;
}

a:hover {
  text-decoration: underline;
}

/* App Header */
.devsite-header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: var(--header-height);
  background: #ffffff;
  border-bottom: 1px solid var(--google-grey-300);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
  overflow: hidden;
}

.codelab-logo {
  display: flex;
  align-items: center;
  gap: 8px;
  text-decoration: none;
  cursor: pointer;
}

.codelab-logo svg {
  height: 24px;
}

.codelab-logo-text {
  font-family: 'Google Sans', sans-serif;
  font-size: 20px;
  color: var(--google-grey-700);
  font-weight: 500;
}

.header-divider {
  width: 1px;
  height: 28px;
  background-color: var(--google-grey-300);
  margin: 0 8px;
}

.header-title {
  font-family: 'Google Sans', sans-serif;
  font-size: 16px;
  font-weight: 500;
  color: var(--google-grey-900);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 600px;
}

/* Progress Bar */
.progress-bar-container {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 4px;
  background-color: var(--google-grey-200);
}

.progress-bar-fill {
  height: 100%;
  background-color: var(--google-blue);
  width: 0%;
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

/* Main Layout */
.codelab-container {
  display: flex;
  margin-top: var(--header-height);
  min-height: calc(100vh - var(--header-height));
}

/* Navigation Drawer */
.devsite-book-nav {
  position: fixed;
  top: var(--header-height);
  bottom: 0;
  left: 0;
  width: var(--drawer-width);
  background-color: #ffffff;
  border-right: 1px solid var(--google-grey-300);
  overflow-y: auto;
  z-index: 900;
  display: flex;
  flex-direction: column;
  transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.drawer-header {
  padding: 16px;
  border-bottom: 1px solid var(--google-grey-200);
}

.filter-box {
  display: flex;
  align-items: center;
  background: var(--google-grey-100);
  border-radius: 8px;
  padding: 6px 12px;
  gap: 8px;
}

.filter-box .material-icons {
  font-size: 20px;
  color: var(--google-grey-600);
}

.filter-box input {
  border: none;
  background: transparent;
  font-size: 14px;
  color: var(--google-grey-900);
  width: 100%;
  outline: none;
}

.step-list {
  list-style: none;
  padding: 8px 0;
  margin: 0;
  flex-grow: 1;
}

.step-item {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  cursor: pointer;
  border-left: 4px solid transparent;
  gap: 12px;
  transition: background-color 0.15s, border-color 0.15s;
  color: var(--google-grey-800);
  text-decoration: none;
}

.step-item:hover {
  background-color: var(--google-grey-100);
}

.step-item.active {
  background-color: var(--google-blue-light);
  border-left-color: var(--google-blue);
  color: var(--google-blue);
  font-weight: 500;
}

.step-number {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--google-grey-200);
  color: var(--google-grey-700);
  font-size: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-weight: 500;
}

.step-item.active .step-number {
  background: var(--google-blue);
  color: #ffffff;
}

.step-item.completed .step-number {
  background: var(--google-green);
  color: #ffffff;
}

.step-label {
  flex-grow: 1;
  font-size: 14px;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Main Content Area */
.codelab-content {
  margin-left: var(--drawer-width);
  flex-grow: 1;
  padding: 40px 64px 120px 64px;
  max-width: 960px;
  width: calc(100% - var(--drawer-width));
}

.codelab-step {
  display: none;
  animation: fadeIn 0.2s ease-in-out;
}

.codelab-step.active {
  display: block;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(4px); }
  to { opacity: 1; transform: translateY(0); }
}

.step-title {
  font-family: 'Google Sans', sans-serif;
  font-size: 32px;
  font-weight: 400;
  color: var(--google-grey-900);
  margin-bottom: 24px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--google-grey-200);
}

/* Metadata Card */
.codelab-meta-card {
  background: var(--google-grey-50);
  border: 1px solid var(--google-grey-300);
  border-radius: 8px;
  padding: 16px 20px;
  margin-bottom: 24px;
  display: flex;
  flex-wrap: wrap;
  gap: 24px;
  font-size: 14px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--google-grey-700);
}

.meta-item strong {
  color: var(--google-grey-900);
}

.meta-item .material-icons {
  font-size: 18px;
  color: var(--google-blue);
}

/* Callouts / Asides */
aside.special {
  margin: 24px 0;
  padding: 16px 20px;
  border-radius: 0 8px 8px 0;
  border-left: 4px solid var(--google-blue);
  background-color: var(--google-blue-light);
  color: var(--google-grey-900);
}

aside.special .aside-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  font-family: 'Google Sans', sans-serif;
  font-size: 15px;
  color: #174ea6;
}

aside.special .aside-header .material-icons {
  font-size: 20px;
}

aside.special p {
  margin-bottom: 8px;
  color: #1a237e;
}

aside.special p:last-child {
  margin-bottom: 0;
}

aside.special.warning, aside.warning {
  border-left-color: #ea8600;
  background-color: #fef7e0;
}

aside.special.warning .aside-header, aside.warning .aside-header {
  color: #b06000;
}

aside.special.warning p, aside.warning p {
  color: #5c3b00;
}

aside.special.tip {
  border-left-color: #1e8e3e;
  background-color: #e6f4ea;
}

aside.special.tip .aside-header {
  color: #137333;
}

aside.special.tip p {
  color: #0d5322;
}

/* Code Blocks */
devsite-code {
  display: block;
  margin: 20px 0;
  border-radius: 8px;
  background-color: #292a2d;
  color: #e8eaed;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0,0,0,0.12);
}

.code-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 16px;
  background-color: #202124;
  border-bottom: 1px solid #3c4043;
  font-family: 'Roboto Mono', monospace;
  font-size: 12px;
  color: #9aa0a6;
  text-transform: uppercase;
}

.copy-button {
  background: transparent;
  border: none;
  color: #bdc1c6;
  font-size: 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px;
  border-radius: 4px;
  transition: background-color 0.2s, color 0.2s;
  font-family: 'Google Sans', sans-serif;
  text-transform: none;
}

.copy-button:hover {
  background-color: rgba(255,255,255,0.1);
  color: #ffffff;
}

.copy-button .material-icons {
  font-size: 16px;
}

pre.devsite-click-to-copy {
  margin: 0;
  padding: 16px 20px;
  overflow-x: auto;
  font-family: 'Roboto Mono', Consolas, Monaco, monospace;
  font-size: 13.5px;
  line-height: 1.5;
  color: #e8eaed;
}

code {
  font-family: 'Roboto Mono', Consolas, Monaco, monospace;
}

p code, li code {
  background-color: var(--google-grey-100);
  color: #c5221f;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 13.5px;
}

/* Lists */
.devsite-list {
  margin: 16px 0 20px 24px;
}

.devsite-list li {
  margin-bottom: 8px;
  color: var(--google-grey-800);
}

/* Images */
.image-container {
  display: flex;
  justify-content: center;
  margin: 28px 0;
}

.image-container img {
  max-width: 100%;
  height: auto;
  border-radius: 8px;
  box-shadow: 0 2px 6px rgba(60,64,67,0.15);
  border: 1px solid var(--google-grey-200);
}

/* Tables */
.table-container {
  overflow-x: auto;
  margin: 24px 0;
}

.devsite-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.devsite-table th, .devsite-table td {
  padding: 12px 16px;
  border: 1px solid var(--google-grey-300);
  text-align: left;
}

.devsite-table th {
  background-color: var(--google-grey-100);
  font-weight: 500;
  color: var(--google-grey-900);
}

.devsite-table tr:nth-child(even) td {
  background-color: var(--google-grey-50);
}

/* Footer Navigation Bar */
.devsite-actions {
  position: fixed;
  bottom: 0;
  left: var(--drawer-width);
  right: 0;
  height: var(--footer-height);
  background-color: #ffffff;
  border-top: 1px solid var(--google-grey-300);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 48px;
  z-index: 850;
  box-shadow: 0 -2px 6px rgba(0,0,0,0.03);
}

.btn-nav {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-family: 'Google Sans', sans-serif;
  font-size: 14px;
  font-weight: 500;
  padding: 10px 24px;
  border-radius: 20px;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid transparent;
}

.btn-back {
  background-color: #ffffff;
  border-color: var(--google-grey-400);
  color: var(--google-grey-700);
}

.btn-back:hover:not(:disabled) {
  background-color: var(--google-grey-100);
  color: var(--google-grey-900);
}

.btn-back:disabled {
  opacity: 0.4;
  cursor: not-allowed;
  border-color: var(--google-grey-300);
}

.step-indicator {
  font-size: 14px;
  color: var(--google-grey-700);
  font-weight: 500;
}

.btn-next {
  background-color: var(--google-blue);
  color: #ffffff;
}

.btn-next:hover {
  background-color: var(--google-blue-hover);
  box-shadow: 0 1px 3px rgba(60,64,67,0.3);
}

/* Backdrop for Mobile Drawer */
.drawer-backdrop {
  display: none;
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0,0,0,0.4);
  z-index: 890;
}

/* Responsive adjustments */
@media (max-width: 900px) {
  .devsite-book-nav {
    transform: translateX(-100%);
  }
  
  .devsite-book-nav.open {
    transform: translateX(0);
  }
  
  .drawer-backdrop.open {
    display: block;
  }
  
  .codelab-content {
    margin-left: 0;
    width: 100%;
    padding: 24px 20px 100px 20px;
  }
  
  .devsite-actions {
    left: 0;
    padding: 0 16px;
  }

  .header-title {
    max-width: 240px;
  }
}
"""

# -----------------------------------------------------------------------------
# Embedded Assets: JavaScript App
# -----------------------------------------------------------------------------
DEFAULT_APP_JS_TEMPLATE = """/**
 * Google Codelabs Interactive Behavior
 * Controls step navigation, progress tracking, drawer filtering, and copy-to-clipboard.
 */

(function () {
  'use strict';

  // DOM Elements
  const stepList = document.getElementById('step-list');
  const stepElements = document.querySelectorAll('.codelab-step');
  const TOTAL_STEPS = stepElements.length;
  let currentStep = 0;

  const prevBtn = document.getElementById('btn-prev');
  const nextBtn = document.getElementById('btn-next');
  const stepIndicator = document.getElementById('step-indicator');
  const progressBarFill = document.getElementById('progress-bar-fill');
  const filterInput = document.getElementById('step-filter');
  const drawer = document.getElementById('drawer');
  const backdrop = document.getElementById('drawer-backdrop');

  /**
   * Initializes the codelab state from URL hash or localStorage.
   */
  function init() {
    let initialStep = 0;
    
    // Check URL hash (e.g. #0, #1, ..., #7)
    const hash = window.location.hash.replace('#', '');
    const parsedHash = parseInt(hash, 10);
    if (!isNaN(parsedHash) && parsedHash >= 0 && parsedHash < TOTAL_STEPS) {
      initialStep = parsedHash;
    } else {
      // Check localStorage
      try {
        const saved = localStorage.getItem('codelab_step');
        const parsedSaved = parseInt(saved, 10);
        if (!isNaN(parsedSaved) && parsedSaved >= 0 && parsedSaved < TOTAL_STEPS) {
          initialStep = parsedSaved;
        }
      } catch (e) {}
    }

    setupEventListeners();
    goToStep(initialStep, false);
  }

  /**
   * Renders the specified step.
   * @param {number} stepIndex - Index of the step (0-based).
   * @param {boolean} smoothScroll - Whether to smoothly scroll to top.
   */
  function goToStep(stepIndex, smoothScroll = true) {
    if (stepIndex < 0 || stepIndex >= TOTAL_STEPS) return;

    currentStep = stepIndex;

    // 1. Show only active step content
    stepElements.forEach((el, idx) => {
      if (idx === currentStep) {
        el.classList.add('active');
      } else {
        el.classList.remove('active');
      }
    });

    // 2. Update navigation drawer items
    const stepItems = document.querySelectorAll('.step-item');
    stepItems.forEach((item, idx) => {
      item.classList.remove('active', 'completed');
      if (idx === currentStep) {
        item.classList.add('active');
        item.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
      } else if (idx < currentStep) {
        item.classList.add('completed');
      }
    });

    // 3. Update Progress Bar
    const progressPercent = TOTAL_STEPS > 1 ? (currentStep / (TOTAL_STEPS - 1)) * 100 : 100;
    if (progressBarFill) {
      progressBarFill.style.width = `${progressPercent}%`;
    }

    // 4. Update Footer Action Buttons
    if (prevBtn) {
      prevBtn.disabled = currentStep === 0;
    }
    if (nextBtn) {
      const labelSpan = nextBtn.querySelector('.btn-label') || nextBtn;
      if (currentStep === TOTAL_STEPS - 1) {
        labelSpan.textContent = 'Done';
      } else {
        labelSpan.textContent = 'Next';
      }
    }
    if (stepIndicator) {
      stepIndicator.textContent = `Step ${currentStep + 1} of ${TOTAL_STEPS}`;
    }

    // 5. Update URL Hash and LocalStorage
    window.location.hash = `#${currentStep}`;
    try {
      localStorage.setItem('codelab_step', currentStep.toString());
    } catch (e) {}

    // 6. Scroll main content to top
    if (smoothScroll) {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    // 7. Close mobile drawer if open
    closeDrawer();
  }

  /**
   * Sets up interactive event listeners.
   */
  function setupEventListeners() {
    // Drawer step clicks
    if (stepList) {
      stepList.addEventListener('click', (e) => {
        const item = e.target.closest('.step-item');
        if (item) {
          e.preventDefault();
          const stepIndex = parseInt(item.getAttribute('data-step'), 10);
          if (!isNaN(stepIndex)) {
            goToStep(stepIndex);
          }
        }
      });
    }

    // Prev / Next button clicks
    if (prevBtn) {
      prevBtn.addEventListener('click', () => {
        if (currentStep > 0) {
          goToStep(currentStep - 1);
        }
      });
    }

    if (nextBtn) {
      nextBtn.addEventListener('click', () => {
        if (currentStep < TOTAL_STEPS - 1) {
          goToStep(currentStep + 1);
        } else {
          goToStep(TOTAL_STEPS - 1);
          window.scrollTo({ top: 0, behavior: 'smooth' });
        }
      });
    }

    // Hash change in browser (Back / Forward buttons)
    window.addEventListener('hashchange', () => {
      const hash = window.location.hash.replace('#', '');
      const stepIndex = parseInt(hash, 10);
      if (!isNaN(stepIndex) && stepIndex >= 0 && stepIndex < TOTAL_STEPS && stepIndex !== currentStep) {
        goToStep(stepIndex, false);
      }
    });

    // Keyboard navigation (ArrowLeft / ArrowRight)
    window.addEventListener('keydown', (e) => {
      if (['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName)) return;
      if (e.key === 'ArrowRight' && currentStep < TOTAL_STEPS - 1) {
        goToStep(currentStep + 1);
      } else if (e.key === 'ArrowLeft' && currentStep > 0) {
        goToStep(currentStep - 1);
      }
    });

    // Filter input
    if (filterInput) {
      filterInput.addEventListener('input', (e) => {
        const query = e.target.value.toLowerCase().trim();
        const items = document.querySelectorAll('.step-item');
        items.forEach((item) => {
          const label = item.querySelector('.step-label');
          const text = label ? label.textContent.toLowerCase() : '';
          if (!query || text.includes(query)) {
            item.style.display = 'flex';
          } else {
            item.style.display = 'none';
          }
        });
      });
    }

    if (backdrop) {
      backdrop.addEventListener('click', closeDrawer);
    }
  }

  function toggleDrawer() {
    if (drawer) drawer.classList.toggle('open');
    if (backdrop) backdrop.classList.toggle('open');
  }

  function closeDrawer() {
    if (drawer) drawer.classList.remove('open');
    if (backdrop) backdrop.classList.remove('open');
  }

  /**
   * Code snippet copy button handler.
   */
  window.copyCode = function (button) {
    const codeBlock = button.closest('devsite-code');
    if (!codeBlock) return;
    const codeEl = codeBlock.querySelector('code') || codeBlock.querySelector('pre');
    if (!codeEl) return;
    
    const textToCopy = codeEl.innerText;
    navigator.clipboard.writeText(textToCopy).then(() => {
      const icon = button.querySelector('.material-icons');
      const text = button.querySelector('.copy-text');
      const originalText = text ? text.textContent : 'Copy';
      const originalIcon = icon ? icon.textContent : 'content_copy';

      if (icon) icon.textContent = 'check';
      if (text) text.textContent = 'Copied!';
      button.classList.add('copied');

      setTimeout(() => {
        if (icon) icon.textContent = originalIcon;
        if (text) text.textContent = originalText;
        button.classList.remove('copied');
      }, 2000);
    }).catch((err) => {
      console.error('Failed to copy to clipboard:', err);
    });
  };

  // Run on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
"""


# -----------------------------------------------------------------------------
# Markdown Parser & HTML Generator
# -----------------------------------------------------------------------------

def escape_html(text: str) -> str:
    return html.escape(text)


def inline_format(text: str) -> str:
    """Formats inline Markdown: code, links, bold, italic, strikethrough."""
    # 1. Protect inline code first so inner underscores/asterisks are never corrupted
    inline_codes = []
    def code_repl(m):
        idx = len(inline_codes)
        inline_codes.append(f'<code translate="no" dir="ltr">{escape_html(m.group(1))}</code>')
        return f"@@@INLINECODEPH{idx}@@@"
    text = re.sub(r'`([^`]+)`', code_repl, text)

    # Strikethrough: ~~text~~
    text = re.sub(r'~~(.*?)~~', r'<del>\1</del>', text)

    # Links: [text](url)
    text = re.sub(
        r'\[(.*?)\]\((https?://[^\s)]+)\)',
        r'<a href="\2" target="_blank" rel="noopener">\1</a>',
        text
    )

    # Relative internal links [text](#step-2)
    text = re.sub(
        r'\[(.*?)\]\((#[^\s)]+)\)',
        r'<a href="\2">\1</a>',
        text
    )

    # Bold: **text** or __text__
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'__(.*?)__', r'<strong>\1</strong>', text)

    # Italic: *text* or _text_ (excluding double asterisks or word internal)
    text = re.sub(r'(?<!\*)\*(?!\*)([^\*]+)\*(?!\*)', r'<em>\1</em>', text)
    text = re.sub(r'(?:^|(?<=[\s(]))_([^_]+)_(?=[\s).,;:!?]|$)', r'<em>\1</em>', text)

    # Restore inline code
    for idx, ic in enumerate(inline_codes):
        text = text.replace(f"@@@INLINECODEPH{idx}@@@", ic)

    return text


def render_code_block_html(lang: str, code: str) -> str:
    """Renders a code block into Google Codelabs devsite-code component."""
    lang = lang.strip() or "bash"
    code = code.rstrip("\n")
    escaped_code = escape_html(code)
    return f'''<devsite-code>
  <div class="code-header">
    <span class="code-lang">{escape_html(lang)}</span>
    <button class="copy-button" onclick="copyCode(this)" aria-label="Copy code">
      <span class="material-icons">content_copy</span>
      <span class="copy-text">Copy</span>
    </button>
  </div>
  <pre class="devsite-click-to-copy" syntax="{escape_html(lang)}"><code class="language-{escape_html(lang)}">{escaped_code}</code></pre>
</devsite-code>'''


def parse_markdown_to_html(md_text: str, source_dir: Path, output_images_dir: Path) -> str:
    """
    Parses a single step's Markdown content into Google Codelabs HTML.
    Protects alerts/asides, code blocks, tables, then handles lists, headings,
    images, and paragraphs.
    """
    # Step 1: Protect alerts / asides (both GFM > [!NOTE] and DevSite style)
    # Processed first so code blocks inside alerts have leading '>' prefixes cleanly removed.
    alert_blocks = []
    def alert_repl(m):
        atype = m.group(1).upper()
        content = m.group(2)
        lines = [re.sub(r'^[ \t]*>[ \t]?', '', l) for l in content.split("\n")]
        body_md = "\n".join(lines).strip()

        icon = "info"
        title = "Note"
        css_class = "special"
        if atype in ("IMPORTANT", "CAUTION"):
            icon = "error_outline"
            title = "Important"
            css_class = "special warning"
        elif atype == "WARNING":
            icon = "warning"
            title = "Warning"
            css_class = "warning"
        elif atype == "TIP":
            icon = "lightbulb"
            title = "Tip"
            css_class = "special tip"

        # Extract code blocks inside the alert body
        inner_code_blocks = []
        def inner_code_repl(cm):
            c_lang = cm.group(1).strip() or "bash"
            c_code = cm.group(2)
            idx = len(inner_code_blocks)
            inner_code_blocks.append(render_code_block_html(c_lang, c_code))
            return f"\n\n<!--INNER_CODE_{idx}-->\n\n"

        body_md_masked = re.sub(r'```([a-zA-Z0-9_-]*)\n(.*?)```', inner_code_repl, body_md, flags=re.DOTALL)

        formatted_parts = []
        for p in body_md_masked.split("\n\n"):
            p = p.strip()
            if not p:
                continue
            if p.startswith("<!--INNER_CODE_"):
                formatted_parts.append(p)
            else:
                formatted_parts.append(f'<p>{inline_format(p)}</p>')

        body_html = "\n  ".join(formatted_parts)
        for c_idx, c_html in enumerate(inner_code_blocks):
            body_html = body_html.replace(f"<!--INNER_CODE_{c_idx}-->", c_html)

        block_html = f'''<aside class="{css_class}">
  <div class="aside-header"><span class="material-icons">{icon}</span><strong>{title}:</strong></div>
  {body_html}
</aside>'''
        idx = len(alert_blocks)
        alert_blocks.append(block_html)
        return f"\n\n<!--ALERT_BLOCK_{idx}-->\n\n"

    text = re.sub(
        r'(?m)^[ \t]*>[ \t]*\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\][ \t]*\n((?:[ \t]*>.*(?:\n|$))+)',
        alert_repl,
        md_text
    )

    # Step 2: Protect code blocks outside alerts
    code_blocks = []
    def code_repl(m):
        lang = m.group(1).strip() or "bash"
        code = m.group(2)
        idx = len(code_blocks)
        block_html = render_code_block_html(lang, code)
        code_blocks.append(block_html)
        return f"\n\n<!--CODE_BLOCK_{idx}-->\n\n"

    text = re.sub(r'```([a-zA-Z0-9_-]*)\n(.*?)```', code_repl, text, flags=re.DOTALL)

    # Step 3: Protect tables
    table_blocks = []
    def table_repl(m):
        table_raw = m.group(0).strip()
        lines = [l.strip() for l in table_raw.split("\n") if l.strip()]
        if len(lines) >= 2 and "|" in lines[0] and re.match(r'^\s*\|?\s*[-:| ]+\|\s*$', lines[1]):
            headers = [c.strip() for c in lines[0].strip("|").split("|")]
            rows = []
            for r in lines[2:]:
                cells = [c.strip() for c in r.strip("|").split("|")]
                rows.append(cells)

            t_html = ['<div class="table-container"><table class="devsite-table"><thead><tr>']
            for h in headers:
                t_html.append(f'<th>{inline_format(h)}</th>')
            t_html.append('</tr></thead><tbody>')
            for r in rows:
                t_html.append('<tr>')
                for c in r:
                    t_html.append(f'<td>{inline_format(c)}</td>')
                t_html.append('</tr>')
            t_html.append('</tbody></table></div>')
            idx = len(table_blocks)
            table_blocks.append("".join(t_html))
            return f"\n\n<!--TABLE_BLOCK_{idx}-->\n\n"
        return table_raw

    table_pattern = r'(?m)^[ \t]*\|[^\n]+\|[ \t]*\n[ \t]*\|[ \t]*:?[-]+:?[ \t]*(?:\|[ \t]*:?[-]+:?[ \t]*)+\|[ \t]*(?:\n[ \t]*\|[^\n]+\|[ \t]*)+'
    text = re.sub(table_pattern, table_repl, text)

    # Step 4: Images ![alt](src)
    def img_repl(m):
        alt_text = m.group(1).strip()
        src = m.group(2).strip()

        # Handle local image copying
        if not src.startswith(('http://', 'https://', 'data:')):
            # Local path
            clean_src = src.split('?')[0].split('#')[0]
            candidate_paths = [
                source_dir / clean_src,
                source_dir / "images" / Path(clean_src).name,
                Path(clean_src)
            ]
            found = False
            dest_name = Path(clean_src).name
            for cand in candidate_paths:
                if cand.is_file():
                    output_images_dir.mkdir(parents=True, exist_ok=True)
                    dest_file = output_images_dir / dest_name
                    try:
                        shutil.copy2(cand, dest_file)
                    except shutil.SameFileError:
                        pass
                    found = True
                    break

            final_src = f"images/{dest_name}"
        else:
            final_src = src

        return f'\n\n<div class="image-container"><img src="{final_src}" alt="{escape_html(alt_text)}" class="devsite-screenshot" loading="lazy"></div>\n\n'

    text = re.sub(r'!\[(.*?)\]\((.*?)\)', img_repl, text)

    # Step 5: Headings
    text = re.sub(r'^####\s+(.+)$', lambda m: f'<h4>{inline_format(m.group(1).strip())}</h4>', text, flags=re.MULTILINE)
    text = re.sub(r'^###\s+(.+)$', lambda m: f'<h3>{inline_format(m.group(1).strip())}</h3>', text, flags=re.MULTILINE)

    # Step 6: Lists & Paragraphs chunking
    lines = text.split("\n")
    out_lines = []
    in_list = False
    list_tag = "ul"
    paragraph_buffer = []

    def flush_paragraph():
        if paragraph_buffer:
            p_text = " ".join(paragraph_buffer).strip()
            if p_text:
                out_lines.append(f"<p>{inline_format(p_text)}</p>")
            paragraph_buffer.clear()

    for line in lines:
        stripped = line.strip()

        # Check for placeholder blocks
        if stripped.startswith("<!--CODE_BLOCK_") or stripped.startswith("<!--TABLE_BLOCK_") or \
           stripped.startswith("<!--ALERT_BLOCK_") or stripped.startswith("<div class=\"image-container\">") or \
           stripped.startswith("<h3>") or stripped.startswith("<h4>"):
            flush_paragraph()
            if in_list:
                out_lines.append(f"</{list_tag}>")
                in_list = False
            out_lines.append(stripped)
            continue

        # Check for list items
        ul_match = re.match(r'^[-*+]\s+(.+)$', stripped)
        ol_match = re.match(r'^[0-9]+\.\s+(.+)$', stripped)

        if ul_match or ol_match:
            flush_paragraph()
            target_tag = "ol" if ol_match else "ul"
            item_text = (ol_match or ul_match).group(1)

            if not in_list:
                list_tag = target_tag
                out_lines.append(f'<{list_tag} class="devsite-list">')
                in_list = True
            elif in_list and list_tag != target_tag:
                out_lines.append(f'</{list_tag}>')
                list_tag = target_tag
                out_lines.append(f'<{list_tag} class="devsite-list">')

            out_lines.append(f"  <li>{inline_format(item_text)}</li>")
            continue

        if in_list:
            out_lines.append(f"</{list_tag}>")
            in_list = False

        if not stripped:
            flush_paragraph()
        elif stripped.startswith("---") or stripped.startswith("***"):
            flush_paragraph()
            out_lines.append("<hr>")
        else:
            paragraph_buffer.append(stripped)

    flush_paragraph()
    if in_list:
        out_lines.append(f"</{list_tag}>")

    assembled = "\n".join(out_lines)

    # Step 7: Restore protected code, tables, and alerts
    for idx, block in enumerate(code_blocks):
        assembled = assembled.replace(f"<!--CODE_BLOCK_{idx}-->", block)
    for idx, block in enumerate(table_blocks):
        assembled = assembled.replace(f"<!--TABLE_BLOCK_{idx}-->", block)
    for idx, block in enumerate(alert_blocks):
        assembled = assembled.replace(f"<!--ALERT_BLOCK_{idx}-->", block)

    return assembled


# -----------------------------------------------------------------------------
# Metadata & Step Parsing
# -----------------------------------------------------------------------------

def parse_header_metadata(readme_content: str):
    """
    Extracts global metadata from the top header block of the Markdown document.
    """
    metadata = {
        'title': 'Google Codelab',
        'authors': '',
        'duration_min': 0,
        'original_url': '',
        'last_updated': '',
        'categories': ''
    }

    # Check preamble before step 1 for title
    step1_pos = re.search(r'^##\s+[0-9]+\.', readme_content, flags=re.MULTILINE)
    preamble = readme_content[:step1_pos.start()] if step1_pos else readme_content

    # Title: first # Title in preamble
    title_m = re.search(r'^#\s+(.+)$', preamble, flags=re.MULTILINE)
    if title_m:
        metadata['title'] = title_m.group(1).strip()
    else:
        # Fallback to note in Section 1: "This lab is based on [Title](URL)"
        note_m = re.search(r'This lab is based on\s+\[(.*?)\]\((https?://[^\s)]+)\)', readme_content, flags=re.IGNORECASE)
        if note_m:
            metadata['title'] = note_m.group(1).strip()
            if not metadata['original_url']:
                metadata['original_url'] = note_m.group(2).strip()

    # Original Lab: > **Original Lab**: [Text](URL) or URL
    orig_m = re.search(r'>\s*\*\*Original Lab\*\*:\s*\[?(.*?)\]?\(?(https?://[^\s)]+)?\)?', readme_content, flags=re.IGNORECASE)
    if orig_m:
        url = orig_m.group(2) or orig_m.group(1)
        if url.startswith("http"):
            metadata['original_url'] = url

    # Authors: > **Authors**: Names
    auth_m = re.search(r'>\s*\*\*Authors?\*\*:\s*(.+)$', readme_content, flags=re.MULTILINE | re.IGNORECASE)
    if auth_m:
        metadata['authors'] = auth_m.group(1).strip()

    # Duration: > **Duration**: N min / minutes
    dur_m = re.search(r'>\s*\*\*Duration\*\*:\s*([0-9]+)\s*(?:min|minutes)?', readme_content, flags=re.IGNORECASE)
    if dur_m:
        metadata['duration_min'] = int(dur_m.group(1))

    # Last Updated: > **Last Updated**: YYYY-MM-DD
    upd_m = re.search(r'>\s*\*\*Last Updated\*\*:\s*(.+)$', readme_content, flags=re.MULTILINE | re.IGNORECASE)
    if upd_m:
        metadata['last_updated'] = upd_m.group(1).strip()

    # Categories: > **Categories**: tags
    cat_m = re.search(r'>\s*\*\*Categories\*\*:\s*(.+)$', readme_content, flags=re.MULTILINE | re.IGNORECASE)
    if cat_m:
        metadata['categories'] = cat_m.group(1).strip()

    return metadata


def extract_steps_and_durations(markdown_content: str, global_duration: int, source_dir: Path, output_images_dir: Path):
    r"""
    Splits markdown into steps by ^## [0-9]+\. Title.
    Intelligently assigns step durations (either explicit, distributed, or word-count estimated).
    """
    # Protect code blocks during step splitting
    parts = re.split(r'(```.*?```)', markdown_content, flags=re.DOTALL)
    masked_parts = []
    code_blocks = []
    for p in parts:
        if p.startswith('```'):
            idx = len(code_blocks)
            code_blocks.append(p)
            masked_parts.append(f'__CODE_BLOCK_PRE_{idx}__')
        else:
            masked_parts.append(p)

    masked_text = ''.join(masked_parts)
    step_matches = list(re.finditer(r'^##\s+([0-9]+)\.\s+(.+)$', masked_text, flags=re.MULTILINE))

    if not step_matches:
        # Fallback: treat entire content as single step
        title = "Overview"
        body_html = parse_markdown_to_html(markdown_content, source_dir, output_images_dir)
        return [{
            'index': 0,
            'number': 1,
            'title': title,
            'duration': global_duration or 10,
            'html': body_html
        }]

    raw_steps = []
    for i, m in enumerate(step_matches):
        step_num = int(m.group(1))
        raw_title = m.group(2).strip()

        # Check for explicit duration in step header e.g. "Title (12 min)"
        explicit_dur = None
        dur_in_header = re.search(r'\((\d+)\s*(?:min|mins|minutes)\)', raw_title, re.IGNORECASE)
        if dur_in_header:
            explicit_dur = int(dur_in_header.group(1))
            raw_title = re.sub(r'\s*\(\d+\s*(?:min|mins|minutes)\)', '', raw_title, flags=re.IGNORECASE).strip()

        start = m.start()
        end = step_matches[i+1].start() if i+1 < len(step_matches) else len(masked_text)
        step_md = masked_text[start:end]

        # Restore code blocks
        for idx, cb in enumerate(code_blocks):
            step_md = step_md.replace(f'__CODE_BLOCK_PRE_{idx}__', cb)

        # Strip the step header line
        step_md_body = re.sub(r'^##\s+[0-9]+\.\s+.*?\n', '', step_md, count=1)
        word_count = len(step_md_body.split())

        raw_steps.append({
            'index': i,
            'number': step_num,
            'title': raw_title,
            'explicit_dur': explicit_dur,
            'word_count': word_count,
            'body_md': step_md_body
        })

    # Duration calculation strategy:
    # 1. If all have explicit durations, use them.
    # 2. If global duration is known, allocate proportionately across non-explicit steps.
    # 3. Otherwise estimate based on word count (~150 words/min), min 2 min for intro, 5 min for working steps.
    total_explicit = sum(s['explicit_dur'] or 0 for s in raw_steps if s['explicit_dur'] is not None)
    unassigned = [s for s in raw_steps if s['explicit_dur'] is None]

    if global_duration > 0 and unassigned:
        remaining_duration = max(0, global_duration - total_explicit)
        # Allocate step 0 (Intro) 0-5 min if not explicit
        total_words = sum(s['word_count'] for s in unassigned) or 1
        allocated_sum = 0
        for idx, s in enumerate(unassigned):
            if idx == len(unassigned) - 1:
                # Assign remainder to last step
                dur = max(0, remaining_duration - allocated_sum)
            else:
                share = (s['word_count'] / total_words) * remaining_duration
                dur = round(share)
                allocated_sum += dur
            s['duration'] = dur
    else:
        for s in raw_steps:
            if s['explicit_dur'] is not None:
                s['duration'] = s['explicit_dur']
            else:
                # Estimate: ~180 words/min
                est = max(1, math.ceil(s['word_count'] / 180))
                s['duration'] = est

    # Parse HTML for each step
    steps = []
    for s in raw_steps:
        dur = s.get('duration', s['explicit_dur'] or 5)
        html_body = parse_markdown_to_html(s['body_md'], source_dir, output_images_dir)
        steps.append({
            'index': s['index'],
            'number': s['number'],
            'title': s['title'],
            'duration': dur,
            'html': html_body
        })

    return steps


# -----------------------------------------------------------------------------
# Main HTML Builder
# -----------------------------------------------------------------------------

def build_codelab_site(
    input_file: Path,
    output_dir: Path,
    custom_title: str = None,
    custom_author: str = None,
    custom_duration: int = None,
    custom_url: str = None
):
    """
    Main pipeline converting Markdown to Google Codelabs site.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    output_images_dir = output_dir / "images"
    output_images_dir.mkdir(parents=True, exist_ok=True)

    with open(input_file, 'r', encoding='utf-8') as f:
        md_content = f.read()

    # Extract metadata
    meta = parse_header_metadata(md_content)
    title = custom_title or meta['title']
    authors = custom_author or meta['authors']
    total_duration = custom_duration if custom_duration is not None else meta['duration_min']
    original_url = custom_url or meta['original_url']

    source_dir = input_file.parent

    # Parse steps
    steps = extract_steps_and_durations(
        md_content,
        global_duration=total_duration,
        source_dir=source_dir,
        output_images_dir=output_images_dir
    )

    # Recalculate total duration if not explicitly provided
    calculated_total_duration = sum(s['duration'] for s in steps)
    if total_duration <= 0:
        total_duration = calculated_total_duration

    # Build Navigation Drawer HTML
    drawer_items_html = []
    for s in steps:
        active_class = " active" if s['index'] == 0 else ""
        item = f'''      <li class="step-item{active_class}" data-step="{s['index']}">
        <span class="step-number">{s['number']}</span>
        <span class="step-label">{escape_html(s['title'])}</span>
      </li>'''
        drawer_items_html.append(item)

    step_list_content = "\n".join(drawer_items_html)

    # Build Steps Content HTML
    steps_html = []
    for s in steps:
        active_class = " active" if s['index'] == 0 else ""
        meta_card = ""
        if s['index'] == 0:
            meta_items = []
            if authors:
                meta_items.append(f'''        <div class="meta-item">
          <span class="material-icons">person</span>
          <span><strong>Author:</strong> {escape_html(authors)}</span>
        </div>''')

            if meta_items:
                joined_items = "\n".join(meta_items)
                meta_card = f'''\n      <div class="codelab-meta-card">\n{joined_items}\n      </div>\n'''

        step_div = f'''    <div class="codelab-step{active_class}" id="step-{s['index']}" data-step="{s['index']}">
      <h2 class="step-title">{s['number']}. {escape_html(s['title'])}</h2>{meta_card}
      {s['html']}
    </div>'''
        steps_html.append(step_div)

    main_content = "\n\n".join(steps_html)

    # Assemble HTML document
    html_doc = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{escape_html(title)} | Google Codelabs</title>
  <link rel="icon" type="image/png" href="https://www.gstatic.com/devrel-devsite/prod/v4672e09ff336ee3bbcf1f2a3ff4c85675e2f79fb6bb9c35ae98dff0bc8eb4800/developers/images/favicon.png">
  
  <!-- Google Fonts & Material Icons -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500;700&family=Roboto:wght@300;400;500;700&family=Roboto+Mono:wght@400;500&display=swap" rel="stylesheet">
  <link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
  
  <link rel="stylesheet" href="styles.css">
</head>
<body>
  <!-- Fixed Top Header -->
  <header class="devsite-header">
    <div class="header-left">
      <a href="#" class="codelab-logo" aria-label="Google Codelabs">
        <svg viewBox="0 0 40 40" width="28" height="28">
          <circle cx="20" cy="20" r="18" fill="#1a73e8"/>
          <path fill="#ffffff" d="M12 20a8 8 0 0 1 13.6-5.7l2.1-2.1A11 11 0 1 0 31 20h-3a8 8 0 0 1-8 8 8 8 0 0 1-8-8z"/>
          <circle cx="20" cy="20" r="4" fill="#fbbc04"/>
        </svg>
        <span class="codelab-logo-text">Google Codelabs</span>
      </a>
      <span class="header-divider"></span>
      <span class="header-title">{escape_html(title)}</span>
    </div>
    
    <div class="progress-bar-container">
      <div class="progress-bar-fill" id="progress-bar-fill"></div>
    </div>
  </header>

  <!-- Main Codelab Layout -->
  <div class="codelab-container">
    <!-- Left Navigation Drawer -->
    <nav class="devsite-book-nav" id="drawer" aria-label="Codelab Table of Contents">
      <div class="drawer-header">
        <div class="filter-box">
          <span class="material-icons">filter_list</span>
          <input type="text" id="step-filter" placeholder="Filter steps..." aria-label="Filter steps">
        </div>
      </div>
      
      <ul class="step-list" id="step-list">
{step_list_content}
      </ul>
    </nav>
    
    <!-- Backdrop for Mobile Navigation -->
    <div class="drawer-backdrop" id="drawer-backdrop"></div>

    <!-- Step Content Area -->
    <main class="codelab-content" id="main-content">
{main_content}
    </main>

    <!-- Bottom Action Navigation Bar -->
    <footer class="devsite-actions">
      <button class="btn-nav btn-back" id="btn-prev" disabled aria-label="Previous step">
        <span class="material-icons">arrow_back</span>
        <span class="btn-label">Back</span>
      </button>
      
      <span class="step-indicator" id="step-indicator">Step 1 of {len(steps)}</span>
      
      <button class="btn-nav btn-next" id="btn-next" aria-label="Next step">
        <span class="btn-label">Next</span>
        <span class="material-icons">arrow_forward</span>
      </button>
    </footer>
  </div>

  <script src="app.js"></script>
</body>
</html>
'''

    # Write files
    index_file = output_dir / "index.html"
    with open(index_file, 'w', encoding='utf-8') as f:
        f.write(html_doc)

    styles_file = output_dir / "styles.css"
    with open(styles_file, 'w', encoding='utf-8') as f:
        f.write(DEFAULT_STYLES_CSS)

    app_file = output_dir / "app.js"
    with open(app_file, 'w', encoding='utf-8') as f:
        f.write(DEFAULT_APP_JS_TEMPLATE)

    num_images = len(list(output_images_dir.glob("*.*")))

    print(f"Generated static codelab site in {output_dir}/:")
    print(f"  - Title: '{title}'")
    print(f"  - Steps: {len(steps)}")
    print(f"  - Images copied: {num_images}")
    print(f"  - Files: {index_file.name}, {styles_file.name}, {app_file.name}")


# -----------------------------------------------------------------------------
# CLI Entrypoint
# -----------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Convert Markdown tutorial (lab.md or README.md) into a Google Codelabs static website."
    )
    parser.add_argument(
        'input',
        nargs='?',
        default=None,
        help="Input markdown file path (default: lab.md, fallback to README.md)"
    )
    parser.add_argument(
        '-i', '--input-file',
        dest='input_flag',
        default=None,
        help="Input markdown file path (overrides positional argument)"
    )
    parser.add_argument(
        '-o', '--output-dir',
        default='docs',
        help="Output directory for the static site (default: docs)"
    )
    parser.add_argument(
        '--title',
        default=None,
        help="Override the codelab title"
    )
    parser.add_argument(
        '--author',
        default=None,
        help="Override the author name"
    )
    parser.add_argument(
        '--duration',
        type=int,
        default=None,
        help="Override total duration in minutes"
    )
    parser.add_argument(
        '--original-url',
        default=None,
        help="Override original codelab URL"
    )

    args = parser.parse_args()

    # Determine input file
    input_candidate = args.input_flag or args.input
    if not input_candidate:
        if os.path.exists('lab.md'):
            input_candidate = 'lab.md'
        elif os.path.exists('README.md'):
            input_candidate = 'README.md'
        else:
            input_candidate = 'lab.md'

    input_path = Path(input_candidate)
    if not input_path.exists():
        print(f"Error: Input markdown file '{input_path}' not found.", file=sys.stderr)
        sys.exit(1)

    output_dir = Path(args.output_dir)

    build_codelab_site(
        input_file=input_path,
        output_dir=output_dir,
        custom_title=args.title,
        custom_author=args.author,
        custom_duration=args.duration,
        custom_url=args.original_url
    )


if __name__ == '__main__':
    main()
