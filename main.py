from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from auth import router as auth_router
from teacher import router as teacher_router
from student import router as student_router
from teacher_view import router as teacher_view_router
import os
from dotenv import load_dotenv
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from models import Resource, Question, Answer
from database import get_db


load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static and template setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
app.mount("/uploads", StaticFiles(directory=os.path.join(BASE_DIR, "uploads")), name="uploads")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
ALGORITHM = "HS256"

app.include_router(auth_router)
app.include_router(teacher_router)
app.include_router(student_router)
app.include_router(teacher_view_router)

@app.get("/")
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/logout")
def logout():
    response = RedirectResponse("/login", status_code=302)
    response.delete_cookie("access_token")
    return response

@app.get("/dashboard")
def dashboard(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse("/login", status_code=302)
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        role = payload.get("role")
        name = payload.get("name")
    except JWTError:
        return RedirectResponse("/login", status_code=302)
    try:
        resources = db.query(Resource).all()
        questions = db.query(Question).all()
    except Exception as e:
        resources = []
        questions = []
        print("Error fetching resources/questions:", e)
    if role == "teacher":
        return templates.TemplateResponse("teacher_dashboard.html", {"request": request, "name": name, "resources": resources, "questions": questions})
    else:
        # Fetch student's answers for grade display
        answers = db.query(Answer).filter(Answer.student_id == payload["id"]).all()
        return templates.TemplateResponse("student_dashboard.html", {"request": request, "name": name, "resources": resources, "questions": questions, "answers": answers})
