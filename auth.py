from fastapi import APIRouter, Request, Form, status, Depends
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import jwt
from database import SessionLocal
from models import User
import os

SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
ALGORITHM = "HS256"

router = APIRouter()
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_access_token(data: dict):
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

@router.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})

@router.post("/login")
def login(request: Request, email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    error = None
    if not user or not pwd_context.verify(password, user.password_hash):
        error = "Invalid email or password."
        return templates.TemplateResponse("login.html", {"request": request, "error": error})
    # Create JWT token
    token = create_access_token({"sub": user.email, "role": user.role, "name": user.name, "id": user.id})
    if user.role == "student":
        response = RedirectResponse(url="/student/dashboard", status_code=status.HTTP_302_FOUND)
    else:
        response = RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    response.set_cookie(key="access_token", value=token, httponly=True)
    return response

@router.get("/register")
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request, "error": None})

@router.post("/register")
def register(request: Request, name: str = Form(...), email: str = Form(...), password: str = Form(...), role: str = Form(...), db: Session = Depends(get_db)):
    error = None
    if db.query(User).filter(User.email == email).first():
        error = "Email already registered."
        return templates.TemplateResponse("register.html", {"request": request, "error": error})
    hashed_password = pwd_context.hash(password)
    user = User(name=name, email=email, password_hash=hashed_password, role=role)
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token({"sub": user.email, "role": user.role, "name": user.name, "id": user.id})
    response = RedirectResponse(url=f"/dashboard", status_code=status.HTTP_302_FOUND)
    response.set_cookie(key="access_token", value=token, httponly=True)
    return response
