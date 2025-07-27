from fastapi import APIRouter, Request, Form, Depends, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from database import SessionLocal
from models import Question, Answer, User
import os

router = APIRouter()
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))
SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
ALGORITHM = "HS256"

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_teacher(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("role") == "teacher":
            return payload
    except JWTError:
        return None
    return None

@router.get("/teacher/answers")
def view_answers(request: Request, db: Session = Depends(get_db)):
    teacher = get_current_teacher(request)
    if not teacher:
        return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)
    questions = db.query(Question).filter(Question.posted_by == teacher["id"]).all()
    answers = db.query(Answer).all()
    students = {u.id: u.name for u in db.query(User).filter(User.role == "student").all()}
    return templates.TemplateResponse("teacher_answers.html", {"request": request, "questions": questions, "answers": answers, "students": students})

@router.post("/teacher/grade-answer")
def grade_answer(request: Request, answer_id: int = Form(...), grade: int = Form(...), db: Session = Depends(get_db)):
    teacher = get_current_teacher(request)
    if not teacher:
        return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)
    answer = db.query(Answer).filter(Answer.id == answer_id).first()
    if answer:
        answer.grade = grade
        db.commit()
    return RedirectResponse("/teacher/answers", status_code=status.HTTP_302_FOUND)

@router.post("/teacher/grade-answer")
def grade_answer(request: Request, answer_id: int = Form(...), grade: int = Form(...), db: Session = Depends(get_db)):
    teacher = get_current_teacher(request)
    if not teacher:
        return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)
    answer = db.query(Answer).filter(Answer.id == answer_id).first()
    if answer:
        answer.grade = grade
        db.commit()
    return RedirectResponse("/teacher/answers", status_code=status.HTTP_302_FOUND)
