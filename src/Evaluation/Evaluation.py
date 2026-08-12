from src.Scope.scope import answer_safe, OUT_OF_SCOPE_MESSAGE

IN_SCOPE_TESTS = [
    {"query": "What does the constitution say about the right to fair trial?", "expected_article": "10A"},
    {"query": "What is the state religion of Pakistan?", "expected_article": "2"},
    {"query": "Who is eligible to become President?", "expected_article": "41"},
    {"query": "What does Article 25 say about equality?", "expected_article": "25"},
    {"query": "What is high treason under the constitution?", "expected_article": "6"},
]

# expected to be rejected by the distance threshold, before ever calling the LLM
OUT_OF_SCOPE_PRE_LLM = [
    "What is the best recipe for chicken biryani?",
    "Who won the last cricket world cup?",
    "What is the weather like in Lahore today?",
]

# close enough to legal/government language that they pass the distance threshold,
# but the retrieved articles don't actually answer them -- LLM should refuse
OUT_OF_SCOPE_LLM_LEVEL = [
    "What is Pakistan's current interest rate set by the central bank?",
    "What are the visa requirements to travel to Pakistan?",
]


def run_in_scope_tests():
    print("=== IN-SCOPE TESTS ===")
    passed = 0
    for test in IN_SCOPE_TESTS:
        result = answer_safe(test["query"])
        cited_articles = [c["article"] for c in result["citations"]]
        ok = test["expected_article"] in cited_articles
        passed += ok
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] {test['query']}")
        print(f"  expected: {test['expected_article']} | got: {cited_articles}")
    print(f"\n{passed}/{len(IN_SCOPE_TESTS)} passed\n")


def run_out_of_scope_tests(queries, label):
    print(f"=== OUT-OF-SCOPE TESTS ({label}) ===")
    for query in queries:
        result = answer_safe(query)
        rejected_pre_llm = result["answer"] == OUT_OF_SCOPE_MESSAGE
        rejected_by_llm = (not rejected_pre_llm) and len(result["citations"]) == 0
        answered_incorrectly = len(result["citations"]) > 0

        if rejected_pre_llm:
            status = "REJECTED (pre-LLM, distance threshold)"
        elif rejected_by_llm:
            status = "REJECTED (LLM level)"
        else:
            status = "FAIL - answered with citations, should have refused"

        print(f"[{status}] {query}")
    print()


if __name__ == "__main__":
    run_in_scope_tests()
    run_out_of_scope_tests(OUT_OF_SCOPE_PRE_LLM, "expected pre-LLM rejection")
    run_out_of_scope_tests(OUT_OF_SCOPE_LLM_LEVEL, "expected LLM-level rejection")