---
name: docs-to-markdown
author: Ibrahim El Sayed (ibelsaye), Balázs Skorka
version: 2.0
date: April 2026
description: "Convert Office files (Word, Excel, PowerPoint) and PDF documents into clean Markdown. Handles modern OOXML, legacy binary, IRM/AIP-protected files, and PDF using Python libraries with Office COM fallback. USE WHEN user asks to convert .docx, .xlsx, .xls, .pptx, .ppt, .doc, .pdf files to Markdown, mentions 'convert to md', 'docs to markdown', 'office to markdown', 'extract content from Word/Excel/PowerPoint/PDF', 'convert presentations to text', 'turn spreadsheet into markdown', 'convert PDF to markdown', 'read protected Office files', 'convert IRM files', 'batch convert documents', 'document converter', 'pdf to md', or any intent to extract content from Office or PDF files into readable Markdown format. Even if the user doesn't say 'Markdown' — if they want to extract text/tables from Office documents or PDFs into a readable format, this skill handles it. DO NOT USE FOR: creating Office files, editing existing Office files, mail merge, or image-only PDFs (scanned documents without OCR)."
---

# Docs-to-Markdown Converter

**Authors:** Ibrahim El Sayed (ibelsaye), Balázs Skorka | **Version:** 2.0 | **Date:** April 2026

> Also known as: office-to-markdown

A simple skill that converts Word, Excel, PowerPoint, and PDF files into clean Markdown.
Drop your files into a source folder, run the skill, and get Markdown files in an output folder.
Your original files are never changed — the skill only reads them.

## How it works

The conversion script tries fast Python libraries first. If those fail (e.g., the file is IRM-protected, encrypted, or legacy binary), it falls back to Office COM automation using the user's Windows/M365 credentials to read the file.

### Platform support

| Capability | Windows | macOS / Linux |
|---|---|---|
| Modern OOXML (.docx, .xlsx, .pptx) | Yes | Yes |
| Legacy binary (.doc, .xls, .ppt) via COM | Yes (Office + pywin32) | No |
| IRM/AIP-protected files via COM | Yes (Office + pywin32) | No |
| PDF (.pdf) | Yes | Yes |
| Pandoc Word conversion | Yes | Yes |

The core Python-library path (python-docx, openpyxl, python-pptx, xlrd, PyMuPDF) is cross-platform. The COM fallback requires **Windows with Microsoft Office desktop installed and pywin32**. On macOS/Linux, files that need COM will fail with a clear error explaining the platform limitation.

### Fallback chain
- **Word** (.docx, .doc): pandoc → python-docx → Office COM (Word) *(Windows only)*
- **Excel** (.xlsx, .xls): openpyxl → xlrd → Office COM (Excel) *(Windows only)*
- **PowerPoint** (.pptx, .ppt): python-pptx → Office COM (PowerPoint) *(Windows only)*
- **PDF** (.pdf): PyMuPDF (fitz) *(cross-platform)*

## Required Agent Capabilities

This skill's guided workflow depends on the following agent tools. If any are unavailable, the corresponding phase will not execute correctly.

| Tool | Used in | Purpose |
|---|---|---|
| `vscode_askQuestions` | Phase 1, 2, 3, 4 | Prompt user for dependency approval, folder choices, dry-run confirmation |
| `run_in_terminal` | Phase 1, 4 | Run `pip install`, dependency verification, and the conversion script |
| `memory` (read/write) | Phase 2, 3, 4 | Save and retrieve user preferences (source/output folder paths) |
| `list_dir` | Phase 4 | Check source folder contents before conversion |
| `create_directory` | Phase 2, 3 | Create source and output folders when they don't exist |
| `read_file` | Phase 1, 2, 3, 4 | Read SKILL.md, user memory file, and conversion output |

If a required tool is disabled or unavailable, stop and tell the user which capability is missing.

## Guided Setup Workflow

Follow these steps in order. If the user has used this skill before and already has their folders configured (check user memory at `/memories/docs-to-markdown-preferences.md`), skip to **Phase 4**.

### Phase 1: Dependency Approval

Before anything else, explain to the user what dependencies are needed and ask for explicit approval to install them.

Present this to the user:

> To convert Office and PDF files to Markdown, the following Python packages need to be installed:
> - **python-docx** — reads Word documents
> - **openpyxl** — reads modern Excel files
> - **python-pptx** — reads PowerPoint presentations
> - **xlrd** — reads legacy Excel files
> - **msoffcrypto-tool** — detects IRM/encrypted files
> - **PyMuPDF** — reads PDF files (text, tables, and structure)
> - **Optional (Windows only): pywin32** — enables Office COM automation for IRM-protected and legacy binary files. Not needed for standard .docx/.xlsx/.pptx/.pdf conversion.
> - **Optional: pandoc** — provides the highest quality Word-to-Markdown conversion
>
> These packages are installed via `pip` into your Python environment.

Ask the user: **"Do you approve installing these dependencies? They are required — the skill cannot run without them."**

Use the `vscode_askQuestions` tool with options: "Yes, install dependencies" and "No, cancel".

**If the user says No** — stop immediately. Do NOT proceed to any other phase. Tell them: "The skill cannot run without these dependencies. No conversion will happen. You can come back anytime and we'll set it up."

**If the user says they already have them installed** — verify by running:
```
python -c "import docx, openpyxl, pptx, xlrd, msoffcrypto, fitz; print('All dependencies OK')"
```
If this fails, tell the user which package is missing and offer to install it. Do NOT proceed until all packages are confirmed installed.

Optionally, check if pywin32 is available (needed only for IRM-protected / legacy binary files on Windows):
```
python -c "import win32com; print('pywin32 OK')" 2>nul || echo "pywin32 not installed — COM fallback for protected files will not be available"
```

**If the user says Yes** — install the packages by running:
```
pip install python-docx openpyxl python-pptx xlrd msoffcrypto-tool PyMuPDF
```

Then ask if the user also wants pywin32 for IRM-protected / legacy binary file support (Windows only):
```
pip install pywin32
```
Wait for installation to complete. If any package fails to install, tell the user which one failed and why. Do NOT proceed to Phase 2 until all packages are successfully installed.

### Phase 2: Output Folder Setup

The output folder is where converted Markdown files will be saved.

Ask the user: **"Where should the converted Markdown files be saved?"**

Use the `vscode_askQuestions` tool with these options:
- `markdown-output` (recommended — clear and descriptive)
- `converted-docs`
- Let me specify a custom path

If the user picks a custom path, use their value. Otherwise use the selected option.

Create the folder if it doesn't exist (ask for confirmation).

### Phase 3: Source Folder Setup

The source folder is where the user places their Office files for conversion.

Ask the user: **"Where should your Office files go for conversion?"**

Use the `vscode_askQuestions` tool with these options:
- `office-source` (recommended — clear and descriptive)
- `docs-to-convert`
- Let me specify a custom path

If the folder doesn't exist, ask for confirmation to create it.

After both folders are set, save the configuration to user memory:

```
memory create /memories/docs-to-markdown-preferences.md
```

Content:
```markdown
# Docs-to-Markdown Preferences

## Folders
- Source folder: `<chosen source path>`
- Output folder: `<chosen output path>`

## Setup
- Dependencies approved: Yes
- Setup date: `<current date>`
```

Tell the user: **"Setup complete! Place your Office or PDF files (.docx, .xlsx, .pptx, .pdf, etc.) in the source folder and I'll convert them to Markdown in the output folder."**

### Phase 4: Run Conversion

This is the main conversion phase. If the user has used the skill before, start here.

1. **Check user memory** — read `/memories/docs-to-markdown-preferences.md` to get the configured source and output folders. If preferences don't exist, go back to Phase 1.

2. **Check source folder** — list the files in the source folder. If empty, tell the user: "Your source folder is empty. Place your Office or PDF files there and ask me to convert again."

3. **Offer dry-run first** — ask the user: "I found X file(s) to convert. Want me to list them first (dry run) or convert them directly?"

4. **Ask how the Markdown will be used** — before running the conversion, ask the user how they intend to use the output. Use the `vscode_askQuestions` tool with these options:
   - **Human-readable** — clean, polished Markdown intended to be read by people (e.g., docs, notes, sharing). The agent will favour readability: tidy headings, preserved tables, trimmed boilerplate, and a brief post-conversion review/cleanup pass on the generated `.md` files.
   - **Data source / reference** — raw Markdown intended to be consumed by another agent, RAG/search index, script, or skill. The agent will keep the output as-is (no cleanup pass), preserve structure verbatim, and treat the files as machine-readable inputs.

   Remember the choice for this run. If the user is unsure, default to **Human-readable**. The underlying conversion command is the same — the choice only controls post-processing and how results are presented.

5. **Run the conversion script** — The script is in the `scripts/` folder next to this SKILL.md. Execute:
   ```
   python scripts/convert_to_md.py "<source_folder>" --output "<output_folder>"
   ```
   Run this from the skill's own directory (the folder containing this SKILL.md).

6. **Apply the chosen output mode**:
   - If **Human-readable** was selected — after the script finishes, do a light cleanup pass on the generated `.md` files (collapse excessive blank lines, fix obvious formatting artefacts) and offer to open one for review.
   - If **Data source / reference** was selected — skip cleanup. Just confirm the files are ready to be ingested and list the output paths so they can be wired into the next agent/skill/pipeline.

7. **Report results** — show the user which files succeeded (OK), failed (FAIL), or were skipped (SKIP), with file sizes.

8. **Source files are safe** — remind the user: "Your original files are untouched — the script only reads them."

## Script Location

The conversion script is in the `scripts/` folder next to this SKILL.md:
```
docs-to-markdown/
├── SKILL.md
└── scripts/
    └── convert_to_md.py
```
It's always relative to where this skill is installed — no hardcoded paths needed.

It supports these CLI flags:
- `--output <dir>` — output directory
- `--dry-run` — list files without converting
- `--quiet` — suppress info/warn messages, only show results
- `--workers N` — parallel workers for modern files (default: 4)

## Important Notes

- The script NEVER modifies source files — read-only operation
- Lock files (`~$...`) are automatically skipped
- Corrupt files are detected and reported gracefully
- IRM/AIP-protected files are handled via Office COM using the logged-in user's credentials **(Windows + Office only)**
- Legacy binary formats (.doc, .xls, .ppt) fall back to COM if Python libraries can't read them **(Windows + Office only)**
- On macOS/Linux, files requiring COM will fail with a clear error — all other file types convert normally
- PDF files are handled natively via PyMuPDF — no Office or COM needed (cross-platform)
- All converted files are saved as `.md` in the output folder

## Troubleshooting

If conversion fails, check the following based on the error:

| Error | Likely cause | Fix |
|---|---|---|
| `FAIL ... (File is not a zip file)` | File is IRM-protected or legacy binary | COM will handle it automatically on Windows. If COM also fails, ensure Office is installed and you're logged in. On macOS/Linux, this file type cannot be converted — see Platform support above. |
| `FAIL ... (COM requires Windows)` | Running on macOS or Linux | COM fallback is Windows-only. IRM-protected and legacy binary files cannot be converted on this platform. |
| `FAIL ... (pywin32 is not installed)` | pywin32 not installed on Windows | Install with `pip install pywin32`. Only needed for IRM-protected or legacy binary files. |
| `FAIL ... (COM timed out)` | Office app hung during read | Close any open Office windows and try again. The script retries once automatically. |
| `FAIL ... (COM failed)` | Office couldn't open the file | Verify you can open the file manually in Office. If it asks for a password, the script can't read it. |
| `SKIP ... (file appears corrupt)` | File header doesn't match its extension | The file may have been renamed or damaged. Try opening it in Office manually. |
| `SKIP ... (lock file)` | File is currently open in Office | Close the file in Office first, then retry. |
| `FAIL ... (PDF: no text found)` | PDF is image-only (scanned) | The PDF contains only images with no extractable text. Run OCR on it first. |
| `pip install` fails | Network or permissions issue | Try running `pip install --user <package>` or check your internet connection. |
