import json
from pathlib import Path
 
import numpy as np
from langchain_huggingface import HuggingFaceEmbeddings
 
CHUNKS_PATH = Path("data/processed/constitution_chunks.json")
EMBEDDINGS_DIR = Path("data/embeddings")
EMBEDDINGS_PATH = EMBEDDINGS_DIR / "embeddings.npy"
METADATA_PATH = EMBEDDINGS_DIR / "metadata.json"
 
MODEL_NAME = "BAAI/bge-small-en-v1.5"
 
# BGE models want this prefix on the QUERY at search time (not on indexed documents).
# Save it alongside the embeddings so the next feature (vector DB / retrieval) knows
# to apply it -- don't hardcode this separately in two places.
QUERY_INSTRUCTION = "Represent this sentence for searching relevant passages: "
 
 
def load_chunks(path=CHUNKS_PATH):
    with open(path, encoding="utf-8") as f:
        return json.load(f)  # list of {"page_content": ..., "metadata": {...}}
 
 
def build_embedder():
    # Note: langchain-huggingface's HuggingFaceEmbeddings has no query_instruction
    # param -- that belongs to an older/different wrapper class. This file only
    # embeds DOCUMENTS anyway (embed_documents), which don't need the instruction
    # prefix. QUERY_INSTRUCTION is saved into metadata.json so the next feature
    # (vector DB / retrieval) can manually prepend it before calling embed_query().
    return HuggingFaceEmbeddings(
        model_name=MODEL_NAME,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},  # bge models expect cosine sim on normalized vectors
    )
 
 
def embed_chunks(chunks, embedder):
    texts = [c["page_content"] for c in chunks]
    vectors = embedder.embed_documents(texts)
    return np.array(vectors, dtype="float32")
 
 
def save_embeddings(vectors, chunks, embeddings_path=EMBEDDINGS_PATH, metadata_path=METADATA_PATH):
    embeddings_path.parent.mkdir(parents=True, exist_ok=True)
    np.save(embeddings_path, vectors)
 
    metadata_payload = {
        "model_name": MODEL_NAME,
        "query_instruction": QUERY_INSTRUCTION,
        "embedding_dim": int(vectors.shape[1]),
        "count": int(vectors.shape[0]),
        "chunks": chunks,  # same order as embeddings.npy rows
    }
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata_payload, f, indent=2, ensure_ascii=False)
 
 
if __name__ == "__main__":
    print("EMBEDDING GENERATION")
 
    chunks = load_chunks()
    print(f"Chunks loaded: {len(chunks)}")
 
    embedder = build_embedder()
    print(f"Model: {MODEL_NAME}")
 
    vectors = embed_chunks(chunks, embedder)
    print(f"Embeddings shape: {vectors.shape}")
 
    save_embeddings(vectors, chunks)
    print(f"Saved -> {EMBEDDINGS_PATH}")
    print(f"Saved -> {METADATA_PATH}")