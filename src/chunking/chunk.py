import re
import json
from pathlib import Path
 
from langchain_core.documents import Document
 
try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    from langchain.text_splitter import RecursiveCharacterTextSplitter
 
INPUT_PATH = Path("data/processed/constitution_articles.json")
OUTPUT_PATH = Path("data/processed/constitution_chunks.json")
 
MAX_CHUNK_CHARS = 1200      # target chunk size (roughly 250-300 tokens)
MIN_CHUNK_CHARS = 200       # merge threshold - avoid shipping tiny leftover clause fragments
CHUNK_OVERLAP = 100         # only used by the raw-text fallback splitter
 
# Matches the start of a top-level numbered clause: (1)  (2)  (2A)  (17AAA) ...
# Deliberately does NOT match lettered sub-clauses like (a) (b), so we split at the
# level a lawyer would call a "clause", not down at "sub-clause", keeping chunks coherent.
#
# IMPORTANT: legal text constantly cross-references other clauses inline, e.g.
# "...the rights conferred by clause (1)..." -- that "(1)" is NOT a new clause, it's a
# reference. We only split when the "(N)" is preceded by a sentence/clause boundary
# (". ", "; ", ") ") or sits at the very start of the text, so references embedded
# mid-sentence are left alone and only genuine clause openings get split on.
CLAUSE_SPLIT_RE = re.compile(r"(?:(?<=\.\s)|(?<=;\s)|(?<=\)\s))(?=\(\d+[A-Z]{0,3}\)\s)")
 
_fallback_splitter = RecursiveCharacterTextSplitter(
    chunk_size=MAX_CHUNK_CHARS,
    chunk_overlap=CHUNK_OVERLAP,
    separators=["\n", ". ", "; ", ", ", " ", ""],
)
 
 
def _split_into_clauses(text):
    """Split article text on top-level numbered clause markers: (1) (2) (2A) ..."""
    parts = CLAUSE_SPLIT_RE.split(text)
    return [p.strip() for p in parts if p.strip()]
 
 
def _pack_clauses(clauses, max_chars=MAX_CHUNK_CHARS, min_chars=MIN_CHUNK_CHARS):
    """Greedily merge consecutive clauses into chunks close to max_chars.
    Any single clause that is itself oversized gets handed to the fallback splitter."""
    chunks, buf = [], ""
    for clause in clauses:
        if len(clause) > max_chars:
            if buf:
                chunks.append(buf)
                buf = ""
            chunks.extend(_fallback_splitter.split_text(clause))
            continue
        candidate = f"{buf} {clause}".strip() if buf else clause
        if len(candidate) <= max_chars:
            buf = candidate
        else:
            if buf:
                chunks.append(buf)
            buf = clause
    if buf:
        chunks.append(buf)
 
    # don't ship a trailing crumb -- fold it back into its predecessor
    if len(chunks) > 1 and len(chunks[-1]) < min_chars:
        chunks[-2] = f"{chunks[-2]} {chunks[-1]}".strip()
        chunks.pop()
    return chunks
 
 
def _header(record):
    bits = [f"Article {record['article']}: {record['title']}"]
    ctx = " | ".join(x for x in (record.get("part"), record.get("chapter")) if x)
    if ctx:
        bits.append(f"({ctx})")
    return " ".join(bits)
 
 
def chunk_article(record):
    """Turn a single article record into 1..N Document chunks."""
    text = record["text"].strip()
    header = _header(record)
 
    if len(text) <= MAX_CHUNK_CHARS:
        pieces = [text]
    else:
        clauses = _split_into_clauses(text)
        # no numbered clauses found (rare: one long prose paragraph) -> raw fallback splitter
        pieces = _pack_clauses(clauses) if len(clauses) > 1 else _fallback_splitter.split_text(text)
 
    total = len(pieces)
    docs = []
    for i, piece in enumerate(pieces, start=1):
        suffix = f" [part {i}/{total}]" if total > 1 else ""
        content = f"{header}{suffix}\n\n{piece}"
        docs.append(Document(
            page_content=content,
            metadata={
                "chunk_id": f"art-{record['article']}-{i}",
                "article": record["article"],
                "title": record["title"],
                "part": record["part"],
                "chapter": record["chapter"],
                "page_start": record["page_start"],
                "page_end": record["page_end"],
                "chunk_index": i,
                "total_chunks": total,
            },
        ))
    return docs
 
 
def chunk_records(records):
    documents = []
    for record in records:
        documents.extend(chunk_article(record))
    return documents
 
 
def save_chunks(documents, path=OUTPUT_PATH):
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = [{"page_content": d.page_content, "metadata": d.metadata} for d in documents]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
 
 
if __name__ == "__main__":
    with open(INPUT_PATH, encoding="utf-8") as f:
        records = json.load(f)
 
    documents = chunk_records(records)
 
    print("CONSTITUTION CHUNKER")
    print(f"Articles in:  {len(records)}")
    print(f"Chunks out:   {len(documents)}")
 
    multi = [d for d in documents if d.metadata["total_chunks"] > 1]
    print(f"Articles split into >1 chunk: {len({d.metadata['article'] for d in multi})}")
 
    if multi:
        art = multi[0].metadata["article"]
        print(f"\nSample multi-chunk article: {art}")
        for d in [d for d in documents if d.metadata["article"] == art]:
            print(f"\n--- {d.metadata['chunk_id']} ({len(d.page_content)} chars) ---")
            print(d.page_content[:300])
 
    save_chunks(documents)
    print(f"\nSaved -> {OUTPUT_PATH}")

import json
with open("data/processed/constitution_chunks.json", encoding="utf-8") as f:
    chunks = json.load(f)

for c in chunks:
    body = c["page_content"].split("\n\n", 1)[-1].strip()
    if body and not (body[0].isupper() or body[0] == "("):
        print(c["metadata"]["chunk_id"], "->", body[:60])