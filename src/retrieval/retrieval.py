import re
from pathlib import Path

import chromadb
from langchain_huggingface import HuggingFaceEmbeddings

PERSIST_DIR = Path("data/chroma_db")
COLLECTION_NAME = "pakistan_constitution"

MODEL_NAME = "BAAI/bge-small-en-v1.5"
QUERY_INSTRUCTION = "Represent this sentence for searching relevant passages: "

# Matches "article 25", "Article 25A", "article 267b", "Art. 199" etc.
ARTICLE_MENTION_RE = re.compile(
    r"art(?:icle)?\.?\s+(\d{1,3}[a-zA-Z]{0,2})", re.IGNORECASE
)

embedder = HuggingFaceEmbeddings(
    model_name=MODEL_NAME,
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True},
)

client = chromadb.PersistentClient(path=str(PERSIST_DIR))
collection = client.get_collection(COLLECTION_NAME)


def _hits_from_results(results):
    hits = []
    if not results["documents"] or not results["documents"][0]:
        return hits
    for doc, meta, dist in zip(
        results["documents"][0], results["metadatas"][0], results["distances"][0]
    ):
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


def retrieve(query, k=5, part_filter=None):
    query_vector = embedder.embed_query(QUERY_INSTRUCTION + query)

    # ------------------------------------------------------------------
    # Exact-match short-circuit: if the query names a specific article
    # number, go straight to a metadata filter instead of trusting dense
    # similarity to find it. Numbers carry very little semantic signal
    # in embedding space, so "what does article 25 say" can easily score
    # article 25's own chunk LOWER than unrelated articles that happen
    # to share more topical vocabulary. Metadata filtering sidesteps
    # that entirely -- we already know exactly which article it is.
    # ------------------------------------------------------------------
    article_match = ARTICLE_MENTION_RE.search(query)
    if article_match:
        article_number = article_match.group(1).upper()

        if part_filter:
            where = {"$and": [{"article": article_number}, {"part": part_filter}]}
        else:
            where = {"article": article_number}

        results = collection.query(
            query_embeddings=[query_vector],
            n_results=k,
            where=where,
            include=["documents", "metadatas", "distances"],
        )
        hits = _hits_from_results(results)
        if hits:
            return hits
        # article number mentioned but not found (e.g. omitted/repealed,
        # or just doesn't exist) -- fall through to normal semantic
        # search below rather than returning nothing

    # ------------------------------------------------------------------
    # Normal semantic search for open-ended / topical questions
    # ------------------------------------------------------------------
    where = {"part": part_filter} if part_filter else None

    results = collection.query(
        query_embeddings=[query_vector],
        n_results=k,
        where=where,
        include=["documents", "metadatas", "distances"],
    )
    return _hits_from_results(results)


if __name__ == "__main__":
    query = "right to fair trial"
    print(f"Query: {query}\n")

    hits = retrieve(query, k=5)
    for h in hits:
        print(f"[{h['chunk_id']}] Article {h['article']}: {h['title']} (distance={h['distance']:.4f})")
        print(f"  {h['text'][:150]}")
        print()

    print("---")
    print("Exact-lookup query test:")
    query2 = "what does article 25 say"
    hits2 = retrieve(query2, k=5)
    for h in hits2:
        print(f"[{h['chunk_id']}] Article {h['article']}: {h['title']} (distance={h['distance']:.4f})")

    print("---")
    print("Filtered query (part=PART II):")
    hits = retrieve(query, k=5, part_filter="PART II")
    for h in hits:
        print(f"[{h['chunk_id']}] Article {h['article']}: {h['title']} (distance={h['distance']:.4f})")