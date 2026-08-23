# 📄 DOCX Skill

**Create, edit, read, and analyze Microsoft Word (.docx) documents.**

**Author**: Anthropic (upstream) | **Type**: Copilot Skill | **Version**: 1.0 | **Date**: May 2026

A skill for working with Word documents end-to-end — generate polished new documents with docx-js, edit existing files via direct XML manipulation (preserving formatting and tracked changes), and read or convert documents using pandoc and LibreOffice.

| | |
|---|---|
| 🆕 **Create** | Generate new .docx files with docx-js — tables, headings, TOC, headers/footers, footnotes, images |
| ✏️ **Edit** | Unpack → edit XML → repack workflow with tracked changes and comments preserved |
| 📖 **Read** | Extract text via pandoc, convert to PDF/images, accept tracked changes programmatically |

> **Who it's for:** Anyone producing or modifying Word documents — consultants writing FDDs/TDDs, PMs producing reports, anyone redlining contracts.

---

## Installation & Setup

### Prerequisites

| Tool | Purpose | Link |
|------|---------|------|
| **VS Code** | IDE and skill host | [Download](https://code.visualstudio.com/) |
| **GitHub Copilot + Chat** | AI assistant | [Marketplace](https://marketplace.visualstudio.com/items?itemName=GitHub.copilot) |
| **Python 3.9+** | Runs the office helper scripts | [Download](https://www.python.org/) |
| **Node.js + npm** | Runs `docx-js` for new-document creation | [Download](https://nodejs.org/) |
| **pandoc** | Text extraction with tracked-changes support | [Install](https://pandoc.org/installing.html) |
| **LibreOffice** | DOCX↔PDF conversion, accepting tracked changes | [Download](https://www.libreoffice.org/) |
| **Poppler (`pdftoppm`)** | PDF→image rendering for visual QA | [Install](https://poppler.freedesktop.org/) |
| **docx-js** | Create new documents from JavaScript | `npm install -g docx` |

### Step 1: Install Dependencies

```bash
# Python script dependencies are bundled in scripts/office
pip install pypdf  # if not already present

# Node package for new-document creation
npm install -g docx

# Verify
pandoc --version
soffice --version
pdftoppm -v
```

### Step 2: Get the Skill Files

**Option A — Clone the repo**:
```
git clone <repo-url>
```
Open the folder in VS Code.

**Option B — Copy only the skill folder** into an existing workspace:
```
<your-workspace>/
└── .github/
    └── skills/
        └── docx/
            ├── SKILL.md
            ├── README.md
            ├── LICENSE.txt
            ├── artefact.yaml
            └── scripts/
                ├── accept_changes.py
                ├── comment.py
                ├── office/
                └── templates/
```

### Step 3: Verify

1. Open Copilot Chat (`Ctrl+Shift+I`)
2. Ask: *"Create a one-page Word memo about Q2 results"* or *"Read this .docx and summarize it"*
3. The skill activates and guides you through the workflow

> **Troubleshooting**: Skill not activating → verify `.github/skills/docx/SKILL.md` exists → reload VS Code. Script errors → confirm Python, Node, LibreOffice, and pandoc are on PATH.

---

## Skill Structure

```
docx/
├── SKILL.md                      # Core workflow — creating, editing, reading
├── README.md                     # This file
├── LICENSE.txt                   # License terms
├── artefact.yaml                 # Catalog metadata
└── scripts/
    ├── accept_changes.py         # Accept all tracked changes (uses LibreOffice)
    ├── comment.py                # Add/reply to comments in unpacked DOCX
    ├── office/
    │   ├── unpack.py             # Extract DOCX → XML files for editing
    │   ├── pack.py               # Repack XML files → DOCX with validation
    │   ├── validate.py           # Validate document XML
    │   └── soffice.py            # LibreOffice wrapper (handles sandbox setup)
    └── templates/                # Document templates and reference samples
```

| File | Purpose | Edit directly? |
|------|---------|----------------|
| `SKILL.md` | Skill definition — workflow, docx-js patterns, XML reference | No — syncs from central repo |
| `scripts/office/*.py` | Office helpers for pack/unpack/validate/PDF conversion | No |
| `scripts/accept_changes.py` | Resolves tracked changes via LibreOffice | No |
| `scripts/comment.py` | Manages comment XML across the unpacked bundle | No |

**Progressive loading**: Only `SKILL.md` loads at start. Scripts are invoked as needed.

---

## Workflow

### Creating a new document

1. **Decide structure** — sections, headings, tables, images
2. **Write a Node.js generator** using docx-js (see "Creating New Documents" in SKILL.md)
3. **Run the generator** to produce the .docx
4. **Validate** with `python scripts/office/validate.py doc.docx`
5. **Visually verify** by converting to PDF/images if formatting is critical

### Editing an existing document

1. **Unpack** — `python scripts/office/unpack.py document.docx unpacked/`
2. **Edit XML** in `unpacked/word/` — use the Edit tool directly, not Python scripts
3. **Add comments** (optional) — `python scripts/comment.py unpacked/ 0 "Comment text"`
4. **Pack** — `python scripts/office/pack.py unpacked/ output.docx --original document.docx`
5. **Auto-repair runs on pack** — fixes whitespace and durableId issues automatically

### Reading content

- **Text only**: `pandoc --track-changes=all document.docx -o output.md`
- **Raw XML**: `python scripts/office/unpack.py document.docx unpacked/`
- **Visual preview**: convert to PDF → render images with `pdftoppm`

---

## What You Get

### Outputs

| Output | Description | When Available |
|--------|-------------|---------------|
| `*.docx` | New or modified Word document | After create/edit workflow |
| `*.md` | Markdown extraction with tracked-changes annotation | After pandoc read |
| `slide-*.jpg` / `page-*.jpg` | Rendered page images for visual QA | After PDF→image conversion |
| `unpacked/` | XML tree of an unpacked DOCX for inspection | After unpack step |

### File Naming Convention

The skill uses whatever filename you specify. For tracked-change edits, the convention is `Claude` as author unless overridden.

---

## Preferences

No preferences available — the skill uses fixed defaults. All behaviour is driven by the prompt; there is no user-level config in `/memories/`.

---

## Key Features

- **docx-js generation** — full table/image/header/footer/TOC support with critical-rule guidance baked into SKILL.md
- **Lossless edit workflow** — unpack → edit raw XML → repack with auto-validation
- **Tracked changes & comments** — programmatic creation, acceptance, rejection, and replies
- **Smart-quote preservation** — unpacker converts to XML entities so quotes survive editing
- **Auto-repair on pack** — fixes common XML issues (whitespace, durableId range) before saving

---

## Portability

This skill is **self-contained**. To use in another workspace:

1. Copy `docx/` → `.github/skills/docx/` in target workspace
2. Ensure Python, Node, pandoc, LibreOffice, and Poppler are installed
3. Run `npm install -g docx` for new-document creation
4. Any Copilot agent will discover and invoke it automatically

---

## Known Limitations

| Limitation | Details |
|-----------|---------|
| Legacy `.doc` requires conversion | Must run `soffice.py --convert-to docx` first |
| LibreOffice required for tracked-change acceptance | `accept_changes.py` cannot work without it |
| Tables width: DXA only | `WidthType.PERCENTAGE` breaks in Google Docs — use DXA exclusively |
| docx-js defaults to A4 | Must set US Letter (12240×15840 DXA) explicitly when needed |
| Page-break must be inside a Paragraph | Standalone `PageBreak()` creates invalid XML |

---

## Usage Examples

```
Create a 2-page memo to the CFO about Q2 cost overruns, formal tone
Fill in <FDD-template.docx> with the requirements from <input.md>
Extract all tracked changes from contract-v3.docx as a redline summary
Replace "Acme Corp" with "Globex" everywhere in agreement.docx
Add a comment from "Reviewer" on every "TBD" in draft.docx
```

---

## Changelog

| Version | Date | Changes |
|---------|------|----------|
| 1.0 | 2026-05-20 | Initial README and artefact.yaml added for ISD catalog integration |

---

## License

See `LICENSE.txt` in the skill folder for full terms.

---

*Built around docx-js, pandoc, LibreOffice, and python-docx tooling. Original skill authored by Anthropic.*
