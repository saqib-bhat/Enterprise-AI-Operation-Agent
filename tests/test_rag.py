from pathlib import Path
from app.rag.ingestion import extract_text_from_pdf, ingest_documents
from app.rag.chunking import chunk_documents
from app.rag.embeddings import get_model, embed_texts
from app.rag.vector_store import build_index, save_index, load_index, INDEX_PATH, METADATA_PATH
from app.rag.retrieval import retrieve
import os
import sys
import json
import subprocess


def _run_rag_subprocess(script: str):
    root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env['PYTHONPATH'] = str(root)
    result = subprocess.run(
        [sys.executable, '-c', script],
        capture_output=True,
        text=True,
        cwd=root,
        env=env,
    )
    if result.returncode != 0:
        raise AssertionError(
            f"Subprocess failed with return code {result.returncode}\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )
    lines = [line for line in result.stdout.strip().splitlines() if line.strip()]
    if not lines:
        raise AssertionError("Subprocess returned no output")
    return json.loads(lines[-1])


def test_ingest_and_chunk(tmp_path):
    script = r'''
import json
from pathlib import Path
from scripts import ingest_documents as ingest_module
from app.rag.ingestion import ingest_documents as ingest_fn
from app.rag.chunking import chunk_documents

ingest_module.ingest_all()
docs = ingest_fn(Path('data/documents'))
chunks = chunk_documents(docs, chunk_size=50, overlap=10)
print(json.dumps({'docs': bool(docs), 'chunks': bool(chunks)}))
'''
    result = _run_rag_subprocess(script)
    assert result['docs'] is True
    assert result['chunks'] is True


def test_embeddings_and_faiss():
    script = r'''
import json
from pathlib import Path
from app.rag.ingestion import ingest_documents
from app.rag.chunking import chunk_documents
from app.rag.embeddings import get_model, embed_texts
from app.rag.vector_store import build_index, save_index, load_index

Docs = ingest_documents(Path('data/documents'))
chunks = chunk_documents(Docs, chunk_size=50, overlap=10)
texts = [c['text'] or '' for c in chunks]
model = get_model()
embs = embed_texts(texts[:10])
index = build_index(embs)
save_index(index, chunks[:10])
idx, meta = load_index()
print(json.dumps({'shape': list(embs.shape), 'idx': idx is not None, 'meta_len': len(meta)}))
'''
    result = _run_rag_subprocess(script)
    assert result['shape'][1] == 384
    assert result['idx'] is True
    assert isinstance(result['meta_len'], int)


def test_retrieval_and_citations():
    script = r'''
import json
from scripts import ingest_documents
from app.rag.retrieval import retrieve

ingest_documents.ingest_all()
res = retrieve('reorder thresholds', top_k=3)
results = res.get('results', [])
valid = all(
    all(k in r for k in ('chunk_id', 'source', 'page', 'text'))
    for r in results[:1]
)
print(json.dumps({'success': res.get('success', False), 'results': len(results), 'valid': valid}))
'''
    result = _run_rag_subprocess(script)
    assert result['success'] is True
    assert isinstance(result['results'], int)
    assert result['valid'] is True
