from resume_parser import parse_resume

if __name__ == "__main__":
    # Change this to your resume file path
    with open("your_resume.pdf", "rb") as f:
        result = parse_resume(f)
        print("Skills found:", result["skills"])
        print("Projects found:", result["projects"])
