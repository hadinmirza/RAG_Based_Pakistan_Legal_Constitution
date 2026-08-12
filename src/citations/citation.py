import re
from src.LLM.LLM import answer

CITATION_RE = re.compile(r"Article (\d+[A-Z]*)")


def extract_citations(answer_text):
    return sorted(set(CITATION_RE.findall(answer_text)))


def verify_citations(cited_articles, hits):
    retrieved_articles = {h["article"] for h in hits}
    valid = [a for a in cited_articles if a in retrieved_articles]
    hallucinated = [a for a in cited_articles if a not in retrieved_articles]
    return valid, hallucinated


def answer_with_citations(query, k=5):
    answer_text, hits = answer(query, k=k)
    cited = extract_citations(answer_text)
    valid, hallucinated = verify_citations(cited, hits)

    citations = []
    for article in valid:
        match = next(h for h in hits if h["article"] == article)
        citations.append({
            "article": match["article"],
            "title": match["title"],
            "chunk_id": match["chunk_id"],
        })

    return {
        "answer": answer_text,
        "citations": citations,
        "hallucinated_citations": hallucinated,
        "sources": hits,
    }


if __name__ == "__main__":
    query = "What does the constitution say about the right to fair trial?"
    result = answer_with_citations(query)

    print(result["answer"])
    print()
    print("Citations:")
    for c in result["citations"]:
        print(f"  - Article {c['article']}: {c['title']}")

    if result["hallucinated_citations"]:
        print("\nWARNING - cited but not in retrieved sources:", result["hallucinated_citations"])