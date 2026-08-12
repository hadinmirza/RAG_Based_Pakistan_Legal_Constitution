from pathlib import Path

import chromadb
from langchain_huggingface import HuggingFaceEmbeddings

PERSIST_DIR = Path("data/chroma_db")
COLLECTION_NAME = "pakistan_constitution"

MODEL_NAME = "BAAI/bge-small-en-v1.5"
QUERY_INSTRUCTION = "Represent this sentence for searching relevant passages: "

embedder = HuggingFaceEmbeddings(
    model_name=MODEL_NAME,
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True},
)

client = chromadb.PersistentClient(path=str(PERSIST_DIR))
collection = client.get_collection(COLLECTION_NAME)


def retrieve(query, k=5, part_filter=None):
    query_vector = embedder.embed_query(QUERY_INSTRUCTION + query)

    where = {"part": part_filter} if part_filter else None

    results = collection.query(
        query_embeddings=[query_vector],
        n_results=k,
        where=where,
        include=["documents", "metadatas", "distances"],
    )

    hits = []
    for doc, meta, dist in zip(results["documents"][0], results["metadatas"][0], results["distances"][0]):
        hits.append({
            "chunk_id": meta["chunk_id"],
            "article": meta["article"],
            "title": meta["title"],
            "part": meta["part"],
            "chapter": meta["chapter"],
            "text": doc,
            "distance": dist,
        })
    return hits


if __name__ == "__main__":
    query = "right to fair trial"
    print(f"Query: {query}\n")

    hits = retrieve(query, k=5)
    for h in hits:
        print(f"[{h['chunk_id']}] Article {h['article']}: {h['title']} (distance={h['distance']:.4f})")
        print(f"  {h['text'][:150]}")
        print()

    print("---")
    print("Filtered query (part=PART II):")
    hits = retrieve(query, k=5, part_filter="PART II")
    for h in hits:
        print(f"[{h['chunk_id']}] Article {h['article']}: {h['title']} (distance={h['distance']:.4f})")