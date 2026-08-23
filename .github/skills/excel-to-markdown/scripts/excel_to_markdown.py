#!/usr/bin/env python3
"""Convert Excel workbooks (.xlsx/.xls) to Markdown pipe tables.

Usage:
    python excel_to_markdown.py <input_file> [options]

Options:
    --output <path>          Write to file instead of stdout
    --sheets <name> ...      Convert only named sheets (default: all)
    --no-header              Treat first row as data, not header
    --max-rows <n>           Limit to first N data rows per sheet
    --compact                Strip fully empty rows and columns
    --index                  Add a row-number column
"""

import argparse
import datetime
import importlib
import subprocess
import sys
import textwrap
from pathlib import Path


def _ensure_openpyxl():
    """Install openpyxl if it is not already available."""
    try:
        importlib.import_module("openpyxl")
    except ImportError:
        print("openpyxl not found — installing…", file=sys.stderr)
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "openpyxl"],
            stdout=sys.stderr,
            stderr=sys.stderr,
        )


_ensure_openpyxl()

import openpyxl  # noqa: E402
from openpyxl.utils import range_boundaries  # noqa: E402


# ── helpers ──────────────────────────────────────────────────────────

def _format_value(value, number_format=None):
    """Convert a cell value to a display string."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, datetime.datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S") if value.hour or value.minute or value.second else value.strftime("%Y-%m-%d")
    if isinstance(value, datetime.date):
        return value.strftime("%Y-%m-%d")
    if isinstance(value, datetime.time):
        return value.strftime("%H:%M:%S")
    if isinstance(value, float):
        # Preserve explicit number formats when present
        if number_format and number_format != "General":
            # Count decimal places hinted by the format
            if "0.0000" in number_format:
                return f"{value:.4f}"
            if "0.000" in number_format:
                return f"{value:.3f}"
            if "0.0" in number_format:
                return f"{value:.1f}"
            if "%" in number_format:
                return f"{value * 100:.2f}%"
        return f"{value:.2f}" if value != int(value) else str(int(value))
    # Escape pipe characters so they don't break the Markdown table
    return str(value).replace("|", "\\|").replace("\n", " ").replace("\r", "")


def _resolve_merged_cells(ws):
    """Build a dict mapping (row, col) → value for merged regions.

    For each merged range the top-left cell's value is placed in the
    first cell; all other cells in the range map to empty string.
    """
    merged = {}
    for merge_range in ws.merged_cells.ranges:
        min_col, min_row, max_col, max_row = range_boundaries(str(merge_range))
        top_left_value = ws.cell(row=min_row, column=min_col).value
        for row in range(min_row, max_row + 1):
            for col in range(min_col, max_col + 1):
                if row == min_row and col == min_col:
                    merged[(row, col)] = top_left_value
                else:
                    merged[(row, col)] = ""
    return merged


def _read_sheet(ws, merged_map, no_header, max_rows, compact, add_index):
    """Read a worksheet into a list of header strings and list of row-lists."""
    # Gather raw grid
    raw_rows = []
    for row in ws.iter_rows(min_row=1):
        raw_rows.append(
            [
                _format_value(
                    merged_map.get((cell.row, cell.column), cell.value),
                    cell.number_format,
                )
                for cell in row
            ]
        )

    if not raw_rows:
        return None, None

    # ── compact: drop fully empty rows and columns ──
    if compact:
        # Drop empty rows
        raw_rows = [r for r in raw_rows if any(c.strip() for c in r)]
        if not raw_rows:
            return None, None
        # Detect non-empty column indices
        col_count = max(len(r) for r in raw_rows)
        keep_cols = [
            ci
            for ci in range(col_count)
            if any((ci < len(r) and r[ci].strip()) for r in raw_rows)
        ]
        raw_rows = [[r[ci] if ci < len(r) else "" for ci in keep_cols] for r in raw_rows]

    if not raw_rows:
        return None, None

    # ── header / data split ──
    if no_header:
        col_count = max(len(r) for r in raw_rows)
        headers = [f"Col {i + 1}" for i in range(col_count)]
        data_rows = raw_rows
    else:
        headers = raw_rows[0]
        data_rows = raw_rows[1:]

    # ── max rows ──
    if max_rows is not None and max_rows > 0:
        data_rows = data_rows[:max_rows]

    # ── index column ──
    if add_index:
        headers = ["#"] + list(headers)
        data_rows = [[str(i + 1)] + list(row) for i, row in enumerate(data_rows)]

    return headers, data_rows


def _build_pipe_table(headers, data_rows):
    """Create a Markdown pipe table from headers and rows."""
    # Normalise column count
    col_count = len(headers)
    safe_rows = [list(r) + [""] * (col_count - len(r)) for r in data_rows]

    # Calculate column widths (minimum 3 for the separator)
    widths = [max(3, len(h)) for h in headers]
    for row in safe_rows:
        for i, cell in enumerate(row[:col_count]):
            widths[i] = max(widths[i], len(cell))

    def _pad_row(cells):
        return "| " + " | ".join(c.ljust(widths[i]) for i, c in enumerate(cells[:col_count])) + " |"

    lines = [_pad_row(headers)]
    lines.append("| " + " | ".join("-" * widths[i] for i in range(col_count)) + " |")
    for row in safe_rows:
        lines.append(_pad_row(row))

    return "\n".join(lines)


# ── main ─────────────────────────────────────────────────────────────

def convert(input_path, *, output_path=None, sheet_names=None,
            no_header=False, max_rows=None, compact=False, add_index=False):
    """Convert an Excel file to Markdown and return the text."""
    path = Path(input_path)
    if not path.exists():
        print(f"Error: file not found — {path}", file=sys.stderr)
        sys.exit(1)

    wb = openpyxl.load_workbook(str(path), data_only=True, read_only=False)

    sheets_to_convert = sheet_names if sheet_names else wb.sheetnames
    missing = [s for s in sheets_to_convert if s not in wb.sheetnames]
    if missing:
        print(f"Warning: sheets not found and skipped — {', '.join(missing)}", file=sys.stderr)
        sheets_to_convert = [s for s in sheets_to_convert if s in wb.sheetnames]

    multi_sheet = len(sheets_to_convert) > 1
    sections = []

    for sname in sheets_to_convert:
        ws = wb[sname]
        merged_map = _resolve_merged_cells(ws)
        headers, data_rows = _read_sheet(ws, merged_map, no_header, max_rows, compact, add_index)

        if headers is None:
            sections.append(f"> Sheet \"{sname}\" is empty.\n")
            continue

        table_md = _build_pipe_table(headers, data_rows)
        if multi_sheet:
            sections.append(f"## Sheet: {sname}\n\n{table_md}\n")
        else:
            sections.append(table_md + "\n")

    result = "\n".join(sections)

    if output_path:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(result, encoding="utf-8")
        print(f"Written to {out}", file=sys.stderr)

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Convert Excel workbooks to Markdown tables.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            examples:
              %(prog)s data.xlsx
              %(prog)s data.xlsx --sheets Summary Details --output report.md
              %(prog)s data.xlsx --max-rows 50 --compact --index
        """),
    )
    parser.add_argument("input", help="Path to the Excel file (.xlsx or .xls)")
    parser.add_argument("--output", help="Write output to this file")
    parser.add_argument("--sheets", nargs="+", help="Only convert these sheets")
    parser.add_argument("--no-header", action="store_true",
                        help="Treat first row as data, not header")
    parser.add_argument("--max-rows", type=int,
                        help="Max data rows per sheet")
    parser.add_argument("--compact", action="store_true",
                        help="Remove fully empty rows/columns")
    parser.add_argument("--index", action="store_true",
                        help="Add a row-number column")

    args = parser.parse_args()

    md = convert(
        args.input,
        output_path=args.output,
        sheet_names=args.sheets,
        no_header=args.no_header,
        max_rows=args.max_rows,
        compact=args.compact,
        add_index=args.index,
    )

    if not args.output:
        print(md)


if __name__ == "__main__":
    main()
