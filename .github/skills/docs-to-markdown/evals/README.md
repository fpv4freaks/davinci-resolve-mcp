# Docs-to-Markdown Skill Testing Guide

This guide explains how to test the docs-to-markdown skill. Run these tests after making changes to verify nothing is broken.

## Test Files

| File                | Purpose                                                      |
| ------------------- | ------------------------------------------------------------ |
| `evals.json`        | 20 functional test prompts with expectations (manual grading) |
| `trigger-eval.json` | 15 trigger/no-trigger queries for description optimization   |

## How to Test

### Quick Smoke Test (5 minutes)

Open Copilot Chat (with the skill loaded) and try these three prompts. Each should behave as described:

1. **First-run setup:** Say "I want to convert some Word documents to markdown. I've never used this skill before."
   - Should: present dependency list, ask for approval via vscode_askQuestions, list pywin32 as optional
   - Should NOT: run pip install without approval, include pywin32 in mandatory install

2. **Denied approval:** After the dependency prompt, say "No, cancel."
   - Should: stop immediately, explain skill can't run without dependencies
   - Should NOT: proceed to folder setup or conversion

3. **Returning user:** Say "convert my documents to markdown" (with preferences already saved)
   - Should: read preferences from memory, skip to Phase 4, list source files, offer dry-run
   - Should NOT: re-ask about dependencies or folders

### Full Test Suite (with skill-creator)

To run the full eval suite with benchmarking, use the [skill-creator](../../skill-creator/) skill:

1. Load the skill-creator skill
2. Ask: "Run evals for the docs-to-markdown skill at `.github/skills/docs-to-markdown`"
3. The skill-creator will:
   - Read `evals/evals.json` for test prompts
   - Spawn subagents for each test case
   - Grade against the expectations
   - Generate a benchmark report

### Trigger Testing

To test whether the skill triggers correctly on different user prompts:

1. Load the skill-creator skill
2. Ask: "Run trigger eval optimization for docs-to-markdown using `evals/trigger-eval.json`"
3. Reviews which queries trigger the skill and which don't
4. Compares against expected `should_trigger` values

## What the Tests Cover

### Functional Evals (evals.json, IDs 1-20)

| ID Range | Scenario Category                  | Key Checks                                                        |
| -------- | ---------------------------------- | ----------------------------------------------------------------- |
| 1-4      | First-run setup (Phase 1)          | Dependency approval flow, denied consent, verification, pywin32 optional |
| 5-7      | Returning user (Phase 2-4)         | Preferences lookup, empty folder handling, dry-run offer          |
| 8        | Scanned/image-only PDF             | PyMuPDF fails gracefully, OCR suggestion                          |
| 9        | Non-Windows + IRM file             | Clear platform error, no cryptic traceback                        |
| 10       | Windows without pywin32            | Clear missing-package error with install command                  |
| 11-12    | Success path (batch + PDF)         | Multi-file conversion, per-file status, PDF via PyMuPDF           |
| 13       | Custom folder path                 | Accepts custom path, saves to preferences                         |
| 14       | Skip dry-run                       | Respects user intent, runs conversion directly                    |
| 15       | Mixed file types                   | All 6 formats, correct fallback chain per type                    |
| 16-17    | CLI flags (workers, dry-run)       | Passes flags correctly to convert_to_md.py                        |
| 18       | Troubleshooting (COM timeout)      | References troubleshooting table, actionable advice               |
| 19       | Lock file handling                 | Skips ~$ files, explains why                                      |
| 20       | Missing agent tool                 | Detects unavailable tool, stops with clear message                |

### Trigger Evals (trigger-eval.json, 15 queries)

| Category           | Count | Examples                                                                |
| ------------------ | ----- | ----------------------------------------------------------------------- |
| Should trigger     | 10    | "convert Word to markdown", "pdf to md", "batch convert Office files"   |
| Should NOT trigger | 5     | "create a Word document", "edit Excel file", "merge PDF files"          |

## Test File Dependencies

Some evals reference test fixture files in `evals/files/`. These are placeholders for manual testing — create appropriate sample files if running locally:

| File | Purpose |
| ---- | ------- |
| `scanned-image-only.pdf` | PDF with only images, no extractable text |
| `irm-protected.docx` | IRM/AIP-protected Word document |
| `legacy-format.doc` | Legacy binary Word format |
| `report.docx` | Standard modern Word document |
| `data.xlsx` | Standard modern Excel workbook |
| `slides.pptx` | Standard modern PowerPoint presentation |
| `proposal.pdf` | Standard PDF with text content |

## Adding New Tests

When adding a new feature or fixing a bug, add a corresponding test:

1. Add a new entry to `evals.json` with the next sequential ID
2. Include: `prompt`, `expected_output`, `files` (if needed), and `expectations`
3. If the feature changes triggering behavior, add entries to `trigger-eval.json`
