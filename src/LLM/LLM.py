import os
from dotenv import load_dotenv
from groq import Groq
from src.retrieval.retrieval import retrieve

load_dotenv()

client = Groq(api_key=os.environ["GROQ_API_KEY"])

SYSTEM_PROMPT = "You are a legal assistant answering questions about the Constitution of Pakistan. Answer ONLY using the provided article excerpts. If the excerpts don't contain the answer, say so. Always cite the Article number(s) you used."


def build_context(hits):
    parts = [f"Article {h['article']} ({h['title']}):\n{h['text']}" for h in hits]
    return "\n\n---\n\n".join(parts)


def answer(query, k=5):
    hits = retrieve(query, k=k)
    context = build_context(hits)
    user_message = f"Context:\n{context}\n\nQuestion: {query}"

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        max_tokens=1000,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
    )

    return response.choices[0].message.content, hits


if __name__ == "__main__":
    query = "What does the constitution say about the right to fair trial?"
    answer_text, hits = answer(query)

    print(answer_text)
    print()
    for h in hits:
        print(f"- Article {h['article']}: {h['title']}")