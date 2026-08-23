# 📊 XLSX Skill

**Create, edit, and analyze Excel spreadsheets.**

**Author**: Anthropic (upstream) | **Type**: Copilot Skill | **Version**: 1.0 | **Date**: May 2026

A skill for building and maintaining Excel workbooks — including financial models with strict industry-standard formatting (blue inputs, black formulas, green cross-sheet links). Uses **pandas** for data analysis and **openpyxl** for formulas and formatting, with **LibreOffice** to recalculate formulas after writing.

| | |
|---|---|
| 🆕 **Create** | New workbooks with formulas, formatting, charts, multiple sheets |
| ✏️ **Edit** | Modify existing files while preserving formulas, formatting, and named styles |
| 📊 **Analyze** | Read with pandas — preview, statistics, multi-sheet aggregations |
| 🧮 **Models** | Financial models with assumption cells, scenario inputs, and zero-error formulas |

> **Who it's for:** Anyone producing or maintaining spreadsheets — consultants building financial models, PMs tracking budgets, anyone cleaning messy tabular data.

---

## Installation & Setup

### Prerequisites

| Tool | Purpose | Link |
|------|---------|------|
| **VS Code** | IDE and skill host | [Download](https://code.visualstudio.com/) |
| **GitHub Copilot + Chat** | AI assistant | [Marketplace](https://marketplace.visualstudio.com/items?itemName=GitHub.copilot) |
| **Python 3.9+** | Runs the spreadsheet helper scripts | [Download](https://www.python.org/) |
| **pandas** | Data analysis and read/write | `pip install pandas openpyxl` |
| **openpyxl** | Formula/formatting-aware writes | `pip install openpyxl` |
| **LibreOffice** | Required for formula recalculation via `scripts/recalc.py` | [Download](https://www.libreoffice.org/) |

### Step 1: Install Dependencies

```bash
pip install pandas openpyxl

# Verify
python -c "import pandas, openpyxl; print('ok')"
soffice --version
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
        └── xlsx/
            ├── SKILL.md
            ├── README.md
            ├── LICENSE.txt
            ├── artefact.yaml
            └── scripts/
                ├── recalc.py
                └── office/
```

### Step 3: Verify

1. Open Copilot Chat (`Ctrl+Shift+I`)
2. Ask: *"Build a 3-year revenue forecast model in Excel"* or *"Clean up this messy CSV"*
3. The skill activates and guides you through the workflow

> **Troubleshooting**: Skill not activating → verify `.github/skills/xlsx/SKILL.md` exists → reload VS Code. `recalc.py` errors → confirm LibreOffice is installed and on PATH.

---

## Skill Structure

```
xlsx/
├── SKILL.md            # Core workflow — pandas vs openpyxl, formula rules, financial-model standards
├── README.md           # This file
├── LICENSE.txt         # License terms
├── artefact.yaml       # Catalog metadata
└── scripts/
    ├── recalc.py       # Recalculate formulas via LibreOffice + scan for errors
    └── office/
        └── soffice.py  # LibreOffice wrapper (sandbox-safe)
```

| File | Purpose | Edit directly? |
|------|---------|----------------|
| `SKILL.md` | Skill definition — output standards, formula rules, library selection | No — syncs from central repo |
| `scripts/recalc.py` | Forces LibreOffice to recalculate all formulas and reports errors as JSON | No |
| `scripts/office/soffice.py` | Configures LibreOffice for sandboxed environments | No |

**Progressive loading**: Only `SKILL.md` loads at start. The recalc script is invoked when needed.

---

## Workflow

### Building a new workbook

1. **Choose tool** — pandas for bulk data, openpyxl for formulas/formatting
2. **Lay out structure** — assumptions on one sheet, calculations on others, outputs on a summary tab
3. **Write data and formulas** — use cell references, never hardcoded calculated values
4. **Apply formatting** — fonts (Arial/professional), number formats, color codes
5. **MANDATORY: Recalculate** — `python scripts/recalc.py output.xlsx`
6. **Verify** — check the JSON for `status: success` and zero errors; fix any `#REF!`, `#DIV/0!`, `#VALUE!`, `#NAME?` before delivering

### Editing an existing workbook

1. **Load with openpyxl** (preserves formulas) — not pandas (which discards them)
2. **Modify** cells, rows, columns, sheets — preserve existing template conventions
3. **Save**, then **recalculate** via `recalc.py`
4. **Verify** zero formula errors

### Analyzing data

```python
import pandas as pd
df = pd.read_excel('file.xlsx', sheet_name=None)  # all sheets
df['Sheet1'].describe()
```

### Financial-model conventions (enforced)

| Color | RGB | Meaning |
|-------|-----|---------|
| 🔵 Blue text | 0,0,255 | Hardcoded inputs, scenario knobs |
| ⚫ Black text | 0,0,0 | Formulas and calculations |
| 🟢 Green text | 0,128,0 | Cross-sheet links within same workbook |
| 🔴 Red text | 255,0,0 | External-file links |
| 🟡 Yellow fill | 255,255,0 | Key assumptions needing review |

Number formats: currency as `$#,##0`, percentages as `0.0%`, multiples as `0.0x`, zeros as `-`, negatives in parentheses.

---

## What You Get

### Outputs

| Output | Description | When Available |
|--------|-------------|---------------|
| `*.xlsx` | New or modified Excel file with recalculated formulas | After save + recalc |
| `*.csv` / `*.tsv` | Data export from pandas | When converting tabular data |
| Recalc JSON | `{"status": "success", "total_formulas": N, "total_errors": 0}` | After `recalc.py` |

### File Naming Convention

The skill uses whatever filename you specify. For models, the convention is `<topic>-model-v<N>.xlsx` (e.g., `revenue-forecast-v3.xlsx`).

---

## Preferences

No preferences available — the skill uses fixed defaults. Industry-standard financial-model color conventions are baked into SKILL.md but always defer to existing template conventions.

---

## Key Features

- **Zero-error guarantee** — `recalc.py` scans all cells and reports every `#REF!`, `#DIV/0!`, `#VALUE!`, `#N/A`, `#NAME?` with location
- **Formula-first** — explicit rule against hardcoding calculated values; everything must be reproducible
- **Industry-standard model formatting** — color conventions match financial-modelling community standards
- **Template-respecting** — existing template conventions override the defaults when editing
- **pandas + openpyxl split** — pick the right tool for data-heavy vs formula-heavy work

---

## Portability

This skill is **self-contained**. To use in another workspace:

1. Copy `xlsx/` → `.github/skills/xlsx/` in target workspace
2. Install Python (`pandas`, `openpyxl`) and LibreOffice
3. Any Copilot agent will discover and invoke it automatically

---

## Known Limitations

| Limitation | Details |
|-----------|---------|
| LibreOffice required for recalc | `recalc.py` cannot work without it; formulas remain as text strings otherwise |
| Reading with `data_only=True` is destructive | Saving discards formulas — keep workflows separate |
| openpyxl ignores Excel-specific features | VBA macros, complex pivot tables, slicers don't round-trip cleanly |
| pandas discards formatting | Use openpyxl when you care about cell formats, fonts, or colors |
| 1-based indexing in openpyxl | Off-by-one errors are common when mixing with 0-based pandas |

---

## Usage Examples

```
Build a 3-year revenue forecast with growth-rate assumptions and a summary tab
Add a "Q3 Actuals" column to budget-2026.xlsx with formulas pulling from raw-data.xlsx
Clean up customer-list.csv — fix malformed rows and produce a proper xlsx
Sum sales by region across all sheets in regional-data.xlsx
Convert this messy TSV into a formatted spreadsheet with column headers
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

*Built around pandas, openpyxl, and LibreOffice. Original skill authored by Anthropic.*
