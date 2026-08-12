import json
from pathlib import Path
 
import numpy as np
import chromadb
 
EMBEDDINGS_PATH = Path("data/embeddings/embeddings.npy")
METADATA_PATH = Path("data/embeddings/metadata.json")
PERSIST_DIR = Path("data/chroma_db")
COLLECTION_NAME = "pakistan_constitution"
 
BATCH_SIZE = 200  # chromadb internal max batch size; My 488 rows fit in ~3 batches
 
def load_embeddings_and_chunks(embeddings_path=EMBEDDINGS_PATH, metadata_path=METADATA_PATH):
    vectors = np.load(embeddings_path)
 
    with open(metadata_path, encoding="utf-8") as f:
        payload = json.load(f)
    chunks = payload["chunks"]
 
    if len(chunks) != vectors.shape[0]:
        raise ValueError(
            f"Mismatch: {len(chunks)} chunks in metadata.json but "
            f"{vectors.shape[0]} rows in embeddings.npy -- did embed.py run to completion?"
        )
    return vectors, chunks, payload
 
 
def clean_metadata(metadata):
    return {k: ("" if v is None else v) for k, v in metadata.items()}
 
 
def build_collection(vectors, chunks, persist_dir=PERSIST_DIR, collection_name=COLLECTION_NAME):
    persist_dir.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(persist_dir))
 
    existing = [c.name for c in client.list_collections()]
    if collection_name in existing:
        client.delete_collection(collection_name)
 
    collection = client.create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}, 
    )
 
    ids = [c["metadata"]["chunk_id"] for c in chunks]
    documents = [c["page_content"] for c in chunks]
    metadatas = [clean_metadata(c["metadata"]) for c in chunks]
    embeddings = vectors.tolist()
 
    for start in range(0, len(ids), BATCH_SIZE):
        end = start + BATCH_SIZE
        collection.add(
            ids=ids[start:end],
            embeddings=embeddings[start:end],
            documents=documents[start:end],
            metadatas=metadatas[start:end],
        )
 
    return collection
 
 
if __name__ == "__main__":
    print("VECTOR DB INDEXING")
 
    vectors, chunks, payload = load_embeddings_and_chunks()
    print(f"Embeddings loaded: {vectors.shape}")
    print(f"Model used to generate them: {payload['model_name']}")
 
    collection = build_collection(vectors, chunks)
    print(f"Collection '{COLLECTION_NAME}' created at: {PERSIST_DIR}")
    print(f"Vectors indexed: {collection.count()}")

    sample_id = chunks[0]["metadata"]["chunk_id"]
    fetched = collection.get(ids=[sample_id], include=["documents", "metadatas"])
    print(f"\nSample fetch for id '{sample_id}':")
    print(f"  metadata: {fetched['metadatas'][0]}")
    print(f"  document (first 100 chars): {fetched['documents'][0][:100]}")