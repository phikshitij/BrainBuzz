from fastapi import APIRouter, Request, Form, UploadFile, File, Depends, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from database import SessionLocal
from models import Question, Resource, User, Answer, Notice, NoticeRecipient
import os
from dotenv import load_dotenv

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

def save_file_locally(file: UploadFile) -> str:
    file_location = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_location, "wb") as f:
        f.write(file.file.read())
    return file.filename  # Return just the filename for URL referencing

router = APIRouter()
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))
SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
ALGORITHM = "HS256"

from models import ChatMessage
from datetime import datetime
from openrouter_api import get_openrouter_response

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/teacher/chatbot")
def chatbot_page(request: Request, db: Session = Depends(get_db)):
    teacher = get_current_teacher(request)
    if not teacher:
        return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)
    history = db.query(ChatMessage).filter(ChatMessage.teacher_id == teacher["id"]).order_by(ChatMessage.timestamp).all()
    return templates.TemplateResponse("teacher_chatbot.html", {"request": request, "history": history})

from fastapi.responses import JSONResponse

@router.post("/teacher/chatbot")
def chatbot_ask(request: Request, message: str = Form(...), db: Session = Depends(get_db)):
    teacher = get_current_teacher(request)
    if not teacher:
        return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)
    response = get_openrouter_response(message)
    chat = ChatMessage(teacher_id=teacher["id"], message=message, response=response, timestamp=datetime.now())
    db.add(chat)
    db.commit()
    return RedirectResponse("/teacher/chatbot", status_code=status.HTTP_302_FOUND)

@router.post("/teacher/chatbot/ajax")
async def chatbot_ask_ajax(request: Request, db: Session = Depends(get_db)):
    import json
    teacher = get_current_teacher(request)
    if not teacher:
        return JSONResponse({"error": "Not authenticated"}, status_code=401)
    data = await request.json()
    message = data.get("message", "")
    response = get_openrouter_response(message)
    now = datetime.now()
    chat = ChatMessage(teacher_id=teacher["id"], message=message, response=response, timestamp=now)
    db.add(chat)
    db.commit()
    return JSONResponse({"response": response, "timestamp": now.strftime("%Y-%m-%d %H:%M")})

@router.post("/teacher/chatbot/clear")
def clear_chat_history(request: Request, db: Session = Depends(get_db)):
    teacher = get_current_teacher(request)
    if not teacher:
        return JSONResponse({"error": "Not authenticated"}, status_code=401)
    db.query(ChatMessage).filter(ChatMessage.teacher_id == teacher["id"]).delete()
    db.commit()
    return JSONResponse({"status": "cleared"})

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

@router.post("/teacher/post-question")
def post_question(
    request: Request,
    question: str = Form(...),
    option1: str = Form(...),
    option2: str = Form(...),
    option3: str = Form(...),
    option4: str = Form(...),
    correct_option: int = Form(...),
    deadline: str = Form(...),
    db: Session = Depends(get_db)
):
    from datetime import datetime
    teacher = get_current_teacher(request)
    if not teacher:
        return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)
    deadline_dt = datetime.strptime(deadline, "%Y-%m-%dT%H:%M")
    q = Question(
        text=question,
        posted_by=teacher["id"],
        type="mcq",
        option1=option1,
        option2=option2,
        option3=option3,
        option4=option4,
        correct_option=correct_option,
        deadline=deadline_dt
    )
    db.add(q)
    db.commit()
    return RedirectResponse("/dashboard", status_code=status.HTTP_302_FOUND)

@router.post("/teacher/post-descriptive-question")
def post_descriptive_question(
    request: Request,
    question: str = Form(...),
    deadline: str = Form(...),
    db: Session = Depends(get_db)
):
    from datetime import datetime
    teacher = get_current_teacher(request)
    if not teacher:
        return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)
    deadline_dt = datetime.strptime(deadline, "%Y-%m-%dT%H:%M")
    q = Question(
        text=question,
        posted_by=teacher["id"],
        type="descriptive",
        deadline=deadline_dt
    )
    db.add(q)
    db.commit()
    return RedirectResponse("/dashboard", status_code=status.HTTP_302_FOUND)

@router.post("/teacher/delete-question")
def delete_question(request: Request, question_id: int = Form(...), db: Session = Depends(get_db)):
    teacher = get_current_teacher(request)
    if not teacher:
        return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)
    question = db.query(Question).filter(Question.id == question_id, Question.posted_by == teacher["id"]).first()
    if question:
        # Delete all answers for this question
        db.query(Answer).filter(Answer.question_id == question_id).delete()
        db.delete(question)
        db.commit()
    return RedirectResponse("/dashboard", status_code=status.HTTP_302_FOUND)

@router.post("/teacher/upload-resource")
def upload_resource(request: Request, type: str = Form(...), file: UploadFile = File(...), db: Session = Depends(get_db)):
    teacher = get_current_teacher(request)
    if not teacher:
        return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)
    filename = save_file_locally(file)
    url = f"/uploads/{filename}"
    res = Resource(type=type, url=url, posted_by=teacher["id"])
    db.add(res)
    db.commit()
    return RedirectResponse("/dashboard", status_code=status.HTTP_302_FOUND)

@router.post("/teacher/delete-resource")
def delete_resource(request: Request, resource_id: int = Form(...), db: Session = Depends(get_db)):
    teacher = get_current_teacher(request)
    if not teacher:
        return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)
    resource = db.query(Resource).filter(Resource.id == resource_id, Resource.posted_by == teacher["id"]).first()
    if resource:
        # Remove file from uploads folder
        import os
        uploads_folder = os.path.join(os.path.dirname(__file__), "uploads")
        filename = resource.url.split("/uploads/")[-1]
        file_path = os.path.join(uploads_folder, filename)
        if os.path.exists(file_path):
            os.remove(file_path)
        db.delete(resource)
        db.commit()
    return RedirectResponse("/dashboard", status_code=status.HTTP_302_FOUND)

@router.get("/teacher/students")
def view_students(request: Request, db: Session = Depends(get_db)):
    teacher = get_current_teacher(request)
    if not teacher:
        return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)
    students = db.query(User).filter(User.role == "student").all()
    notices = db.query(Notice).filter(Notice.teacher_id == teacher["id"]).order_by(Notice.created_at.desc()).all()
    return templates.TemplateResponse("teacher_students.html", {"request": request, "students": students, "notices": notices})

@router.post("/teacher/post-notice")
def post_notice(request: Request, title: str = Form(...), content: str = Form(...), recipients: list = Form(...), db: Session = Depends(get_db)):
    teacher = get_current_teacher(request)
    if not teacher:
        return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)
    # Ensure recipients is always a list
    if isinstance(recipients, str):
        recipients = [recipients]
    print(f"[DEBUG] Recipients received: {recipients}")  # Debug print
    # If all students are selected, ensure all student IDs are included
    all_students = db.query(User).filter(User.role == "student").all()
    all_student_ids = {str(s.id) for s in all_students}
    selected_ids = set(recipients)
    # If all students are selected (by count or by select-all logic), use all student IDs
    if selected_ids == all_student_ids or len(selected_ids) == len(all_student_ids):
        recipients = list(all_student_ids)
    notice = Notice(title=title, content=content, teacher_id=teacher["id"])
    db.add(notice)
    db.commit()
    db.refresh(notice)
    # Add recipients
    for student_id in recipients:
        db.add(NoticeRecipient(notice_id=notice.id, student_id=int(student_id)))
    db.commit()
    return RedirectResponse("/teacher/students", status_code=status.HTTP_302_FOUND)

@router.post("/teacher/delete-notice")
def delete_notice(request: Request, notice_id: int = Form(...), db: Session = Depends(get_db)):
    teacher = get_current_teacher(request)
    if not teacher:
        return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)
    notice = db.query(Notice).filter(Notice.id == notice_id, Notice.teacher_id == teacher["id"]).first()
    if notice:
        db.delete(notice)
        db.commit()
    return RedirectResponse("/teacher/students", status_code=status.HTTP_302_FOUND)

@router.get("/teacher/dashboard")
def teacher_dashboard(request: Request, db: Session = Depends(get_db)):
    teacher = get_current_teacher(request)
    if not teacher:
        return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)

    # Example data you might want to show on the dashboard
    questions = db.query(Question).filter(Question.posted_by == teacher["id"]).all()
    notices = db.query(Notice).filter(Notice.teacher_id == teacher["id"]).all()
    resources = db.query(Resource).filter(Resource.posted_by == teacher["id"]).all()

    return templates.TemplateResponse("teacher_dashboard.html", {
        "request": request,
        "teacher": teacher,
        "questions": questions,
        "notices": notices,
        "resources": resources
    })
