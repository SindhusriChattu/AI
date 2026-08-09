import fitz  # PyMuPDF
import re

# Basic skill keyword list — expand this based on target roles
SKILL_KEYWORDS = [
    "python", "sql", "machine learning", "deep learning", "nlp",
    "scikit-learn", "tensorflow", "keras", "xgboost", "lightgbm",
    "streamlit", "power bi", "tableau", "pandas", "numpy",
    "spacy", "faiss", "word2vec", "excel", "statistics"
]


def extract_text_from_pdf(uploaded_file):
    """Extract raw text from uploaded PDF resume."""
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text


def extract_skills(text):
    """Match known skill keywords in resume text."""
    text_lower = text.lower()
    found_skills = [skill for skill in SKILL_KEYWORDS if skill in text_lower]
    return list(set(found_skills))


def extract_projects(text):
    """Naive project title extraction using common resume patterns."""
    # Looks for lines after 'PROJECTS' section header, before next ALL-CAPS header
    match = re.search(r'PROJECTS?(.*?)(?=[A-Z\s]{5,}\n|$)', text, re.DOTALL | re.IGNORECASE)
    if match:
        block = match.group(1)
        lines = [l.strip("•- ") for l in block.split("\n") if len(l.strip()) > 15]
        return lines[:6]  # cap at 6 project lines
    return []


def parse_resume(uploaded_file):
    text = extract_text_from_pdf(uploaded_file)
    skills = extract_skills(text)
    projects = extract_projects(text)
    return {
        "raw_text": text,
        "skills": skills,
        "projects": projects
    }
