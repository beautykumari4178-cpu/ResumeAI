
import { useState } from "react";
import "./App.css";

const API_URL = "http://127.0.0.1:8000";

function App() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [resume, setResume] = useState(null);
  const [skills, setSkills] = useState([]);
  const [jobDescription, setJobDescription] = useState("");
  const [matchResult, setMatchResult] = useState(null);
  const [matching, setMatching] = useState(false);

  async function analyzeResume() {
    if (!file) {
      setError("Please select a PDF resume first.");
      return;
    }

    setLoading(true);
    setError("");
    setResume(null);
    setSkills([]);
    setMatchResult(null);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const parseResponse = await fetch(
        `${API_URL}/api/resume/parse`,
        { method: "POST", body: formData }
      );

      const resumeData = await parseResponse.json();

      if (!parseResponse.ok) {
        throw new Error(
          resumeData.detail || "Could not extract resume text."
        );
      }

      if (!resumeData.text) {
        throw new Error("No text was extracted from this PDF.");
      }

      setResume(resumeData);

      const skillsForm = new FormData();
      skillsForm.append("text", resumeData.text);

      const skillsResponse = await fetch(
        `${API_URL}/api/resume/skills`,
        { method: "POST", body: skillsForm }
      );

      const skillsData = await skillsResponse.json();

      if (!skillsResponse.ok) {
        throw new Error(
          skillsData.detail || "Could not extract skills."
        );
      }

      setSkills(
        Array.isArray(skillsData.skills_found)
          ? skillsData.skills_found
          : []
      );
    } catch (err) {
      setError(err.message || "Could not connect to the backend.");
    } finally {
      setLoading(false);
    }
  }

  async function matchResume() {
    if (!resume?.text) {
      setError("Please analyze your resume first.");
      return;
    }

    if (!jobDescription.trim()) {
      setError("Please enter a job description.");
      return;
    }

    setMatching(true);
    setError("");
    setMatchResult(null);

    try {
      const formData = new FormData();
      formData.append("resume_text", resume.text);
      formData.append("job_description", jobDescription);

      const response = await fetch(
        `${API_URL}/api/resume/match`,
        { method: "POST", body: formData }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Matching failed.");
      }

      setMatchResult(data);
    } catch (err) {
      setError(err.message || "Could not connect to the backend.");
    } finally {
      setMatching(false);
    }
  }

  const matchedSkills = Array.isArray(matchResult?.matched_skills)
    ? matchResult.matched_skills
    : [];

  const missingSkills = Array.isArray(matchResult?.missing_skills)
    ? matchResult.missing_skills
    : [];

  return (
    <main className="app">
      <header className="header">
        <h1>ResumeAI</h1>
        <p>AI-Powered Resume Analyzer &amp; Job Matcher</p>
      </header>

      <section className="card">
        <h2>Analyze your resume</h2>
        <p>Upload a PDF to get started.</p>

        <input
          type="file"
          accept=".pdf,application/pdf"
          onChange={(event) => {
            setFile(event.target.files?.[0] || null);
            setError("");
            setResume(null);
            setSkills([]);
            setMatchResult(null);
          }}
        />

        <button onClick={analyzeResume} disabled={loading || !file}>
          {loading ? "Analyzing resume..." : "Analyze Resume →"}
        </button>
      </section>

      {resume && (
        <section className="card">
          <h2>Resume overview</h2>

          <p><strong>File:</strong> {resume.filename || file?.name}</p>
          <p><strong>Pages:</strong> {resume.page_count ?? "N/A"}</p>
          <p>
            <strong>Characters:</strong>{" "}
            {resume.character_count ?? resume.text.length}
          </p>

          {resume.warning && <p>{resume.warning}</p>}

          <h3>Skills found ({skills.length})</h3>

          {skills.length > 0 ? (
            <div className="skills">
              {skills.map((skill) => (
                <span className="skill" key={skill}>
                  {skill}
                </span>
              ))}
            </div>
          ) : (
            <p>No matching skills found.</p>
          )}

          <h3>Extracted text</h3>
          <pre className="resume-text">{resume.text}</pre>
        </section>
      )}

      <section className="card">
        <h2>Job Description Matcher</h2>
        <p>
          Paste a job description to compare its required skills
          with your resume.
        </p>

        <textarea
          value={jobDescription}
          onChange={(event) => setJobDescription(event.target.value)}
          placeholder="Example: We need Python, SQL, Pandas, Excel and Machine Learning."
          rows={6}
        />

        <button
          onClick={matchResume}
          disabled={!resume?.text || matching}
        >
          {matching ? "Matching..." : "Match with Job Description"}
        </button>

        {matchResult && (
          <div className="match-results">
            <h3>
              Match Score: {matchResult.match_percentage ?? 0}%
            </h3>

            <h3>Matched Skills</h3>
            <p>
              {matchedSkills.length > 0
                ? matchedSkills.join(", ")
                : "No matching skills found."}
            </p>

            <h3>Missing Skills</h3>
            <p>
              {missingSkills.length > 0
                ? missingSkills.join(", ")
                : "No missing skills from the detected list."}
            </p>
          </div>
        )}
      </section>

      {error && <p className="error">{error}</p>}

      <footer>ResumeAI · Built with React and FastAPI</footer>
    </main>
  );
}

export default App;
