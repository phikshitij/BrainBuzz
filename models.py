from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime, Boolean
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50))
    email = Column(String(100), unique=True, index=True)
    password_hash = Column(String(128))
    role = Column(String(10))  # 'teacher' or 'student'
    answers = relationship("Answer", back_populates="student")

class Question(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True, index=True)
    text = Column(String(500))
    posted_by = Column(Integer, ForeignKey("users.id"))
    type = Column(String(20), default="mcq")  # 'mcq' or 'descriptive'
    option1 = Column(String(200), nullable=True)
    option2 = Column(String(200), nullable=True)
    option3 = Column(String(200), nullable=True)
    option4 = Column(String(200), nullable=True)
    correct_option = Column(Integer, nullable=True)  # 1-4, which option is correct
    deadline = Column(DateTime)  # New field for deadline
    answers = relationship("Answer", back_populates="question")

class Answer(Base):
    __tablename__ = "answers"
    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"))
    student_id = Column(Integer, ForeignKey("users.id"))
    selected_option = Column(Integer, nullable=True)  # For MCQ
    description = Column(String(2000), nullable=True)  # For descriptive answers
    grade = Column(Integer, nullable=True)  # Assigned by teacher
    answer_text = Column(Text, nullable=True)  # Keep for backward compatibility
    is_peer_review = Column(Boolean, default=False)  # Flag for peer review answers
    timestamp = Column(DateTime, default=datetime.utcnow)  # Timestamp for when the answer was submitted
    question = relationship("Question", back_populates="answers")
    student = relationship("User", back_populates="answers")

class Resource(Base):
    __tablename__ = "resources"
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(10))  # 'video' or 'note'
    url = Column(Text)
    posted_by = Column(Integer, ForeignKey("users.id"))

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(Integer, ForeignKey("users.id"))
    message = Column(Text)
    response = Column(Text)
    timestamp = Column(DateTime)

class Notice(Base):
    __tablename__ = "notices"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255))
    content = Column(Text)
    teacher_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    recipients = relationship("NoticeRecipient", back_populates="notice")

class NoticeRecipient(Base):
    __tablename__ = "notice_recipients"
    id = Column(Integer, primary_key=True, index=True)
    notice_id = Column(Integer, ForeignKey("notices.id"))
    student_id = Column(Integer, ForeignKey("users.id"))
    notice = relationship("Notice", back_populates="recipients")
