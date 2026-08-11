import json
from groq import Groq

MODEL = "openai/gpt-oss-120b"


def get_client(api_key):
    return Groq(api_key=api_key)


def generate_prep_questions(api_key, role, skills, projects, per_category=5):
    """Generate a categorized interview prep sheet: Direct, Scenario-based, Logical/Aptitude.
    Each question comes with a model answer for self-study."""
    client = get_client(api_key)

    skills_str = ", ".join(skills) if skills else "general " + role + " skills"
    projects_str = "; ".join(projects) if projects else "no specific projects listed"

    prompt = f"""You are preparing interview study material for a candidate applying for a {role} role.

Candidate's skills: {skills_str}
Candidate's projects: {projects_str}

Generate exactly {per_category} questions for EACH of these 3 categories (total {per_category * 3} questions):

1. "Direct" — straightforward technical/knowledge questions based on the candidate's actual skills and tools.
2. "Scenario" — realistic on-the-job scenario or case-study questions relevant to a {role} (e.g., "You find missing values in a dataset before a deadline, what do you do?"), and questions that reference the candidate's specific projects where relevant.
3. "Logical" — logical reasoning / aptitude style questions relevant to problem-solving in a {role} role (can include basic quantitative/logical puzzles interviewers commonly ask freshers).

For each question, also write a clear, well-structured model answer (3-6 sentences) that the candidate can study from.

Return ONLY a valid JSON array, no markdown formatting, no preamble, no explanation.
Format exactly like this:
[
  {{"category": "Direct", "question": "...", "answer": "..."}},
  {{"category": "Scenario", "question": "...", "answer": "..."}},
  {{"category": "Logical", "question": "...", "answer": "..."}}
]
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.6,
    )

    raw = response.choices[0].message.content.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        questions = json.loads(raw)
        return questions
    except json.JSONDecodeError:
        return [{"category": "Error", "question": "Could not parse questions.",
                  "answer": raw[:300]}]

