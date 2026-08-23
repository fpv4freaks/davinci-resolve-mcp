# 📄 Docs-to-Markdown

**Convert Word, Excel, PowerPoint, and PDF files into clean Markdown — including IRM-protected and legacy formats.**

**Authors**: Ibrahim El Sayed, Balázs Skorka | **Type**: VS Code GitHub Copilot Skill | **Version**: 2.0 | **Date**: April 2026

> Also known as: office-to-markdown

Converts Office documents (.docx, .xlsx, .pptx and legacy .doc, .xls, .ppt) and PDF files (.pdf) to Markdown files. Handles modern, legacy binary, IRM/AIP-encrypted, and PDF files using Python libraries with Office COM fallback. The script only reads files — it never modifies the source.

| | |
|---|---|
| 📄 **Convert** | Word, Excel, PowerPoint, and PDF to Markdown |
| 🔐 **Handle** | IRM-protected, encrypted, and legacy binary files |
| ⚡ **Batch** | Convert entire folders in parallel |

> **Who it's for:** Anyone who needs to extract content from Office files or PDFs into readable, searchable Markdown format — consultants, delivery leads, project managers working with SOWs, proposals, staffing plans, and design documents.

---

## Installation & Setup

### Prerequisites

| Tool | Purpose | Link |
|------|---------|------|
| **VS Code** | IDE and skill host | [Download](https://code.visualstudio.com/) |
| **GitHub Copilot + Chat** | AI assistant | [Marketplace](https://marketplace.visualstudio.com/items?itemName=GitHub.copilot) |
| **Python 3.8+** | Runs the conversion script | [Download](https://www.python.org/) |
| **Microsoft Office** (optional) | Required only for IRM-protected or legacy binary files | — |
| **pandoc** (optional) | Best quality Word-to-Markdown conversion | [Download](https://pandoc.org/) |

> **Note:** PDF conversion uses PyMuPDF and requires no additional software beyond Python.

### Step 1: Get the Skill Files

**Option A — Agentic Skill Installer** (recommended):

1. Open the **Agentic Skill Installer** from the Activity Bar
2. Find **docs-to-markdown** in the Skills section
3. Click the download icon to install

**Option B — Copy the skill folder** into your workspace:
```
<your-workspace>/
└── .github/
    └── skills/
        └── docs-to-markdown/
            ├── SKILL.md
            ├── README.md
            ├── LICENSE.TXT
            └── scripts/
                └── convert_to_md.py
```

### Step 2: Verify

1. Open Copilot Chat (`Ctrl+Shift+I`)
2. Say "convert my documents to Markdown" or "I need to convert a Word document" or "convert a PDF to Markdown"
3. The skill activates and guides you through setup

---

## Skill Structure

```
docs-to-markdown/
├── SKILL.md              # Skill workflow & instructions
├── README.md             # This file
├── LICENSE.TXT           # MIT License
└── scripts/
    └── convert_to_md.py  # The conversion script (bundled)
```

| File | Purpose |
|------|---------|
| `SKILL.md` | Guided workflow — dependency approval, folder setup, conversion |
| `scripts/convert_to_md.py` | Python script that reads Office files and writes Markdown (bundled with the skill) |

---

## Workflow

1. **Approve Dependencies** — The skill lists the Python packages needed and asks for your approval before installing anything.
2. **Select Output Folder** — Choose or create a folder where Markdown files will be saved. Recommended: `markdown-output`.
3. **Select Source Folder** — Choose or create a folder where you place your files. Recommended: `office-source`.
4. **Convert** — The skill runs the conversion script. You can do a dry run first to preview what will be converted.

On repeat use, steps 1-3 are skipped — your preferences are remembered across sessions.

---

## What You Get

### Outputs

| Output | Description |
|--------|-------------|
| `*.md` | One Markdown file per input file, saved in the output folder |

### Conversion Quality

| File Type | What's Extracted |
|-----------|-----------------|
| **Word** | Headings, bold/italic, lists, tables, document structure |
| **Excel** | Each sheet as a Markdown table with all data |
| **PowerPoint** | Slide titles, bullet content, tables, speaker notes |
| **PDF** | Text with heading detection (by font size), tables, page structure |

### Script CLI Options

```
python convert_to_md.py <input> [--output DIR] [--dry-run] [--quiet] [--workers N]
```

| Flag | Description |
|------|-------------|
| `--output`, `-o` | Output directory |
| `--dry-run` | List files without converting |
| `--quiet`, `-q` | Only show OK/FAIL/SKIP results |
| `--workers`, `-w` | Parallel workers (default: 4) |

---

## Preferences

### User Preferences

Preferences are stored in VS Code's user memory at `/memories/docs-to-markdown-preferences.md` and persist across all workspaces.

| Setting | Description | Default |
|---------|-------------|---------|
| **Source folder** | Where Office files are placed for conversion | `office-source` |
| **Output folder** | Where Markdown files are saved | `markdown-output` |
| **Dependencies approved** | Whether the user approved package installation | Set during first run |

To view or change preferences, ask: "Show my docs-to-markdown preferences" or "Change my conversion output folder".

To reset, ask: "Reset my docs-to-markdown preferences" — this will re-trigger the setup workflow.

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | April 2026 | Initial release — guided setup, batch conversion, IRM support, progress indicators, dry-run, quiet mode, corrupt/lock file detection |
| 2.0 | April 2026 | Added PDF conversion via PyMuPDF, renamed to docs-to-markdown (alias: office-to-markdown) |
