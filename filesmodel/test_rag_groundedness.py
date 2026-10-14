"""
AI Model Testing POC - Clinical Assistant (Model #5) groundedness evaluation
===============================================================================
This is the highest-risk model in the pipeline: it's generative (RAG + Llama
8B), so it can produce fluent, confident, WRONG answers (hallucination).
In a clinical-review context, an ungrounded claim is a real risk, not just
a quality bug.

What this checks, per golden question:
  1. Does the retrieved evidence actually contain what's needed to answer?
     (retrieval quality - separate from generation quality)
  2. Does the generated answer's claims trace back to that evidence?
     (groundedness - is it making things up?)
  3. For questions with NO evidence in the record, does the model correctly
     say "not found" instead of fabricating an answer?
     (negative/refusal testing - arguably the most important check here)

This uses an LLM-as-judge pattern (a second model grades groundedness)
because exact string matching is too brittle for natural-language answers.
You need an Anthropic API key for the judge step - set ANTHROPIC_API_KEY.

Usage:
    export ANTHROPIC_API_KEY=your_key_here
    python test_rag_groundedness.py
"""

import json
import os
import requests

import config

try:
    import anthropic
except ImportError:
    anthropic = None


def load_golden_qa():
    with open(config.GOLDEN_QA_SET, "r", encoding="utf-8") as f:
        return json.load(f)


def call_clinical_assistant(question, record_id):
    """Call the real Clinical Assistant endpoint. Adjust the request/response
    shape once Dev confirms the actual API contract - critically, you need
    the endpoint to return the retrieved evidence chunks SEPARATELY from the
    generated answer, not just the final answer. If Dev's API only returns
    the final answer with no visibility into retrieval, that's the first
    thing to push back on - you can't test groundedness without it."""
    response = requests.post(
        config.ENDPOINTS["clinical_assistant"],
        json={"question": question, "record_id": record_id},
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    # Expected shape:
    # {"answer": "...", "retrieved_evidence": ["chunk1 text", "chunk2 text", ...]}
    return data.get("answer", ""), data.get("retrieved_evidence", [])


def judge_groundedness(question, answer, retrieved_evidence, expected_evidence):
    """Use an LLM judge to score whether the answer's claims are supported
    by the retrieved evidence. Returns a dict with score and reasoning."""
    if anthropic is None:
        raise RuntimeError("pip install anthropic first")

    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    prompt = f"""You are evaluating a clinical AI assistant's answer for groundedness.

Question asked: {question}

Evidence retrieved by the system from the medical record:
{json.dumps(retrieved_evidence, indent=2)}

Expected evidence (ground truth, for reference only - the system may phrase
differently but should cover the same facts):
{json.dumps(expected_evidence, indent=2)}

Answer given by the system:
{answer}

Evaluate strictly:
1. Is every factual claim in the answer supported by the retrieved evidence?
   Flag ANY claim not traceable to the evidence as a hallucination.
2. If expected evidence is empty (meaning nothing should be found), does the
   answer correctly indicate nothing was found, rather than inventing a claim?

Respond ONLY with JSON, no other text:
{{"grounded": true or false, "hallucinated_claims": ["..."], "reasoning": "..."}}"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}],
    )
    text = response.content[0].text.strip()
    text = text.replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"grounded": None, "hallucinated_claims": [], "reasoning": f"Judge output unparseable: {text}"}


def run():
    qa_set = load_golden_qa()
    results = []
    grounded_count = 0
    scored_count = 0

    print(f"Running {len(qa_set)} golden questions against Clinical Assistant...\n")

    for item in qa_set:
        question = item["question"]
        record_id = item["record_id"]
        expected_evidence = item.get("expected_evidence_snippets", [])

        try:
            answer, retrieved = call_clinical_assistant(question, record_id)
        except Exception as e:
            print(f"  FAILED to call assistant for '{question}': {e}")
            results.append({"question": question, "error": str(e)})
            continue

        verdict = judge_groundedness(question, answer, retrieved, expected_evidence)

        print(f"  Question: '{question}'")
        print(f"    Answer: {answer[:200]}")
        print(f"    Grounded: {verdict.get('grounded')}")
        if verdict.get("hallucinated_claims"):
            print(f"    HALLUCINATED CLAIMS: {verdict['hallucinated_claims']}")
        print(f"    Reasoning: {verdict.get('reasoning', '')}\n")

        results.append({
            "question": question,
            "answer": answer,
            "retrieved_evidence": retrieved,
            "verdict": verdict,
        })

        if verdict.get("grounded") is not None:
            scored_count += 1
            if verdict["grounded"]:
                grounded_count += 1

    score = grounded_count / scored_count if scored_count else 0
    print("=" * 50)
    print(f"Groundedness score: {score:.2f} ({grounded_count}/{scored_count})")
    print(f"Threshold (config.GROUNDEDNESS_MIN_SCORE): {config.GROUNDEDNESS_MIN_SCORE}")
    print("PASS" if score >= config.GROUNDEDNESS_MIN_SCORE else "FAIL - below threshold, review hallucinated_claims above")
    print("=" * 50)

    return results


if __name__ == "__main__":
    run()
