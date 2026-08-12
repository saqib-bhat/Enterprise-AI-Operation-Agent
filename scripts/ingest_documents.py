from __future__ import annotations
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from app.rag.ingestion import ingest_documents
from app.rag.chunking import chunk_documents
from app.rag.embeddings import embed_texts
from app.rag.vector_store import build_index, save_index, load_index, index_exists
import json
import os


def ensure_documents_exist():
    # create sample PDFs if not present using reportlab
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    outdir = Path('data/documents')
    outdir.mkdir(parents=True, exist_ok=True)

    samples = {
        'inventory_policy.pdf': [
            'Inventory Policy',
            'Reorder thresholds: maintain minimum stock levels. Approval required for orders over $10,000.',
            'Maximum stock levels: Do not exceed max capacity. Stock variance rules and cycle counts monthly.'
        ],
        'vendor_policy.pdf': [
            'Vendor Policy',
            'Vendor pricing rules: require three quotes for purchases over $5,000.',
            'Vendor evaluation: annual reviews, contract requirements, procurement approval process.'
        ],
        'operations_sop.pdf': [
            'Operations SOP',
            'Inventory procedures: receiving, inspection, reconciliation steps.',
            'Escalation procedures and purchasing procedures for emergency restocks.'
        ]
    }

    for name, pages in samples.items():
        path = outdir / name
        if path.exists():
            continue
        c = canvas.Canvas(str(path), pagesize=letter)
        for p in pages:
            c.setFont('Helvetica', 12)
            c.drawString(72, 720, p)
            c.showPage()
        c.save()


def ingest_all(chunk_size=800, overlap=200):
    ensure_documents_exist()
    docs = ingest_documents(Path('data/documents'))
    chunks = chunk_documents(docs, chunk_size=chunk_size, overlap=overlap)
    texts = [c['text'] for c in chunks]
    if not texts:
        print('No text to embed')
        return 1
    embs = embed_texts(texts)
    index = build_index(embs)
    # metadata includes chunk order corresponding to embeddings
    metadata = [{k: v for k, v in c.items()} for c in chunks]
    save_index(index, metadata)
    print(f'Indexed {len(metadata)} chunks')
    return 0


if __name__ == '__main__':
    raise SystemExit(ingest_all())
