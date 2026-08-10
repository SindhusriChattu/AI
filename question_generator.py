import json
from groq import Groq

MODEL = "openai/gpt-oss-120b"


def get_client(api_key):
    return Groq(api_key=api_key)


def generate_questions(api_key, role, skills, projects, num_questions=8):
    """Generate personalized interview questions based on resume data."""
    client = get_client(api_key)

    skills_str = ", ".join(skills) if skills else "general " + role + " skills"
    projects_str = "; ".join(projects) if projects else "no specific projects listed"

    prompt = f"""You are an expert technical interviewer for a {role} role.

Candidate's skills: {skills_str}
Candidate's projects: {projects_str}

Generate exactly {num_questions} interview questions with this mix:
- 60% technical questions based on the candidate's actual skills
- 30% project-based questions referencing their specific projects
- 10% behavioral/HR questions (e.g., strengths, weaknesses, teamwork)

Return ONLY a valid JSON array, no markdown formatting, no preamble, no explanation.
Format exactly like this:
[
  {{"question": "...", "type": "technical", "topic": "..."}},
  {{"question": "...", "type": "project", "topic": "..."}},
  {{"question": "...", "type": "behavioral", "topic": "..."}}
]
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )

    raw = response.choices[0].message.content.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        questions = json.loads(raw)
        return questions
    except json.JSONDecodeError:
        # Fallback: return raw text wrapped so app doesn't crash
        return [{"question": "Could not parse questions. Raw output: " + raw[:200],
                  "type": "error", "topic": "error"}]
