from __future__ import annotations
import os
from pathlib import Path
from typing import List, Dict
import uuid
from pypdf import PdfReader



def extract_text_from_pdf(path: Path) -> List[Dict]:
    """Extract text from each page of a PDF; return list of dicts with filename, page_number, text."""
    results = []
    try:
        reader = PdfReader(str(path))
        for i, page in enumerate(reader.pages, start=1):
            try:
                text = page.extract_text() or ""
            except Exception:
                text = ""
            results.append({"source": path.name, "page": i, "text": text})
    except Exception:
        # return empty for error but preserve filename
        results.append({"source": path.name, "page": None, "text": ""})
    return results


def ingest_documents(folder: Path) -> List[Dict]:
    folder = Path(folder)
    docs = []
    if not folder.exists():
        return docs
    for fp in sorted(folder.iterdir()):
        if fp.suffix.lower() != ".pdf":
            continue
        extracted = extract_text_from_pdf(fp)
        docs.extend(extracted)
    return docs
