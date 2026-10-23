
from io import BytesIO
import re

import pymupdf
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(
    title="ResumeAI API",
    description="Resume analyzer and job matching API",
    version="1.0.0",
)


# Allow the React frontend to connect to the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Skills that the application can detect
SKILL_LIST = [
    "Python",
    "Java",
    "C++",
    "C",
    "JavaScript",
    "TypeScript",
    "HTML",
    "CSS",
    "React",
    "Node.js",
    "FastAPI",
    "Django",
    "SQL",
    "PostgreSQL",
    "MySQL",
    "MongoDB",
    "Pandas",
    "NumPy",
    "Matplotlib",
    "Seaborn",
    "Scikit-learn",
    "Machine Learning",
    "Deep Learning",
    "Data Science",
    "Power BI",
    "Tableau",
    "Excel",
    "Git",
    "GitHub",
    "REST API",
    "AWS",
    "Docker",
    "Linux",
]


# Learning suggestions for missing skills
SKILL_SUGGESTIONS = {
    "Python": {
        "reason": "Python is useful for automation, data analysis, and backend development.",
        "project": "Build a Student Record Management System using Python.",
    },
    "SQL": {
        "reason": "SQL helps you query, manage, and analyze relational databases.",
        "project": "Build an E-commerce Sales Analysis project using SQL.",
    },
    "Pandas": {
        "reason": "Pandas is widely used for cleaning and analyzing datasets.",
        "project": "Analyze a student performance dataset using Pandas.",
    },
    "NumPy": {
        "reason": "NumPy provides efficient numerical and array operations.",
        "project": "Create a numerical data analysis project using NumPy.",
    },
    "Excel": {
        "reason": "Excel is useful for organizing data, formulas, and reporting.",
        "project": "Create an interactive sales report using Excel.",
    },
    "Machine Learning": {
        "reason": "Machine Learning helps build predictive models from data.",
        "project": "Build a Student Performance Prediction model.",
    },
    "Matplotlib": {
        "reason": "Matplotlib helps present data through charts and graphs.",
        "project": "Create a data visualization report using Matplotlib.",
    },
    "Git": {
        "reason": "Git helps track code changes and collaborate on projects.",
        "project": "Track a Python project using Git and GitHub.",
    },
    "Java": {
        "reason": "Java is used for object-oriented programming and application development.",
        "project": "Build a Library Management System using Java.",
    },
    "React": {
        "reason": "React helps build interactive user interfaces.",
        "project": "Build a job listing dashboard using React.",
    },
    "PostgreSQL": {
        "reason": "PostgreSQL is useful for managing relational data and complex queries.",
        "project": "Build a database-backed inventory management system.",
    },
    "JavaScript": {
        "reason": "JavaScript adds interactivity to web applications.",
        "project": "Build an interactive task management application.",
    },
    "HTML": {
        "reason": "HTML structures the content of web pages.",
        "project": "Create a personal portfolio webpage.",
    },
    "CSS": {
        "reason": "CSS styles web pages and helps create responsive layouts.",
        "project": "Design a responsive portfolio website.",
    },
    "FastAPI": {
        "reason": "FastAPI helps build APIs with Python.",
        "project": "Build a REST API for a student management system.",
    },
}


def find_skills(text: str) -> list[str]:
    """Return supported skills found in the supplied text."""
    found_skills = []

    for skill in SKILL_LIST:
        pattern = r"(?<!\w)" + re.escape(skill) + r"(?!\w)"

        if re.search(pattern, text, flags=re.IGNORECASE):
            found_skills.append(skill)

    return found_skills


@app.get("/")
def home():
    return {
        "message": "Welcome to ResumeAI API",
        "docs": "/docs",
    }


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/api/resume/parse")
async def parse_resume(file: UploadFile = File(...)):
    """Extract readable text from an uploaded PDF resume."""

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Please upload a PDF file.",
        )

    pdf_bytes = await file.read()

    if not pdf_bytes:
        raise HTTPException(
            status_code=400,
            detail="The uploaded PDF is empty.",
        )

    try:
        with pymupdf.open(
            stream=BytesIO(pdf_bytes),
            filetype="pdf",
        ) as pdf:
            resume_text = "\n".join(
                page.get_text() for page in pdf
            ).strip()

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail="Could not read this PDF. Please upload a valid PDF.",
        ) from exc

    if not resume_text:
        raise HTTPException(
            status_code=422,
            detail=(
                "No readable text found. This PDF may be scanned; "
                "OCR support is not included yet."
            ),
        )

    skills = find_skills(resume_text)

    return {
        "filename": file.filename,
        "text": resume_text,
        "skills": skills,
        "message": "Resume parsed successfully.",
    }


@app.post("/api/resume/skills")
def extract_resume_skills(text: str = Form(...)):
    """Find supported skills in resume text."""

    if not text.strip():
        raise HTTPException(
            status_code=400,
            detail="Resume text cannot be empty.",
        )

    skills = find_skills(text)

    return {
        "skills": skills,
        "count": len(skills),
        "message": "Skills extracted successfully.",
    }


@app.post("/api/resume/match")
def match_resume(
    resume_text: str = Form(...),
    job_description: str = Form(...),
):
    """Compare resume skills with skills found in a job description."""

    if not resume_text.strip():
        raise HTTPException(
            status_code=400,
            detail="Resume text cannot be empty.",
        )

    if not job_description.strip():
        raise HTTPException(
            status_code=400,
            detail="Job description cannot be empty.",
        )

    resume_skills = find_skills(resume_text)
    required_skills = find_skills(job_description)

    matched_skills = [
        skill
        for skill in required_skills
        if skill in resume_skills
    ]

    missing_skills = [
        skill
        for skill in required_skills
        if skill not in resume_skills
    ]

    missing_skill_suggestions = []

    for skill in missing_skills:
        suggestion = SKILL_SUGGESTIONS.get(
            skill,
            {
                "reason": (
                    f"{skill} is mentioned in the job description. "
                    "Learn its fundamentals and practical applications."
                ),
                "project": (
                    f"Build a beginner-friendly project using {skill}."
                ),
            },
        )

        missing_skill_suggestions.append(
            {
                "skill": skill,
                "reason": suggestion["reason"],
                "project": suggestion["project"],
            }
        )

    match_percentage = (
        round(
            len(matched_skills) / len(required_skills) * 100
        )
        if required_skills
        else 0
    )

    return {
        "resume_skills": resume_skills,
        "required_skills": required_skills,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "missing_skill_suggestions": missing_skill_suggestions,
        "match_percentage": match_percentage,
        "message": (
            "Skill comparison completed."
            if required_skills
            else "No supported skills found in the job description."
        ),
    }
