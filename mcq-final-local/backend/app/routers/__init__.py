try:
	from app.routers import auth, exam_questions, exams, questions, subjects
except ModuleNotFoundError:
	from backend.app.routers import auth, exam_questions, exams, questions, subjects