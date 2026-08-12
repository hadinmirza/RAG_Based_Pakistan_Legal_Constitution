from src.retrieval.retrieval import retrieve
from src.citations.citation import answer_with_citations

DISTANCE_THRESHOLD = 0.

OUT_OF_SCOPE_MESSAGE = "This question does not appear to be covered by the Constitution of Pakistan. I can only answer questions based on its content."


def answer_safe(query, k=5):
    hits = retrieve(query, k=k)
    print("top distance:", hits[0]["distance"] if hits else None)

    if not hits or hits[0]["distance"] > DISTANCE_THRESHOLD:
        return {
            "answer": OUT_OF_SCOPE_MESSAGE,
            "citations": [],
            "hallucinated_citations": [],
            "sources": [],
        }

    return answer_with_citations(query, k=k)


if __name__ == "__main__":
    queries = [
        "What does the constitution say about the right to fair trial?",
        "What is the best recipe for chicken biryani?",
    ]

    for query in queries:
        print("Query:", query)
        result = answer_safe(query)
        print(result["answer"])
        print()