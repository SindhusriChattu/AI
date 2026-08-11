import streamlit as st

from resume_parser import parse_resume
from question_generator import generate_prep_questions

st.set_page_config(page_title="AI Interview Prep Sheet", page_icon="📝", layout="centered")

API_KEY = st.secrets.get("GROQ_API_KEY", "")

SAMPLE_QUESTIONS = [
    {"category": "Direct", "question": "What is the difference between a list and a tuple in Python?",
     "answer": "A list is mutable, meaning its elements can be changed after creation, while a tuple is immutable. "
               "Lists use square brackets [] and tuples use parentheses (). Because tuples are immutable, they are "
               "slightly faster and can be used as dictionary keys, whereas lists cannot."},
    {"category": "Direct", "question": "Explain the difference between INNER JOIN and LEFT JOIN in SQL.",
     "answer": "INNER JOIN returns only the rows that have matching values in both tables. LEFT JOIN returns all "
               "rows from the left table, along with matched rows from the right table — unmatched right-table "
               "columns are filled with NULL. LEFT JOIN is useful when you want to keep all records from the "
               "primary table regardless of a match."},
    {"category": "Scenario", "question": "You're given a dataset with 15% missing values in a key column, and the "
                                          "deadline is tomorrow. How do you handle it?",
     "answer": "First, I'd check whether the missing values are random or follow a pattern (MCAR/MAR/MNAR). Given "
               "the tight deadline, I'd use median/mode imputation for numerical/categorical columns as a fast, "
               "defensible approach, while flagging the column for a deeper follow-up. I'd document the assumption "
               "clearly so stakeholders know it's a temporary fix, not a permanent data quality solution."},
    {"category": "Scenario", "question": "Walk me through how you'd explain a drop in a key metric to a "
                                          "non-technical stakeholder.",
     "answer": "I'd start with the headline number and business impact in plain language, avoiding jargon. Then "
               "I'd show 1-2 simple visuals (trend line, comparison) that make the 'why' obvious at a glance. "
               "Finally, I'd give a clear recommendation or next step rather than just presenting the problem."},
    {"category": "Logical", "question": "A clock shows 3:15. What is the angle between the hour and minute hands?",
     "answer": "The minute hand at 15 minutes is at 90°. The hour hand moves 0.5° per minute, so at 3:15 it is at "
               "(3×30) + (15×0.5) = 90 + 7.5 = 97.5°. The angle between them is 97.5° − 90° = 7.5°."},
]


def get_sample_data():
    return {
        "questions": SAMPLE_QUESTIONS,
        "resume_data": {"skills": ["python", "sql", "pandas", "power bi"], "projects": ["Sample Project"]},
        "role": "Data Analyst (Sample Preview)",
    }


CATEGORY_INFO = {
    "Direct": {"emoji": "🎯", "desc": "Straightforward technical/knowledge questions based on your skills."},
    "Scenario": {"emoji": "🧩", "desc": "Realistic on-the-job scenarios and project-based questions."},
    "Logical": {"emoji": "🧠", "desc": "Logical reasoning / aptitude style questions."},
}

defaults = {
    "prep_questions": None,
    "resume_data": None,
    "role": "",
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

st.title("📝 AI Interview Prep Sheet")
st.caption("Upload your resume + target role, get a categorized Q&A sheet to study from — no live interview needed.")

# ---------------- Setup form ----------------
st.subheader("Step 1: Tell us about the role")

role = st.text_input("Target Role", placeholder="e.g., Data Analyst, ML Engineer", value=st.session_state.role)
uploaded_file = st.file_uploader("Upload your resume (PDF)", type=["pdf"])
per_category = st.slider("Questions per category", min_value=3, max_value=8, value=5)

if st.button("Generate Prep Sheet", type="primary", disabled=not (role and uploaded_file and API_KEY)):
    if not API_KEY:
        st.error("GROQ_API_KEY not set in secrets.")
    else:
        with st.spinner("Reading your resume..."):
            resume_data = parse_resume(uploaded_file)
            st.session_state.resume_data = resume_data

        with st.spinner("Generating your personalized prep sheet..."):
            questions = generate_prep_questions(
                API_KEY, role,
                resume_data["skills"],
                resume_data["projects"],
                per_category
            )
            st.session_state.prep_questions = questions
            st.session_state.role = role

if not API_KEY:
    st.warning("⚠️ Add your GROQ_API_KEY in secrets before generating.")
    if st.button("👀 Preview with sample data (no API key needed)"):
        sample = get_sample_data()
        st.session_state.prep_questions = sample["questions"]
        st.session_state.resume_data = sample["resume_data"]
        st.session_state.role = sample["role"]
        st.rerun()

# ---------------- Results ----------------
if st.session_state.prep_questions:
    questions = st.session_state.prep_questions

    if st.session_state.resume_data and st.session_state.resume_data.get("skills"):
        with st.expander("Skills detected from your resume"):
            st.write(", ".join(st.session_state.resume_data["skills"]))

    st.divider()
    st.subheader(f"Prep Sheet — {st.session_state.role}")

    for category, info in CATEGORY_INFO.items():
        cat_questions = [q for q in questions if q.get("category", "").lower() == category.lower()]
        if not cat_questions:
            continue

        st.markdown(f"### {info['emoji']} {category} Questions")
        st.caption(info["desc"])

        for i, q in enumerate(cat_questions, 1):
            with st.expander(f"Q{i}. {q['question']}"):
                st.markdown("**Model Answer:**")
                st.write(q.get("answer", "No answer generated."))

        st.divider()

    # Plain text export for offline studying
    export_lines = [f"INTERVIEW PREP SHEET — {st.session_state.role}\n"]
    for category in CATEGORY_INFO:
        cat_questions = [q for q in questions if q.get("category", "").lower() == category.lower()]
        if not cat_questions:
            continue
        export_lines.append(f"\n{'=' * 40}\n{category.upper()} QUESTIONS\n{'=' * 40}\n")
        for i, q in enumerate(cat_questions, 1):
            export_lines.append(f"\nQ{i}. {q['question']}\nA: {q.get('answer', '')}\n")

    st.download_button(
        "⬇️ Download as text file",
        data="\n".join(export_lines),
        file_name=f"interview_prep_{st.session_state.role.replace(' ', '_')}.txt",
        mime="text/plain",
    )

    if st.button("Generate New Prep Sheet"):
        st.session_state.prep_questions = None
        st.rerun()
