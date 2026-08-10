import json
from groq import Groq

MODEL = "openai/gpt-oss-120b"


def get_client(api_key):
    return Groq(api_key=api_key)


def evaluate_answer(api_key, question, answer):
    """Score a candidate's answer and decide if a follow-up is needed."""
    client = get_client(api_key)

    prompt = f"""You are an expert interviewer evaluating a candidate's spoken answer.

Question asked: {question}
Candidate's answer: {answer}

Evaluate the answer on a scale of 1-10 considering: correctness, clarity, depth, and structure.
If the answer is vague, incomplete, or too short, set needs_followup to true and provide ONE
natural follow-up question. Otherwise set needs_followup to false and followup_question to null.

Return ONLY valid JSON, no markdown, no preamble. Format exactly like this:
{{"score": 7, "feedback": "short 1-2 sentence feedback", "needs_followup": false, "followup_question": null}}
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )

    raw = response.choices[0].message.content.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        result = json.loads(raw)
        return result
    except json.JSONDecodeError:
        return {"score": 5, "feedback": "Could not evaluate properly.",
                "needs_followup": False, "followup_question": None}


def generate_final_report(api_key, qa_history):
    """Summarize overall performance across all Q&A pairs."""
    client = get_client(api_key)

    history_str = ""
    for i, item in enumerate(qa_history, 1):
        history_str += f"\nQ{i}: {item['question']}\nAnswer: {item['answer']}\nScore: {item['score']}/10\n"

    prompt = f"""Here is a candidate's full mock interview transcript with scores:
{history_str}

Based on this, provide an overall assessment. Return ONLY valid JSON, no markdown:
{{"overall_score": <average out of 10>, "strengths": ["...", "..."], "weak_areas": ["...", "..."], "topics_to_revise": ["...", "..."], "summary": "2-3 sentence overall summary"}}
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )

    raw = response.choices[0].message.content.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"overall_score": 0, "strengths": [], "weak_areas": [],
                "topics_to_revise": [], "summary": "Could not generate report."}
