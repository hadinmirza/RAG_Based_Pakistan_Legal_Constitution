"""
app.py -- Flask backend for the Constitution of Pakistan RAG chat UI.

Wired to:
  - src/Scope/scope.py -> answer_safe(query, k=5)
      returns {"answer": ..., "citations": [...], "hallucinated_citations": [...], "sources": [...]}
      Pre-LLM rejection (distance threshold) returns the fixed
      OUT_OF_SCOPE_MESSAGE as the answer text -- we detect that exact
      message to mark the response as "rejected" in the UI so it renders
      as a system-style bubble instead of a normal answer.

SECURITY NOTE: GROQ_API_KEY must be set as a real environment variable
on your machine (never hardcoded here or anywhere in the repo). If a key
was ever pasted into a chat, chat log, or committed to git, treat it as
compromised and rotate it in the Groq console.
"""

from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

from src.Scope.scope import answer_safe, OUT_OF_SCOPE_MESSAGE


def get_answer(question: str) -> dict:
    """Bridges the UI to your RAG pipeline."""
    result = answer_safe(question)

    is_rejected = result.get("answer", "").strip() == OUT_OF_SCOPE_MESSAGE.strip()

    # citations: be defensive about shape, since it comes from
    # src/citations/citation.py which may format entries differently
    # than a flat list of dicts.
    citations = []
    for c in result.get("citations", []):
        if isinstance(c, dict):
            citations.append({
                "article": c.get("article"),
                "title": c.get("title"),
                "part": c.get("part"),
            })
        else:
            citations.append({"article": str(c), "title": None, "part": None})

    return {
        "status": "rejected_prescope" if is_rejected else "answered",
        "answer": result.get("answer", ""),
        "citations": citations,
    }


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/ask", methods=["POST"])
def ask():
    data = request.get_json(silent=True) or {}
    question = (data.get("question") or "").strip()

    if not question:
        return jsonify({"error": "Question cannot be empty."}), 400

    try:
        result = get_answer(question)
    except Exception as exc:
        return jsonify({"error": f"Something went wrong: {exc}"}), 500

    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
