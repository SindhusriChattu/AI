import streamlit as st

from resume_parser import parse_resume
from question_generator import generate_prep_questions

st.set_page_config(page_title="AI Interview Prep Sheet", page_icon="📝", layout="centered")

API_KEY = st.secrets.get("GROQ_API_KEY", "")

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
