"""Turn files (.txt, .md, .pdf, .docx, .csv, .json/.jsonl) into plain text.

Each loader returns one string. The Chunker then splits that string.
Heavy libraries are imported only when needed, so you only have to install
the ones for the formats you actually use.
"""

import csv
import json
import re
from pathlib import Path

SUPPORTED_EXTENSIONS = (".txt", ".md", ".pdf", ".docx", ".csv", ".json", ".jsonl")


# ---------- helpers ----------

def _read_text_file(path):
    return Path(path).read_text(encoding="utf-8-sig", errors="replace")


def _end_sentence(line):
    """Make sure a line ends with sentence punctuation so it splits cleanly."""
    line = line.strip()
    if line and line[-1] not in ".!?":
        line += "."
    return line


def _require(module_name, pip_name):
    try:
        return __import__(module_name)
    except ImportError as e:
        raise ImportError(
            f"Reading this file type needs '{pip_name}'. "
            f"Install it with: pip install {pip_name}"
        ) from e


# ---------- loaders ----------

def load_txt(path):
    return _read_text_file(path)


def load_md(path):
    """Read Markdown and strip common syntax, keeping the readable text."""
    text = _read_text_file(path)
    text = re.sub(r"```[^\n]*\n?", "", text)                  # code fence lines
    text = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"\1", text)      # images -> alt text
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)       # links -> link text
    text = re.sub(r"^\s{0,3}#{1,6}\s*", "", text, flags=re.M)  # heading markers
    text = re.sub(r"^\s*>\s?", "", text, flags=re.M)           # blockquotes
    text = re.sub(r"^\s*([-*+]|\d+\.)\s+", "", text, flags=re.M)  # list bullets
    text = re.sub(r"(\*\*|__|\*|_|~~|`)", "", text)            # bold/italic/code
    text = re.sub(r"^\s*([-*_]\s*){3,}$", "", text, flags=re.M)  # horizontal rules
    return text


def load_pdf(path):
    pypdf = _require("pypdf", "pypdf")
    reader = pypdf.PdfReader(str(path))
    pages = [(page.extract_text() or "").strip() for page in reader.pages]
    text = "\n\n".join(p for p in pages if p)
    if not text:
        raise ValueError(
            "No extractable text found in this PDF. It may be a scanned "
            "document; run OCR (e.g. pytesseract) first."
        )
    return text


def load_docx(path):
    docx = _require("docx", "python-docx")
    doc = docx.Document(str(path))
    blocks = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    for table in doc.tables:
        for row in table.rows:
            cells = [c.text.strip() for c in row.cells if c.text.strip()]
            if cells:
                blocks.append(_end_sentence(" | ".join(cells)))
    return "\n\n".join(blocks)


def load_csv(path):
    """Each row becomes one sentence: 'column: value; column: value.'"""
    lines = []
    with open(path, newline="", encoding="utf-8-sig", errors="replace") as f:
        for row in csv.DictReader(f):
            pairs = [
                f"{k.strip()}: {v.strip()}"
                for k, v in row.items()
                if k and v and v.strip()
            ]
            if pairs:
                lines.append(_end_sentence("; ".join(pairs)))
    return "\n".join(lines)


def _flatten_json(obj, key=None):
    """Yield readable lines for every value in a JSON structure."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from _flatten_json(v, str(k))
    elif isinstance(obj, list):
        for item in obj:
            yield from _flatten_json(item, key)
    elif obj is not None:
        value = str(obj).strip()
        if value:
            yield _end_sentence(f"{key}: {value}" if key else value)


def load_json(path):
    """Handles a normal .json file or a .jsonl file (one object per line)."""
    raw = _read_text_file(path)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        data = [json.loads(line) for line in raw.splitlines() if line.strip()]
    return "\n".join(_flatten_json(data))


_LOADERS = {
    ".txt": load_txt,
    ".md": load_md,
    ".pdf": load_pdf,
    ".docx": load_docx,
    ".csv": load_csv,
    ".json": load_json,
    ".jsonl": load_json,
}


def load_text(path):
    """Pick the right loader from the file extension and return plain text."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"File not found: {path}")
    ext = path.suffix.lower()
    loader = _LOADERS.get(ext)
    if loader is None:
        raise ValueError(
            f"Unsupported file type '{ext}'. "
            f"Supported: {', '.join(SUPPORTED_EXTENSIONS)}"
        )
    return loader(path)
