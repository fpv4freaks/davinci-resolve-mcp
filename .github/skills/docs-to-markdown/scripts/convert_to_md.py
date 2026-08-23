"""
Docs-to-Markdown Converter

Authors: Ibrahim El Sayed (ibelsaye), Balázs Skorka
Date:    April 2026

What it does:
    Takes Word, Excel, PowerPoint, or PDF files and converts them to Markdown (.md).
    It ONLY READS the source files — it never changes or saves over them.

How it works:
    1. It first tries fast Python libraries to read the file.
    2. If that fails (e.g. the file is IRM-protected, encrypted, or a legacy
       binary format), it falls back to opening the file read-only through
       the Office desktop app (via COM) using your Windows/M365 login.
    3. The extracted content is written as a clean Markdown file.

Fallback chain:
    Word  (.docx, .doc):       pandoc -> python-docx -> Office COM (Word)
    Excel (.xlsx, .xls):       openpyxl -> xlrd -> Office COM (Excel)
    PowerPoint (.pptx, .ppt):  python-pptx -> Office COM (PowerPoint)
    PDF   (.pdf):              PyMuPDF (fitz)

Usage:
    python convert_to_md.py <file_or_folder> [--output <output_dir>]

Examples:
    python convert_to_md.py report.docx
    python convert_to_md.py proposal.pdf
    python convert_to_md.py ./my_docs --output ./converted

Requirements:
    - Python 3.8+
    - Packages auto-installed on first run (python-docx, openpyxl, PyMuPDF, etc.)
    - For protected/legacy files: Microsoft Office installed + pywin32
    - Optional: pandoc (for best Word conversion quality)
"""

import argparse, json, shutil, subprocess, sys, tempfile, textwrap
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# ---------------------------------------------------------------------------
# Dependency bootstrap
# ---------------------------------------------------------------------------
def _try_import(name):
    try: __import__(name); return True
    except ImportError: return False

_PKGS = {"python-docx":"docx","openpyxl":"openpyxl","python-pptx":"pptx",
         "xlrd":"xlrd","msoffcrypto-tool":"msoffcrypto",
         "PyMuPDF":"fitz"}
# pywin32 is optional — only needed for COM fallback (IRM-protected / legacy binary files on Windows).
_HAS_WIN32COM = _try_import("win32com")

def _check_packages():
    missing = [p for p, m in _PKGS.items() if not _try_import(m)]
    if missing:
        raise ImportError(
            "Missing required packages: " + ", ".join(missing) + "\n"
            "Install them with:  pip install " + " ".join(missing) + "\n"
            "The SKILL.md Phase 1 workflow handles installation with user approval."
        )

_check_packages()

from docx import Document as DocxDocument          # noqa: E402
from docx.table import Table as DocxTable          # noqa: E402
from pptx import Presentation                      # noqa: E402
import openpyxl, xlrd, msoffcrypto                 # noqa: E402
import fitz                                        # noqa: E402  (PyMuPDF)

PANDOC = shutil.which("pandoc")
_OLE2_MAGIC = b"\xd0\xcf\x11\xe0"
_ZIP_MAGIC  = b"PK\x03\x04"
_ole2_cache: dict[str, bool] = {}        # path-str -> True/False
_enc_cache:  dict[str, bool] = {}        # path-str -> True/False
_QUIET = False                           # set via --quiet flag

def _log(msg: str):
    """Print unless --quiet is active."""
    if not _QUIET: print(msg)

# ---------------------------------------------------------------------------
# File-format detection (cached — each file is read at most once)
# ---------------------------------------------------------------------------
def _is_ole2(path: Path) -> bool:
    key = str(path)
    if key not in _ole2_cache:
        try:
            with open(path, "rb") as f: _ole2_cache[key] = f.read(4) == _OLE2_MAGIC
        except Exception: _ole2_cache[key] = False
    return _ole2_cache[key]

def _is_encrypted(path: Path) -> bool:
    key = str(path)
    if key not in _enc_cache:
        if not _is_ole2(path):
            _enc_cache[key] = False
        else:
            try:
                with open(path, "rb") as f: _enc_cache[key] = msoffcrypto.OfficeFile(f).is_encrypted()
            except Exception: _enc_cache[key] = False
    return _enc_cache[key]

def _classify(path: Path) -> str:
    if _is_encrypted(path): return "IRM/AIP-encrypted"
    if _is_ole2(path): return "legacy binary or protected"
    return "modern OOXML"

# ---------------------------------------------------------------------------
# Robustness: corrupt file detection & lock file detection
# ---------------------------------------------------------------------------
_LOCK_PATTERNS = ("~$", ".~lock.")  # Office & LibreOffice lock file prefixes

def _is_lock_file(path: Path) -> bool:
    return any(path.name.startswith(p) for p in _LOCK_PATTERNS)

def _check_file_health(path: Path) -> str | None:
    """Return an error message if the file looks corrupt/locked, else None."""
    if _is_lock_file(path):
        return "lock file (currently open in another app)"
    try:
        size = path.stat().st_size
    except OSError as e:
        return f"cannot access file ({e})"
    if size == 0:
        return "file is empty (0 bytes)"
    ext = path.suffix.lower()
    # Modern OOXML files (.docx, .xlsx, .pptx) must be ZIP archives
    # unless they're OLE2-wrapped (IRM/legacy)
    if ext in (".docx", ".xlsx", ".pptx") and not _is_ole2(path):
        try:
            with open(path, "rb") as f:
                magic = f.read(4)
            if magic != _ZIP_MAGIC:
                return f"file appears corrupt (expected ZIP header, got {magic.hex()})"
        except OSError as e:
            return f"cannot read file ({e})"
    return None

# ---------------------------------------------------------------------------
# Markdown helpers
# ---------------------------------------------------------------------------
def _esc(text: str) -> str:
    return text.replace("|", "\\|")

def _md_table(rows: list) -> str:
    if not rows: return ""
    ncols = max(len(r) for r in rows)
    rows = [r + [""] * (ncols - len(r)) for r in rows]
    lines = ["| " + " | ".join(rows[0]) + " |",
             "| " + " | ".join(["---"] * ncols) + " |"]
    lines.extend("| " + " | ".join(r) + " |" for r in rows[1:])
    return "\n".join(lines)

# ---------------------------------------------------------------------------
# COM read-only extraction (runs in isolated subprocess)
# ---------------------------------------------------------------------------
_COM_EXCEL = textwrap.dedent(r'''
import sys, json, pythoncom, traceback
pythoncom.CoInitialize()
import win32com.client as win32
app = None
try:
    app = win32.DispatchEx("Excel.Application")
    app.Visible = False; app.DisplayAlerts = False; app.AskToUpdateLinks = False
    wb = app.Workbooks.Open(sys.argv[1], UpdateLinks=0, ReadOnly=True)
    out = []
    for i in range(1, wb.Sheets.Count + 1):
        ws = wb.Sheets(i)
        used = ws.UsedRange
        if not used or used.Rows.Count == 0: continue
        data = used.Value
        if data is None: continue
        if not isinstance(data, tuple): data = ((data,),)
        elif data and not isinstance(data[0], tuple): data = (data,)
        out.append({"name": ws.Name,
                     "rows": [[str(c).strip() if c is not None else "" for c in r] for r in data]})
    wb.Close(False)
    with open(sys.argv[2], "w", encoding="utf-8") as f: json.dump(out, f, ensure_ascii=False)
except Exception: traceback.print_exc(); sys.exit(1)
finally:
    if app:
        try: app.Quit()
        except: pass
    pythoncom.CoUninitialize()
''')

_COM_PPTX = textwrap.dedent(r'''
import sys, json, pythoncom, traceback
pythoncom.CoInitialize()
import win32com.client as win32
app = None
try:
    app = win32.DispatchEx("PowerPoint.Application")
    app.DisplayAlerts = False
    prs = app.Presentations.Open(sys.argv[1], ReadOnly=True, WithWindow=False)
    out = []
    for i in range(1, prs.Slides.Count + 1):
        slide = prs.Slides(i); title = ""; body = []
        for j in range(1, slide.Shapes.Count + 1):
            shape = slide.Shapes(j)
            if shape.HasTextFrame:
                try: text = shape.TextFrame.TextRange.Text.strip()
                except: continue
                is_title = False
                try: is_title = shape.PlaceholderFormat.Type == 1
                except: pass
                if not is_title and shape.Name and "title" in shape.Name.lower(): is_title = True
                if is_title: title = text
                elif text: body.append(text)
            if shape.HasTable:
                tbl = shape.Table
                rows = []
                for r in range(1, tbl.Rows.Count + 1):
                    row = []
                    for c in range(1, tbl.Columns.Count + 1):
                        try: row.append(tbl.Cell(r, c).Shape.TextFrame.TextRange.Text.strip())
                        except: row.append("")
                    rows.append(row)
                body.append({"table": rows})
        notes = ""
        try: notes = slide.NotesPage.Shapes(2).TextFrame.TextRange.Text.strip()
        except: pass
        out.append({"index": i, "title": title, "body": body, "notes": notes})
    prs.Close()
    with open(sys.argv[2], "w", encoding="utf-8") as f: json.dump(out, f, ensure_ascii=False)
except Exception: traceback.print_exc(); sys.exit(1)
finally:
    if app:
        try: app.Quit()
        except: pass
    pythoncom.CoUninitialize()
''')

_COM_WORD = textwrap.dedent(r'''
import sys, json, pythoncom, traceback
pythoncom.CoInitialize()
import win32com.client as win32
app = None
try:
    app = win32.DispatchEx("Word.Application")
    app.Visible = False; app.DisplayAlerts = False
    doc = app.Documents.Open(sys.argv[1], ReadOnly=True)
    paras = []
    for i in range(1, doc.Paragraphs.Count + 1):
        p = doc.Paragraphs(i)
        paras.append({"text": p.Range.Text.strip(),
                       "style": p.Style.NameLocal if p.Style else ""})
    tables = []
    for i in range(1, doc.Tables.Count + 1):
        tbl = doc.Tables(i); rows = []
        for r in range(1, tbl.Rows.Count + 1):
            row = []
            for c in range(1, tbl.Columns.Count + 1):
                try: row.append(tbl.Cell(r, c).Range.Text.strip().replace("\r"," ").replace("\x07","").strip())
                except: row.append("")
            rows.append(row)
        tables.append(rows)
    doc.Close(False)
    with open(sys.argv[2], "w", encoding="utf-8") as f:
        json.dump({"paragraphs": paras, "tables": tables}, f, ensure_ascii=False)
except Exception: traceback.print_exc(); sys.exit(1)
finally:
    if app:
        try: app.Quit()
        except: pass
    pythoncom.CoUninitialize()
''')

_COM_SCRIPTS = {"excel": _COM_EXCEL, "powerpoint": _COM_PPTX, "word": _COM_WORD}

def _com_extract(src: Path, kind: str, timeout: int = 180, retries: int = 1) -> Path:
    """Open file via COM (read-only), extract content to temp JSON.
    Retries once on transient COM failures."""
    if sys.platform != "win32":
        raise RuntimeError(
            "COM requires Windows with Microsoft Office desktop installed. "
            "IRM-protected and legacy binary files cannot be converted on "
            f"{sys.platform}. Modern .docx/.xlsx/.pptx and PDF files work "
            "cross-platform."
        )
    if not _HAS_WIN32COM:
        raise RuntimeError(
            "pywin32 is not installed. COM fallback is required for this file "
            "(IRM-protected or legacy binary format). "
            "Install it with: pip install pywin32"
        )
    last_err = None
    for attempt in range(1 + retries):
        tmp_dir = Path(tempfile.mkdtemp(prefix="office_ext_"))
        out = tmp_dir / (src.stem + ".json")
        helper = tmp_dir / "_h.py"
        helper.write_text(_COM_SCRIPTS[kind], encoding="utf-8")
        try:
            r = subprocess.run([sys.executable, str(helper), str(src.resolve()), str(out)],
                               capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            for p in ("EXCEL", "POWERPNT", "WINWORD"):
                subprocess.run(["taskkill", "/F", "/IM", f"{p}.EXE"], capture_output=True)
            last_err = RuntimeError(f"COM timed out after {timeout}s")
            continue
        finally:
            helper.unlink(missing_ok=True)
        if r.returncode != 0:
            hint = (r.stderr.strip().splitlines() or ["unknown error"])[-1]
            last_err = RuntimeError(f"COM failed: {hint}")
            if attempt < retries:
                _log(f"  [warn] COM attempt {attempt+1} failed, retrying...")
                _cleanup(out)
                continue
            raise last_err
        if not out.exists() or out.stat().st_size == 0:
            last_err = RuntimeError("COM produced no output")
            if attempt < retries:
                _log(f"  [warn] COM attempt {attempt+1} produced no output, retrying...")
                _cleanup(out)
                continue
            raise last_err
        return out
    raise last_err  # all retries exhausted

def _cleanup(path: Path):
    try: path.unlink(missing_ok=True); path.parent.rmdir()
    except Exception: pass

# ---------------------------------------------------------------------------
# Word (.docx / .doc)
# ---------------------------------------------------------------------------
def _docx_via_pandoc(src: Path) -> str:
    r = subprocess.run([PANDOC, str(src), "-f", "docx", "-t", "markdown", "--wrap=none"],
                       capture_output=True, text=True, encoding="utf-8")
    if r.returncode == 0: return r.stdout
    raise RuntimeError(r.stderr)

def _para_to_md(para) -> str:
    style = (para.style.name or "").lower()
    parts = []
    for run in para.runs:
        t = run.text
        if run.bold: t = f"**{t}**"
        if run.italic: t = f"*{t}*"
        parts.append(t)
    text = "".join(parts)
    if not text.strip(): return ""
    if style.startswith("heading"):
        try: level = int(style.replace("heading", "").strip())
        except ValueError: level = 1
        return f"{'#' * level} {text}"
    if style.startswith("list"): return f"- {text}"
    return text

def _docx_via_python(src: Path) -> str:
    from docx.text.paragraph import Paragraph
    doc = DocxDocument(str(src))
    lines = []
    for el in doc.element.body:
        tag = el.tag.split("}")[-1]
        if tag == "p":
            md = _para_to_md(Paragraph(el, doc))
            if md: lines.append(md)
        elif tag == "tbl":
            tbl = DocxTable(el, doc)
            lines.append(_md_table([[_esc(c.text.strip()) for c in row.cells] for row in tbl.rows]))
    return "\n\n".join(lines)

def _com_word_to_md(json_path: Path) -> str:
    data = json.loads(json_path.read_text(encoding="utf-8"))
    lines = []
    for p in data.get("paragraphs", []):
        text, style = p["text"], p.get("style", "").lower()
        if not text: continue
        if "heading 1" in style:   lines.append(f"# {text}")
        elif "heading 2" in style: lines.append(f"## {text}")
        elif "heading 3" in style: lines.append(f"### {text}")
        elif "heading" in style:   lines.append(f"#### {text}")
        elif "list" in style:      lines.append(f"- {text}")
        else:                      lines.append(text)
    for tbl in data.get("tables", []):
        lines.append(f"\n{_md_table([[_esc(c) for c in r] for r in tbl])}\n")
    return "\n\n".join(lines)

def convert_docx(src: Path) -> str:
    if not _is_ole2(src):
        if PANDOC:
            try: return _docx_via_pandoc(src)
            except Exception: pass
        try: return _docx_via_python(src)
        except Exception as e: _log(f"  [warn] python-docx failed ({e})")
    _log(f"  [info] {src.name} is {_classify(src)}, reading via Office COM (Word)")
    jp = _com_extract(src, "word")
    try: return _com_word_to_md(jp)
    finally: _cleanup(jp)

# ---------------------------------------------------------------------------
# Excel (.xlsx / .xls)
# ---------------------------------------------------------------------------
def _xlsx_via_openpyxl(src: Path) -> str:
    wb = openpyxl.load_workbook(str(src), read_only=True, data_only=True)
    sections = []
    for name in wb.sheetnames:
        rows_raw = list(wb[name].iter_rows(values_only=True))
        if not rows_raw: continue
        rows_raw = [r for r in rows_raw if any(c is not None for c in r)] or rows_raw
        rows = [[_esc(str(c).strip()) if c is not None else "" for c in r] for r in rows_raw]
        sections.append(f"## {name}\n\n{_md_table(rows)}")
    wb.close()
    return "\n\n".join(sections)

def _xls_via_xlrd(src: Path) -> str:
    wb = xlrd.open_workbook(str(src))
    sections = []
    for sheet in wb.sheets():
        if sheet.nrows == 0: continue
        rows = [[_esc(str(sheet.cell_value(rx, cx)).strip()) for cx in range(sheet.ncols)]
                for rx in range(sheet.nrows)]
        sections.append(f"## {sheet.name}\n\n{_md_table(rows)}")
    return "\n\n".join(sections)

def _com_excel_to_md(json_path: Path) -> str:
    sheets = json.loads(json_path.read_text(encoding="utf-8"))
    return "\n\n".join(
        f"## {s['name']}\n\n{_md_table([[_esc(c) for c in r] for r in s['rows']])}"
        for s in sheets)

def convert_xlsx(src: Path) -> str:
    if not _is_ole2(src):
        try: return _xlsx_via_openpyxl(src)
        except Exception as e: _log(f"  [warn] openpyxl failed ({e})")
    try: return _xls_via_xlrd(src)
    except Exception as e: _log(f"  [warn] xlrd failed ({e})")
    _log(f"  [info] {src.name} is {_classify(src)}, reading via Office COM (Excel)")
    jp = _com_extract(src, "excel")
    try: return _com_excel_to_md(jp)
    finally: _cleanup(jp)

# ---------------------------------------------------------------------------
# PowerPoint (.pptx / .ppt)
# ---------------------------------------------------------------------------
def _pptx_via_python(src: Path) -> str:
    prs = Presentation(str(src))
    sections = []
    for idx, slide in enumerate(prs.slides, 1):
        title, body = "", []
        for shape in slide.shapes:
            if shape.has_text_frame:
                if shape == slide.shapes.title:
                    title = shape.text_frame.text.strip()
                else:
                    for para in shape.text_frame.paragraphs:
                        t = para.text.strip()
                        if t: body.append(f"{'  ' * (para.level or 0)}- {t}")
            if shape.has_table:
                rows = [[_esc(cell.text.strip()) for cell in row.cells] for row in shape.table.rows]
                if rows: body.append(f"\n{_md_table(rows)}\n")
        notes = ""
        if slide.has_notes_slide and slide.notes_slide.notes_text_frame:
            notes = slide.notes_slide.notes_text_frame.text.strip()
        md = f"## Slide {idx}" + (f": {title}" if title else "")
        if body: md += "\n\n" + "\n".join(body)
        if notes: md += f"\n\n> **Notes:** {notes}"
        sections.append(md)
    return "\n\n---\n\n".join(sections)

def _com_pptx_to_md(json_path: Path) -> str:
    slides = json.loads(json_path.read_text(encoding="utf-8"))
    sections = []
    for s in slides:
        heading = f"## Slide {s['index']}" + (f": {s['title']}" if s.get("title") else "")
        body = []
        for item in s.get("body", []):
            if isinstance(item, dict) and "table" in item:
                body.append(f"\n{_md_table([[_esc(c) for c in r] for r in item['table']])}\n")
            else:
                body.append(f"- {item}")
        md = heading
        if body: md += "\n\n" + "\n".join(body)
        if s.get("notes"): md += f"\n\n> **Notes:** {s['notes']}"
        sections.append(md)
    return "\n\n---\n\n".join(sections)

def convert_pptx(src: Path) -> str:
    if not _is_ole2(src):
        try: return _pptx_via_python(src)
        except Exception as e: _log(f"  [warn] python-pptx failed ({e})")
    _log(f"  [info] {src.name} is {_classify(src)}, reading via Office COM (PowerPoint)")
    jp = _com_extract(src, "powerpoint")
    try: return _com_pptx_to_md(jp)
    finally: _cleanup(jp)

# ---------------------------------------------------------------------------
# PDF (.pdf)
# ---------------------------------------------------------------------------
def convert_pdf(src: Path) -> str:
    """Extract text from a PDF file using PyMuPDF (fitz).
    Preserves headings (detected via font size), tables, and page structure."""
    doc = fitz.open(str(src))
    sections = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        blocks = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)["blocks"]
        page_lines = []
        for block in blocks:
            if block["type"] != 0:  # skip image blocks
                continue
            for line in block["lines"]:
                spans = line["spans"]
                if not spans:
                    continue
                text = "".join(s["text"] for s in spans).strip()
                if not text:
                    continue
                # Detect headings by font size (largest spans)
                max_size = max(s["size"] for s in spans)
                is_bold = any("bold" in s["font"].lower() for s in spans)
                if max_size >= 18:
                    page_lines.append(f"# {text}")
                elif max_size >= 15 or (max_size >= 13 and is_bold):
                    page_lines.append(f"## {text}")
                elif max_size >= 12 and is_bold:
                    page_lines.append(f"### {text}")
                else:
                    page_lines.append(text)
        # Also try to extract tables from the page
        tables = page.find_tables()
        for table in tables:
            rows = table.extract()
            if rows:
                md_rows = [[_esc(str(c).strip()) if c else "" for c in r] for r in rows]
                page_lines.append(f"\n{_md_table(md_rows)}\n")
        if page_lines:
            sections.append(f"<!-- Page {page_num + 1} -->\n\n" + "\n\n".join(page_lines))
    doc.close()
    return "\n\n---\n\n".join(sections)

# ---------------------------------------------------------------------------
# Dispatcher & CLI
# ---------------------------------------------------------------------------
CONVERTERS = {
    ".docx": convert_docx, ".doc": convert_docx,
    ".xlsx": convert_xlsx, ".xls": convert_xlsx,
    ".pptx": convert_pptx, ".ppt": convert_pptx,
    ".pdf": convert_pdf,
}
SUPPORTED = set(CONVERTERS)

_STREAM_THRESHOLD = 512 * 1024  # 512 KB — stream-write files above this size

def convert_file(src: Path, output_dir: Path, index: int = 0, total: int = 0) -> str:
    prefix = f"[{index}/{total}] " if total > 0 else ""
    # Health check
    issue = _check_file_health(src)
    if issue: return f"{prefix}SKIP  {src.name}  ({issue})"
    conv = CONVERTERS.get(src.suffix.lower())
    if not conv: return f"{prefix}SKIP  {src.name} (unsupported)"
    try:
        md = conv(src)
        out = output_dir / (src.stem + ".md")
        if len(md) > _STREAM_THRESHOLD:
            with open(out, "w", encoding="utf-8", buffering=64*1024) as f:
                f.write(md)
        else:
            out.write_text(md, encoding="utf-8")
        return f"{prefix}OK    {src.name}  ->  {out.name}  ({out.stat().st_size / 1024:.0f} KB)"
    except Exception as e:
        return f"{prefix}FAIL  {src.name}  ({e})"

def main():
    ap = argparse.ArgumentParser(description="Convert Office and PDF files to Markdown.")
    ap.add_argument("input", help="File or folder to convert.")
    ap.add_argument("--output", "-o", default=None, help="Output directory.")
    ap.add_argument("--workers", "-w", type=int, default=4, help="Parallel workers (default: 4).")
    ap.add_argument("--dry-run", action="store_true",
                    help="List files that would be converted without converting them.")
    ap.add_argument("--quiet", "-q", action="store_true",
                    help="Suppress info/warn messages. Only show OK/FAIL/SKIP per file.")
    args = ap.parse_args()

    global _QUIET
    _QUIET = args.quiet

    src = Path(args.input).resolve()
    if not src.exists():
        print(f"Error: {src} does not exist."); sys.exit(1)

    if src.is_file():
        files, default_out = [src], src.parent / "md_output"
    else:
        files = sorted(f for f in src.rglob("*")
                       if f.suffix.lower() in SUPPORTED
                       and not f.name.startswith("~")
                       and not _is_lock_file(f))
        default_out = src / "md_output"

    out_dir = Path(args.output).resolve() if args.output else default_out
    out_dir.mkdir(parents=True, exist_ok=True)

    if not files:
        print("No supported Office files found."); sys.exit(0)

    print(f"{'[DRY RUN] Would convert' if args.dry_run else 'Converting'} {len(files)} file(s)  ->  {out_dir}")

    if args.dry_run:
        for f in files:
            cls = _classify(f)
            size_kb = f.stat().st_size / 1024
            print(f"  {f.name}  ({size_kb:.0f} KB, {cls})")
        print("Done (dry run — nothing converted).")
        return

    if PANDOC: _log(f"[info] pandoc found at {PANDOC}")
    else:      _log("[info] pandoc not found — using python-docx fallback for .docx")

    legacy = [f for f in files if _is_ole2(f)]
    modern = [f for f in files if not _is_ole2(f)]
    total = len(files)
    counter = [0]  # mutable for closure access in threads

    if legacy:
        enc = sum(1 for f in legacy if _is_encrypted(f))
        leg = len(legacy) - enc
        parts = ([f"{enc} IRM/encrypted"] if enc else []) + ([f"{leg} legacy"] if leg else [])
        _log(f"[info] {', '.join(parts)} file(s) — using Office COM with your credentials")

    for f in legacy:
        counter[0] += 1
        print(convert_file(f, out_dir, counter[0], total))
    if modern:
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futs = {pool.submit(convert_file, f, out_dir): f for f in modern}
            for fut in as_completed(futs):
                counter[0] += 1
                # Re-format with counter (thread results don't have index yet)
                result = fut.result()
                # Inject progress prefix if not already present
                if not result.startswith("["):
                    result = f"[{counter[0]}/{total}] {result}"
                print(result)
    print("Done.")

if __name__ == "__main__":
    main()
