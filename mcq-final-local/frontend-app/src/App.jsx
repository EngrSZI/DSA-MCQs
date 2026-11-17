import { useEffect, useRef, useState } from "react";
import axios from "axios";
import "./App.css";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "";

// Backend stores UTC datetimes as naive values. Treat a timestamp without
// an explicit timezone as UTC so browsers in Pakistan (UTC+05:00) do not
// add five hours to the exam deadline.
const parseServerDate = (value) => {
  if (!value) return NaN;
  const text = String(value);
  if (/([zZ]|[+-]\d{2}:?\d{2})$/.test(text)) {
    return new Date(text).getTime();
  }
  return new Date(`${text}Z`).getTime();
};

function App() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [token, setToken] = useState("");
  const [student, setStudent] = useState(null);

  const [attempt, setAttempt] = useState(null);
  const [timeRemaining, setTimeRemaining] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [answers, setAnswers] = useState({});

  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [submissionNotice, setSubmissionNotice] = useState("");
  const [adminMode, setAdminMode] = useState(false);
  const [students, setStudents] = useState([]);
  const [studentDetail, setStudentDetail] = useState(null);
  const [selectedStudentId, setSelectedStudentId] = useState(null);
  const [studentDetailLoading, setStudentDetailLoading] = useState(false);
  const [studentFile, setStudentFile] = useState(null);
  const [adminMessage, setAdminMessage] = useState("");
  const [tabSwitchCount, setTabSwitchCount] = useState(0);
  const submittingRef = useRef(false);
  const tabViolationLockRef = useRef(false);

  useEffect(() => {
    const studentName = student?.full_name?.trim() || student?.email?.trim();
    document.title = studentName
      ? `${studentName} | MCQ Examination`
      : "MCQ Examination";
  }, [student]);

  // -----------------------------------------------------
  // Login and start assigned exam
  // -----------------------------------------------------

  const loadStudents = async (accessToken = token) => {
    const response = await axios.get(`${API_BASE_URL}/admin/students`, {
      headers: { Authorization: `Bearer ${accessToken}` },
    });
    setStudents(response.data);
  };

  const toggleStudentAttempts = async (studentId) => {
    if (selectedStudentId === studentId) {
      setSelectedStudentId(null);
      setStudentDetail(null);
      return;
    }

    setSelectedStudentId(studentId);
    setStudentDetail(null);
    setStudentDetailLoading(true);
    setError("");
    try {
      const response = await axios.get(
        `${API_BASE_URL}/admin/results/students/${studentId}/attempts`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setStudentDetail(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || "Unable to load student attempts.");
    } finally {
      setStudentDetailLoading(false);
    }
  };

  const handleStudentImport = async () => {
    if (!studentFile) return;
    setLoading(true);
    setAdminMessage("");
    setError("");
    try {
      const formData = new FormData();
      formData.append("file", studentFile);
      const response = await axios.post(`${API_BASE_URL}/admin/students/import`, formData, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setAdminMessage(`Import complete: ${response.data.created} created, ${response.data.updated} updated, ${response.data.failed} failed.`);
      setStudentFile(null);
      await loadStudents();
    } catch (err) {
      setError(err.response?.data?.detail || "Unable to import students.");
    } finally {
      setLoading(false);
    }
  };

  const downloadStudentTemplate = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/admin/students/template.xlsx`, {
        headers: { Authorization: `Bearer ${token}` },
        responseType: "blob",
      });
      const url = window.URL.createObjectURL(response.data);
      const a = document.createElement("a");
      a.href = url;
      a.download = "students_template.xlsx";
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError(err.response?.data?.detail || "Unable to download template.");
    }
  };

  const downloadResults = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/admin/results/export.xlsx`, {
        headers: { Authorization: `Bearer ${token}` },
        responseType: "blob",
      });
      const url = window.URL.createObjectURL(response.data);
      const a = document.createElement("a");
      a.href = url;
      a.download = "student_results.xlsx";
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError(err.response?.data?.detail || "Unable to export results.");
    }
  };

  const handleLogin = async (event) => {
    event.preventDefault();

    setLoading(true);
    setError("");
    setResult(null);

    try {
      console.log("Starting login...");

      const formData = new URLSearchParams();
      formData.append("username", email);
      formData.append("password", password);

      const loginResponse = await axios.post(
        `${API_BASE_URL}/auth/login`,
        formData,
        {
          headers: {
            "Content-Type": "application/x-www-form-urlencoded",
          },
        }
      );

      console.log("Login response:", loginResponse.data);

      const accessToken = loginResponse.data.access_token;

      if (!accessToken) {
        throw new Error("Access token was not returned by the server.");
      }

      setToken(accessToken);

      const authConfig = {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      };

      const meResponse = await axios.get(`${API_BASE_URL}/auth/me`, authConfig);
      const currentUser = meResponse.data;

      if (currentUser.role === "admin") {
        setStudent({ ...currentUser, email: currentUser.email });
        setAdminMode(true);
        await loadStudents(accessToken);
        return;
      }

      const studentInfo = currentUser;

      const authConfig2 = {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      };

      console.log("Finding published exam...");

      const examsResponse = await axios.get(
        `${API_BASE_URL}/exams`,
        authConfig2
      );
      const availableExams = Array.isArray(examsResponse.data)
        ? examsResponse.data
        : [];
      if (availableExams.length === 0) {
        throw new Error("No published exam is currently available.");
      }
      const configuredExamId = import.meta.env.VITE_EXAM_ID;
      const selectedExam = configuredExamId
        ? availableExams.find((exam) => String(exam.id) === String(configuredExamId))
        : availableExams[0];
      if (!selectedExam) {
        throw new Error("The configured exam is not available.");
      }

      console.log("Starting assigned exam...", selectedExam.id);

      const attemptResponse = await axios.post(
        `${API_BASE_URL}/attempts/start?exam_id=${selectedExam.id}`,
        {},
        authConfig2
      );

      console.log("Attempt response:", attemptResponse.data);

      const newAttempt = attemptResponse.data;
      setAttempt(newAttempt);
      const expiresAtMs = parseServerDate(newAttempt.expires_at);
      if (!Number.isFinite(expiresAtMs)) {
        throw new Error("The server returned an invalid exam expiry time.");
      }
      setTimeRemaining(
        Math.max(0, Math.ceil((expiresAtMs - Date.now()) / 1000))
      );

      console.log(
        "Loading questions for attempt:",
        newAttempt.id
      );

      const questionsResponse = await axios.get(
        `${API_BASE_URL}/attempts/${newAttempt.id}/questions`,
        authConfig
      );

      console.log(
        "Questions response:",
        questionsResponse.data
      );

      const questionsData = questionsResponse.data;

      const loadedQuestions = Array.isArray(questionsData)
        ? questionsData
        : questionsData.questions || [];

      setQuestions(loadedQuestions);

      setStudent({
        ...studentInfo,
        email: email,
      });
      console.log("Exam loaded successfully.");
    } catch (err) {
      console.error("Login or exam-loading error:", err);

      setError(
        err.response?.data?.detail ||
          err.message ||
          "Unable to login or start the assigned exam."
      );
    } finally {
      setLoading(false);
    }
  };

  // -----------------------------------------------------
  // Select an answer
  // -----------------------------------------------------

  const handleAnswerChange = (questionId, selectedOption) => {
    setAnswers((previousAnswers) => ({
      ...previousAnswers,
      [questionId]: selectedOption,
    }));
  };

  // -----------------------------------------------------
  // Submit exam
  // -----------------------------------------------------

  const handleSubmit = async (automatic = false) => {
    if (!attempt || !token || submittingRef.current) {
      return;
    }

    if (!automatic) {
      const confirmed = window.confirm(
        "Are you sure you want to submit this exam? You will be logged out after submission."
      );
      if (!confirmed) return;
    }

    submittingRef.current = true;
    setLoading(true);
    setError("");

    try {
      const submission = {
        answers: Object.entries(answers).map(
          ([questionId, selectedOption]) => ({
            question_id: Number(questionId),
            selected_option: selectedOption,
          })
        ),
        tab_switch_penalty: Number((tabSwitchCount * 0.2).toFixed(2)),
      };

      const submitResponse = await axios.post(
        `${API_BASE_URL}/attempts/${attempt.id}/submit`,
        submission,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      setSubmissionNotice(
        submitResponse.data.expired
          ? "Time expired. Your answers have been saved and submitted. You will be logged out."
          : "Your answers have been saved and submitted. You will be logged out."
      );
      setResult({
        ...(submitResponse.data.final_result || submitResponse.data),
        isFinalResult: Boolean(submitResponse.data.final_result),
        progress: submitResponse.data.progress || submitResponse.data.final_result?.progress,
      });

      // Submission is final. Do not start another batch. Clear the token and
      // return to the login screen after the confirmation is visible.
      window.setTimeout(() => {
        setToken("");
        setAdminMode(false);
        setStudents([]);
        setStudentFile(null);
        setAdminMessage("");
        setStudent(null);
        setAttempt(null);
        setTimeRemaining(null);
        setQuestions([]);
        setAnswers({});
        setResult(null);
        setSubmissionNotice("");
        setError("");
        setEmail("");
        setPassword("");
        setTabSwitchCount(0);
        tabViolationLockRef.current = false;
        submittingRef.current = false;
      }, 2500);
    } catch (err) {
      console.error("Submit error:", err);
      submittingRef.current = false;
      setError(
        err.response?.data?.detail || "Unable to submit the exam"
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!attempt?.expires_at || result) return undefined;

    const updateTimeRemaining = () => {
      const expiresAtMs = parseServerDate(attempt.expires_at);
      const seconds = Number.isFinite(expiresAtMs)
        ? Math.max(0, Math.ceil((expiresAtMs - Date.now()) / 1000))
        : 0;
      setTimeRemaining(seconds);

      if (seconds <= 0 && !submittingRef.current) {
        handleSubmit(true);
      }
    };

    updateTimeRemaining();
    const timer = window.setInterval(updateTimeRemaining, 1000);
    return () => window.clearInterval(timer);
  }, [attempt?.id, attempt?.expires_at, result]);

  useEffect(() => {
    if (!attempt || result) return undefined;

    const handleTabViolation = () => {
      const isHidden = document.visibilityState === "hidden" || !document.hasFocus();
      if (isHidden) {
        if (!tabViolationLockRef.current) {
          tabViolationLockRef.current = true;
          setTabSwitchCount((previous) => previous + 1);
        }
      } else {
        tabViolationLockRef.current = false;
      }
    };

    const handleFocusRestore = () => {
      tabViolationLockRef.current = false;
    };

    document.addEventListener("visibilitychange", handleTabViolation);
    window.addEventListener("blur", handleTabViolation);
    window.addEventListener("focus", handleFocusRestore);

    return () => {
      document.removeEventListener("visibilitychange", handleTabViolation);
      window.removeEventListener("blur", handleTabViolation);
      window.removeEventListener("focus", handleFocusRestore);
    };
  }, [attempt?.id, result]);

  // -----------------------------------------------------
  // Logout
  // -----------------------------------------------------

  const handleLogout = () => {
    setToken("");
    setAdminMode(false);
    setStudents([]);
    setStudentFile(null);
    setAdminMessage("");
    setStudent(null);
    setAttempt(null);
    setTimeRemaining(null);
    setQuestions([]);
    setAnswers({});
    setResult(null);
    setError("");
    setTabSwitchCount(0);
    tabViolationLockRef.current = false;
  };

  // -----------------------------------------------------
  // Login screen
  // -----------------------------------------------------

  if (!token) {
    return (
      <div className="app-container">
        <div className="login-card">
          <h1>MCQ Examination System</h1>
          <p>Student Login</p>

          {error && (
            <div className="error-message">
              {error}
            </div>
          )}

          <form onSubmit={handleLogin}>
            <label>Email</label>

            <input
              type="email"
              value={email}
              onChange={(event) =>
                setEmail(event.target.value)
              }
              placeholder="Enter your email"
              required
            />

            <label>Password</label>

            <input
              type="password"
              value={password}
              onChange={(event) =>
                setPassword(event.target.value)
              }
              placeholder="Enter your password"
              required
            />

            <button type="submit" disabled={loading}>
              {loading ? "Logging in..." : "Login"}
            </button>
          </form>


        </div>
      </div>
    );
  }

  if (adminMode) {
    return (
      <div className="app-container">
        <div className="exam-card">
          <div className="top-bar">
            <div>
              <h1>Administrator Dashboard</h1>
              <p>Student registration and result processing</p>
            </div>
            <button className="logout-button" onClick={handleLogout}>Logout</button>
          </div>

          {error && <div className="error-message">{error}</div>}
          {adminMessage && <div className="success-message">{adminMessage}</div>}

          <div className="admin-section">
            <h2>Bulk Student Registration</h2>
            <p>Upload an Excel file with: Student ID, Full Name, Email, Password. Program is optional.</p>
            <div className="admin-actions">
              <button onClick={downloadStudentTemplate}>Download Excel Template</button>
              <input type="file" accept=".xlsx,.xlsm" onChange={(e) => setStudentFile(e.target.files?.[0] || null)} />
              <button onClick={handleStudentImport} disabled={!studentFile || loading}>
                {loading ? "Importing..." : "Import Students"}
              </button>
            </div>
          </div>

          <div className="admin-section">
            <h2>Results</h2>
            <button onClick={downloadResults}>Download Student Results Excel</button>
          </div>

          <div className="admin-section">
            <h2>Registered Students ({students.length})</h2>
            <div className="table-wrap">
              <table>
                <thead><tr><th>Student ID</th><th>Name</th><th>Email</th><th>Program</th><th>Status</th><th>Attempts</th></tr></thead>
                <tbody>
                  {students.map((s) => (
                    <tr key={s.id}>
                      <td>{s.student_id}</td><td>{s.full_name}</td><td>{s.email}</td><td>{s.program}</td><td>{s.is_active ? "Active" : "Inactive"}</td>
                      <td><button className="table-action" onClick={() => toggleStudentAttempts(s.id)}>{selectedStudentId === s.id ? "Hide details" : "View attempts"}</button></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {selectedStudentId !== null && (
            <div className="admin-section student-attempts-section">
              <h2>Student Attempt Details</h2>
              {studentDetailLoading && <p>Loading attempt history...</p>}
              {studentDetail && (
                <>
                  <p className="student-detail-heading">
                    {studentDetail.student.full_name} ({studentDetail.student.student_id || studentDetail.student.email})
                  </p>
                  <div className="attempt-summary-grid">
                    <p><strong>Cumulative Score</strong><span>{Number(studentDetail.cumulative_score).toFixed(2)}</span></p>
                    <p><strong>Correct</strong><span>{studentDetail.cumulative_correct}</span></p>
                    <p><strong>Wrong</strong><span>{studentDetail.cumulative_wrong}</span></p>
                    <p><strong>Total Deductions</strong><span>{Number(studentDetail.cumulative_deductions).toFixed(2)}</span></p>
                    <p><strong>Submitted Attempts</strong><span>{studentDetail.attempts.filter((item) => item.status === "submitted").length}</span></p>
                  </div>

                  {studentDetail.attempts.length === 0 ? (
                    <p>No exam attempts recorded for this student.</p>
                  ) : studentDetail.attempts.map((item) => (
                    <article className="attempt-detail" key={item.attempt_id}>
                      <div className="attempt-detail-heading">
                        <div>
                          <h3>{item.exam_title} · Batch {item.batch_number}</h3>
                          <p>Attempt #{item.attempt_id} · {item.status} · {item.submitted_at ? new Date(item.submitted_at).toLocaleString() : "Not submitted"}</p>
                        </div>
                        <strong className="attempt-score">Attempt score {Number(item.cumulative_attempt_score).toFixed(2)} / {Number(item.total_marks).toFixed(2)}</strong>
                      </div>
                      <div className="attempt-metrics">
                        <span>Attempted {item.questions_attempted}/{item.questions_assigned}</span>
                        <span>Correct {item.correct_count}</span>
                        <span>Wrong {item.wrong_count}</span>
                        <span>Unanswered {item.unanswered_count}</span>
                        <span>Wrong-answer deduction -{Number(item.wrong_answer_deduction).toFixed(2)}</span>
                        <span>Tab switches {item.tab_switch_count}</span>
                        <span>Tab-switch deduction -{Number(item.tab_switch_deduction).toFixed(2)}</span>
                        <span>Total deductions -{Number(item.total_deductions).toFixed(2)}</span>
                      </div>
                      <div className="table-wrap question-detail-table">
                        <table>
                          <thead><tr><th>Question</th><th>Student Answer</th><th>Correct Answer</th><th>Result</th><th>Marks</th></tr></thead>
                          <tbody>
                            {item.questions.map((question) => (
                              <tr key={question.question_id}>
                                <td className="question-detail-text">{question.question_number}. {question.question_text}</td>
                                <td>{question.selected_option ? `${question.selected_option}: ${question.selected_answer}` : "Unanswered"}</td>
                                <td>{question.correct_option}: {question.correct_answer}</td>
                                <td>{question.is_correct === null ? "Unanswered" : question.is_correct ? "Correct" : "Incorrect"}</td>
                                <td>{Number(question.marks_awarded).toFixed(2)}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </article>
                  ))}
                </>
              )}
            </div>
          )}
        </div>
      </div>
    );
  }

  // -----------------------------------------------------
  // Result screen
  // -----------------------------------------------------

  if (result) {
    return (
      <div className="app-container">
        <div className="exam-card">
          <div className="top-bar">
            <h1>Examination Result</h1>

            <button
              className="logout-button"
              onClick={handleLogout}
            >
              Logout
            </button>
          </div>

          <div className="student-info">
            <p>
              <strong>Student:</strong>{" "}
              {student?.email}
            </p>

            <p>
              <strong>Exam ID:</strong>{" "}
              {result.exam_id}
            </p>

            <p>
              <strong>Attempt ID:</strong>{" "}
              {result.attempt_id}
            </p>
          </div>

          {submissionNotice && (
            <div className="success-message">
              {submissionNotice}
            </div>
          )}

          <div className="result-box">
            <h2>
              {result.isFinalResult ? "Exam Completed" : "Submission Recorded"}
            </h2>

            {(result.progress || result.isFinalResult) && (
              <>
                <p>
                  <strong>Questions Attempted:</strong>{" "}
                  {result.progress?.completed_questions ?? 0} / {result.progress?.total_questions ?? result.total_questions ?? 400}
                </p>
                <p>
                  <strong>Questions Remaining:</strong>{" "}
                  {result.progress?.remaining_questions ?? Math.max((result.progress?.total_questions ?? result.total_questions ?? 400) - (result.progress?.completed_questions ?? 0), 0)}
                </p>
                <p>
                  <strong>Overall Progress:</strong>{" "}
                  {Number(result.progress?.completion_percentage ?? 0).toFixed(2)}%
                </p>
              </>
            )}

            <p>
              <strong>Status:</strong>{" "}
              {result.status}
            </p>
          </div>

          <button onClick={handleLogout}>
            Return to Login
          </button>
        </div>
      </div>
    );
  }

  // -----------------------------------------------------
  // Exam screen
  // -----------------------------------------------------

  return (
    <div className="app-container">
      <div className="exam-card">
        <div className="top-bar">
          <div>
            <h1>MCQ Examination</h1>

            <p>
              Student: {student?.email}
            </p>

            <p>
              Exam ID: {attempt?.exam_id}
            </p>

            <p>
              Attempt ID: {attempt?.id}
            </p>
          </div>

          <button
            className="logout-button"
            onClick={handleLogout}
          >
            Logout
          </button>
        </div>

        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        <div className="exam-summary">
          <p>
            Total Questions: {questions.length}
          </p>

          <p>
            Total Marks: {attempt?.total_marks}
          </p>

          <p>
            Time Remaining: {timeRemaining === null
              ? "--:--"
              : `${String(Math.floor(timeRemaining / 60)).padStart(2, "0")}:${String(timeRemaining % 60).padStart(2, "0")}`}
          </p>

          <p>
            Question Allocation: {attempt?.completed_questions ?? 0} / {attempt?.total_questions ?? 400}
          </p>

        </div>

        {questions.length === 0 ? (
          <p>No questions found for this exam.</p>
        ) : (
          questions.map((question, index) => (
            <div
              className="question-card"
              key={question.id}
            >
              <h3>
                {index + 1}.{" "}
                {question.question_text}
              </h3>

              <label>
                <input
                  type="radio"
                  name={`question-${question.id}`}
                  value="A"
                  checked={
                    answers[question.id] === "A"
                  }
                  onChange={() =>
                    handleAnswerChange(
                      question.id,
                      "A"
                    )
                  }
                />

                {question.option_a}
              </label>

              <label>
                <input
                  type="radio"
                  name={`question-${question.id}`}
                  value="B"
                  checked={
                    answers[question.id] === "B"
                  }
                  onChange={() =>
                    handleAnswerChange(
                      question.id,
                      "B"
                    )
                  }
                />

                {question.option_b}
              </label>

              <label>
                <input
                  type="radio"
                  name={`question-${question.id}`}
                  value="C"
                  checked={
                    answers[question.id] === "C"
                  }
                  onChange={() =>
                    handleAnswerChange(
                      question.id,
                      "C"
                    )
                  }
                />

                {question.option_c}
              </label>

              <label>
                <input
                  type="radio"
                  name={`question-${question.id}`}
                  value="D"
                  checked={
                    answers[question.id] === "D"
                  }
                  onChange={() =>
                    handleAnswerChange(
                      question.id,
                      "D"
                    )
                  }
                />

                {question.option_d}
              </label>
            </div>
          ))
        )}

        <button
          className="submit-button"
          onClick={handleSubmit}
          disabled={loading || questions.length === 0}
        >
          {loading ? "Submitting..." : "Submit Exam"}
        </button>
      </div>
    </div>
  );
}

export default App;