from fastapi import APIRouter, Request, Form, Depends, status
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from database import SessionLocal
from models import Question, Answer, Resource, User, Notice, NoticeRecipient
import os
from datetime import datetime

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

def get_current_student(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("role") == "student":
            return payload
    except JWTError:
        return None
    return None

@router.get("/student/questions")
def get_questions(request: Request, db: Session = Depends(get_db)):
    student = get_current_student(request)
    if not student:
        return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)
    answers = db.query(Answer).filter(Answer.student_id == student["id"]).all()
    answered_question_ids = {a.question_id for a in answers}
    questions = db.query(Question).filter(~Question.id.in_(answered_question_ids)).all()
    answered_qids = {a.question_id for a in answers}
    return templates.TemplateResponse("student_questions.html", {"request": request, "questions": questions, "answered_qids": answered_qids})

@router.post("/student/submit-answer")
def submit_answer(request: Request, question_id: int = Form(...), selected_option: int = Form(...), db: Session = Depends(get_db)):
    try:
        student = get_current_student(request)
        if not student:
            return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)
        student_id = int(student["id"])
        question = db.query(Question).filter(Question.id == question_id).first()
        if not question:
            return RedirectResponse("/dashboard?error=invalid_question", status_code=status.HTTP_302_FOUND)
        # Check if already answered
        existing_answer = db.query(Answer).filter(
            Answer.question_id == question_id,
            Answer.student_id == student_id
        ).first()
        if existing_answer:
            return RedirectResponse("/dashboard?error=already_answered", status_code=status.HTTP_302_FOUND)
        # Check deadline
        if question.deadline and question.deadline < datetime.now():
            return RedirectResponse("/dashboard?error=deadline", status_code=status.HTTP_302_FOUND)
        answer = Answer(question_id=question_id, student_id=student_id, selected_option=selected_option)
        db.add(answer)
        db.commit()
        print(f"[DEBUG] Saved MCQ answer: student_id={student_id}, question_id={question_id}, selected_option={selected_option}")
        return RedirectResponse("/student/dashboard?success=submitted", status_code=status.HTTP_302_FOUND)
    except Exception as e:
        print(f"[ERROR] Exception in /student/submit-answer: {e}")
        return RedirectResponse("/student/dashboard?error=internal_error", status_code=status.HTTP_302_FOUND)

@router.post("/student/submit-descriptive-answer")
def submit_descriptive_answer(request: Request, question_id: int = Form(...), description: str = Form(...), db: Session = Depends(get_db)):
    try:
        student = get_current_student(request)
        if not student:
            return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)
        student_id = int(student["id"])
        question = db.query(Question).filter(Question.id == question_id).first()
        if not question:
            return RedirectResponse("/dashboard?error=invalid_question", status_code=status.HTTP_302_FOUND)
        # Check if already answered
        existing_answer = db.query(Answer).filter(
            Answer.question_id == question_id,
            Answer.student_id == student_id
        ).first()
        if existing_answer:
            return RedirectResponse("/dashboard?error=already_answered", status_code=status.HTTP_302_FOUND)
        # Check deadline
        if question.deadline and question.deadline < datetime.now():
            return RedirectResponse("/dashboard?error=deadline", status_code=status.HTTP_302_FOUND)
        answer = Answer(question_id=question_id, student_id=student_id, description=description)
        db.add(answer)
        db.commit()
        print(f"[DEBUG] Saved descriptive answer: student_id={student_id}, question_id={question_id}, description={description}")
        return RedirectResponse("/student/dashboard?success=submitted", status_code=status.HTTP_302_FOUND)
    except Exception as e:
        print(f"[ERROR] Exception in /student/submit-descriptive-answer: {e}")
        return RedirectResponse("/student/dashboard?error=internal_error", status_code=status.HTTP_302_FOUND)

@router.get("/student/peer-review")
def peer_review(request: Request, db: Session = Depends(get_db)):
    student = get_current_student(request)
    if not student:
        return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)
    # Get all descriptive questions and their answers
    questions = db.query(Question).filter(Question.type == "descriptive").all()
    peer_answers = []
    for question in questions:
        # Get all answers for this question except the current student's
        answers = db.query(Answer).filter(
            Answer.question_id == question.id,
            Answer.student_id != student["id"]
        ).all()
        # Check if current student has already submitted a peer review answer
        my_peer_review = db.query(Answer).filter(
            Answer.question_id == question.id,
            Answer.student_id == student["id"],
            Answer.is_peer_review == True
        ).first()
        # Check if current student has already submitted their own descriptive answer (not as a peer review)
        my_own_answer = db.query(Answer).filter(
            Answer.question_id == question.id,
            Answer.student_id == student["id"],
            Answer.is_peer_review == False
        ).first()
        peer_answers.append({
            "question": question,
            "answers": answers,
            "already_answered": my_peer_review is not None,
            "has_own_answer": my_own_answer is not None
        })
    return templates.TemplateResponse(
        "peer_review.html",
        {
            "request": request,
            "peer_answers": peer_answers,
            "student_id": student["id"]
        }
    )

@router.post("/student/submit-peer-review")
def submit_peer_review(
    request: Request,
    question_id: int = Form(...),
    description: str = Form(...),
    db: Session = Depends(get_db)
):
    student = get_current_student(request)
    if not student:
        return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)
    
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        return RedirectResponse("/student/peer-review?error=invalid_question", status_code=status.HTTP_302_FOUND)
    
    # Check if already answered
    existing_answer = db.query(Answer).filter(
        Answer.question_id == question_id,
        Answer.student_id == student["id"]
    ).first()
    
    if existing_answer:
        return RedirectResponse("/student/peer-review?error=already_answered", status_code=status.HTTP_302_FOUND)
    
    # Check deadline
    if question.deadline and question.deadline < datetime.now():
        return RedirectResponse("/student/peer-review?error=deadline", status_code=status.HTTP_302_FOUND)
    
    answer = Answer(
        question_id=question_id,
        student_id=student["id"],
        description=description,
        is_peer_review=True
    )
    db.add(answer)
    db.commit()
    return RedirectResponse("/student/peer-review?success=submitted", status_code=status.HTTP_302_FOUND)

@router.get("/student/resources")
def get_resources(request: Request, db: Session = Depends(get_db)):
    student = get_current_student(request)
    if not student:
        return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)
    resources = db.query(Resource).all()
    return templates.TemplateResponse("student_resources.html", {"request": request, "resources": resources})

@router.get("/student/dashboard")
def get_dashboard(request: Request, db: Session = Depends(get_db)):
    try:
        print("[DEBUG] Entered /student/dashboard route")
        student = get_current_student(request)
        if not student:
            print("[DEBUG] No student found, redirecting to login")
            return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)
        
        payload = jwt.decode(request.cookies.get("access_token"), SECRET_KEY, algorithms=[ALGORITHM])
        name = payload["name"]
        student_id = int(payload["id"])
        
        # Get all questions
        questions = db.query(Question).all()
        
        # Get student's answers (ensure int type for ID)
        answers = db.query(Answer).filter(Answer.student_id == student_id).all()
        answered_qids = {a.question_id for a in answers}
        print(f"[DEBUG] Answered question IDs: {answered_qids}")
        
        # Filter out questions that have been answered
        active_questions = [q for q in questions if int(q.id) not in answered_qids]
        print(f"[DEBUG] Active questions after filtering: {[q.id for q in active_questions]}")
        
        resources = db.query(Resource).all()
        now = datetime.now()
        
        # Fetch notices for this student
        notices = (
            db.query(Notice)
            .join(NoticeRecipient, Notice.id == NoticeRecipient.notice_id)
            .filter(NoticeRecipient.student_id == student_id)
            .order_by(Notice.created_at.desc())
            .all()
        )
        print(f"[DEBUG] Student dashboard: payload['id'] = {payload['id']} (type: {type(payload['id'])})")
        print(f"[DEBUG] Notices fetched: {len(notices)}")
        for n in notices:
            print(f"[DEBUG] Notice: id={n.id}, title={n.title}")
        
        return templates.TemplateResponse(
            "student_dashboard.html",
            {
                "request": request,
                "name": name,
                "resources": resources,
                "questions": active_questions,  # Only unanswered questions
                "answers": answers,
                "now": now,
                "notices": notices
            }
        )
    except Exception as e:
        print(f"[ERROR] Exception in /student/dashboard: {e}")
        return templates.TemplateResponse(
            "student_dashboard.html",
            {
                "request": request,
                "name": "",
                "resources": [],
                "questions": [],
                "answers": [],
                "now": datetime.now(),
                "notices": [],
                "error": "An error occurred while loading your dashboard. Please try again later."
            }
        )

@router.get("/student/grades")
def get_grades(request: Request, db: Session = Depends(get_db)):
    student = get_current_student(request)
    if not student:
        return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)
    answers = db.query(Answer).filter(Answer.student_id == student["id"]).all()
    return templates.TemplateResponse("student_grades.html", {"request": request, "answers": answers})
