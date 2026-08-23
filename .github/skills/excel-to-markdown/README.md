# 📊 Excel to Markdown

**Convert Excel spreadsheets into clean, paste-ready Markdown tables**

**Author**: Balazs Skorka | **Type**: VS Code GitHub Copilot Skill | **Version**: 1.0 | **Date**: March 2026

Converts `.xlsx` and `.xls` workbooks into well-formatted Markdown pipe tables — ready for wikis, READMEs, ADO work items, or any documentation. Handles multi-sheet workbooks, merged cells, dates, booleans, and special characters automatically.

| | |
|---|---|
| 📄 **Convert** | Turn any Excel file into Markdown pipe tables |
| 🧹 **Clean** | Strip empty rows/columns with `--compact` mode |
| 🔢 **Index** | Add row numbers for easy reference |

> **Who it's for:** Anyone who needs Excel data in text-based documentation — Solution Architects writing specs, PMs updating wikis, developers adding data to READMEs.

---

## Installation & Setup

### Prerequisites

| Tool | Purpose | Link |
|------|---------|------|
| **VS Code** | IDE and skill host | [Download](https://code.visualstudio.com/) |
| **GitHub Copilot + Chat** | AI assistant | [Marketplace](https://marketplace.visualstudio.com/items?itemName=GitHub.copilot) |
| **Python 3.8+** | Runs the conversion script | [Download](https://www.python.org/downloads/) |

> No MCP server required. The `openpyxl` Python package is auto-installed on first use.

### Get the Skill Files

**Option A — Clone the repo** (recommended):
```
git clone https://github.com/mcaps-microsoft/ISDAIFirstAiBS.git
```
Open the folder in VS Code.

**Option B — Copy only the skill folder** into an existing workspace:
```
<your-workspace>/
└── .github/
    └── skills/
        └── excel-to-markdown/
            ├── SKILL.md
            ├── README.md
            ├── evals/
            │   └── evals.json
            └── scripts/
                └── excel_to_markdown.py
```

### Verify

1. Open Copilot Chat (`Ctrl+Shift+I`)
2. Say: *"convert this spreadsheet to markdown"* or *"turn this xlsx into a table"*
3. The skill activates and guides you through the conversion

> **Troubleshooting**: Skill not activating → verify `.github/skills/excel-to-markdown/SKILL.md` exists → reload VS Code.

---

## Skill Structure

```
excel-to-markdown/
├── SKILL.md                          # Skill definition — workflow & trigger config
├── README.md                         # This file
├── evals/
│   └── evals.json                    # Test cases for skill evaluation
└── scripts/
    └── excel_to_markdown.py          # Python conversion engine
```

| File | Purpose | Edit? |
|------|---------|-------|
| `SKILL.md` | Skill definition — workflow, triggers, edge cases | Advanced |
| `scripts/excel_to_markdown.py` | Conversion logic — formats, data types, table building | Advanced |
| `evals/evals.json` | Test prompts and expected outputs | Yes — add test cases |

---

## Workflow

1. **Identify** — Point Copilot to your Excel file (path, workspace file, or upload)
2. **Convert** — The skill runs `excel_to_markdown.py` with appropriate flags
3. **Deliver** — Output as inline Markdown, saved `.md` file, or clipboard-ready text
4. **Refine** *(optional)* — Filter columns, limit rows, change format if requested

---

## CLI Options

The conversion script supports these flags:

| Flag | Description | Example |
|------|-------------|---------|
| `--output <path>` | Save to file instead of stdout | `--output report.md` |
| `--sheets <names>` | Convert only named sheets | `--sheets Summary Details` |
| `--no-header` | Treat first row as data, not header | `--no-header` |
| `--max-rows <n>` | Limit to first N data rows per sheet | `--max-rows 20` |
| `--compact` | Remove fully empty rows and columns | `--compact` |
| `--index` | Add a row-number `#` column | `--index` |

---

## What You Get

### Output Format

- **Multi-sheet workbooks** → each sheet gets a `## Sheet: <name>` heading
- **Single-sheet workbooks** → clean table with no extra heading
- **Dates** → `YYYY-MM-DD` format
- **Booleans** → `Yes` / `No` (not `True` / `False`)
- **Decimals** → 2 decimal places by default, respects cell formatting
- **Pipe characters** → escaped as `\|` to preserve table structure

### Example Output

```markdown
## Sheet: Employees

| Name          | Department  | Start Date | Salary | Active |
| ------------- | ----------- | ---------- | ------ | ------ |
| Alice Johnson | Engineering | 2020-03-15 | 95000  | Yes    |
| Bob Smith     | Marketing   | 2019-07-01 | 72000  | Yes    |
```

---

## Key Features

- **Multi-sheet support** — Converts all sheets or selected ones with `--sheets`
- **Merged cell handling** — Top-left value preserved, remaining cells left empty
- **Auto-install** — `openpyxl` installs automatically on first run
- **Compact mode** — Strips sparse data (empty rows/columns) for clean output
- **Aligned columns** — Padded pipe tables for readable raw Markdown

---

## Portability

This skill is **fully self-contained**. To use in another workspace:

1. Copy `excel-to-markdown/` → `.github/skills/excel-to-markdown/` in target workspace
2. Ensure Python 3.8+ is installed
3. Any Copilot agent will discover and invoke it automatically

---

## Known Limitations

| Limitation | Details |
|-----------|---------|
| `.xls` format | Requires `xlrd` package (not auto-installed); `.xlsx` is preferred |
| Very wide tables | Tables with 8+ columns may not render well in narrow viewports |
| Charts & images | Not extracted — only cell data is converted |
| Complex formulas | Uses `data_only=True` — reads cached values, not live formulas |

---

## Usage Examples

```
"convert this spreadsheet to markdown"
"turn Sales.xlsx into a table for our wiki"
"xlsx to md — only the Summary sheet, first 10 rows"
"make this Excel readable, remove the empty columns"
"export the inventory spreadsheet with row numbers"
```

---

## Eval Results

Benchmarked against 3 test cases (multi-sheet, sparse data, wide table with special characters):

| Configuration | Pass Rate | Assertions |
|---------------|-----------|------------|
| **With Skill** | 100% | 18/18 |
| Baseline (No Skill) | 83% | 15/18 |
| **Delta** | **+17%** | **+3** |

---

## Changelog

| Version | Date | Changes |
|---------|------|----------|
| 1.0 | 2026-03-19 | Initial release — core conversion, multi-sheet, compact, index |
