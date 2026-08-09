import streamlit as st
import pandas as pd
import plotly.express as px

from resume_parser import parse_resume
from question_generator import generate_questions
from evaluator import evaluate_answer, generate_final_report

st.set_page_config(page_title="AI Interview Agent", page_icon="🎤", layout="centered")

API_KEY = st.secrets.get("GROQ_API_KEY", "")

# ---------------- Session state init ----------------
defaults = {
    "stage": "setup",          # setup -> interview -> report
    "questions": [],
    "current_q_index": 0,
    "current_question": None,
    "is_followup": False,
    "qa_history": [],           # list of {question, answer, score, feedback, type}
    "resume_data": None,
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

st.title("🎤 AI Interview Agent")
st.caption("Personalized mock interview based on your resume — with real-time evaluation.")

# ---------------- STAGE 1: Setup ----------------
if st.session_state.stage == "setup":
    st.subheader("Step 1: Tell us about the interview")

    role = st.text_input("Target Role", placeholder="e.g., Data Analyst, ML Engineer")
    uploaded_file = st.file_uploader("Upload your resume (PDF)", type=["pdf"])
    num_questions = st.slider("Number of questions", min_value=4, max_value=12, value=8)

    if st.button("Start Interview", type="primary", disabled=not (role and uploaded_file and API_KEY)):
        if not API_KEY:
            st.error("GROQ_API_KEY not set in .streamlit/secrets.toml")
        else:
            with st.spinner("Reading your resume..."):
                resume_data = parse_resume(uploaded_file)
                st.session_state.resume_data = resume_data

            with st.spinner("Generating personalized questions..."):
                questions = generate_questions(
                    API_KEY, role,
                    resume_data["skills"],
                    resume_data["projects"],
                    num_questions
                )
                st.session_state.questions = questions
                st.session_state.current_q_index = 0
                st.session_state.current_question = questions[0]["question"]
                st.session_state.is_followup = False
                st.session_state.qa_history = []
                st.session_state.stage = "interview"
                st.rerun()

    if not API_KEY:
        st.warning("⚠️ Add your GROQ_API_KEY in .streamlit/secrets.toml before starting.")

# ---------------- STAGE 2: Interview loop ----------------
elif st.session_state.stage == "interview":
    total_q = len(st.session_state.questions)
    idx = st.session_state.current_q_index

    st.progress(min(idx / total_q, 1.0))
    st.subheader(f"Question {idx + 1} of {total_q}")
    if st.session_state.is_followup:
        st.caption("↳ Follow-up question")

    st.markdown(f"**{st.session_state.current_question}**")

    answer = st.text_area("Your answer", height=150, key=f"answer_{idx}_{st.session_state.is_followup}")

    if st.button("Submit Answer", type="primary", disabled=not answer.strip()):
        with st.spinner("Evaluating your answer..."):
            result = evaluate_answer(API_KEY, st.session_state.current_question, answer)

        st.session_state.qa_history.append({
            "question": st.session_state.current_question,
            "answer": answer,
            "score": result["score"],
            "feedback": result["feedback"],
        })

        if result.get("needs_followup") and result.get("followup_question"):
            st.session_state.current_question = result["followup_question"]
            st.session_state.is_followup = True
            st.rerun()
        else:
            # Move to next main question
            st.session_state.is_followup = False
            next_idx = st.session_state.current_q_index + 1
            if next_idx < total_q:
                st.session_state.current_q_index = next_idx
                st.session_state.current_question = st.session_state.questions[next_idx]["question"]
                st.rerun()
            else:
                st.session_state.stage = "report"
                st.rerun()

    st.divider()
    if st.button("End Interview Early"):
        st.session_state.stage = "report"
        st.rerun()

# ---------------- STAGE 3: Final report ----------------
elif st.session_state.stage == "report":
    st.subheader("📊 Your Interview Report")

    if not st.session_state.qa_history:
        st.info("No answers recorded.")
    else:
        with st.spinner("Generating final report..."):
            report = generate_final_report(API_KEY, st.session_state.qa_history)

        col1, col2 = st.columns(2)
        col1.metric("Overall Score", f"{report.get('overall_score', 0)}/10")
        col2.metric("Questions Answered", len(st.session_state.qa_history))

        st.markdown("**Summary**")
        st.write(report.get("summary", ""))

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**✅ Strengths**")
            for s in report.get("strengths", []):
                st.write(f"- {s}")
        with c2:
            st.markdown("**⚠️ Areas to Improve**")
            for w in report.get("weak_areas", []):
                st.write(f"- {w}")

        st.markdown("**📚 Topics to Revise**")
        for t in report.get("topics_to_revise", []):
            st.write(f"- {t}")

        st.divider()
        st.markdown("**Question-by-question breakdown**")
        df = pd.DataFrame(st.session_state.qa_history)
        df.index = df.index + 1
        fig = px.bar(df, x=df.index, y="score", labels={"x": "Question #", "score": "Score"},
                     title="Score per Question", range_y=[0, 10])
        st.plotly_chart(fig, use_container_width=True)

        with st.expander("View full transcript"):
            for i, item in enumerate(st.session_state.qa_history, 1):
                st.markdown(f"**Q{i}: {item['question']}**")
                st.write(f"Answer: {item['answer']}")
                st.write(f"Score: {item['score']}/10 — {item['feedback']}")
                st.divider()

    if st.button("Start New Interview"):
        for key, val in defaults.items():
            st.session_state[key] = val
        st.rerun()
