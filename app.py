# app.py
from typing import List, Optional
from datetime import date

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from sqlalchemy import create_engine, Column, Integer, String, Date
from sqlalchemy.orm import declarative_base, sessionmaker, Session

DATABASE_URL = "sqlite:///./students.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


# SQLAlchemy model
class StudentModel(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    dob = Column(Date, nullable=True)


# Create tables (safe to run every start)
Base.metadata.create_all(bind=engine)


# Pydantic schemas
class StudentCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    dob: Optional[date] = None


class StudentRead(StudentCreate):
    id: int

    class Config:
        orm_mode = True


# single FastAPI app
app = FastAPI(title="Student DB - Simple")

# CORS (development only — narrow origins for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # change to ["http://127.0.0.1:5500"] for more safety
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Create student
@app.post("/students", response_model=StudentRead, status_code=201)
def create_student(payload: StudentCreate, db: Session = Depends(get_db)):
    exists = db.query(StudentModel).filter(StudentModel.email == payload.email).first()
    if exists:
        raise HTTPException(status_code=400, detail="Email already registered")

    student = StudentModel(
        first_name=payload.first_name,
        last_name=payload.last_name,
        email=payload.email,
        dob=payload.dob,
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


# Read all students
@app.get("/students", response_model=List[StudentRead])
def list_students(db: Session = Depends(get_db)):
    students = db.query(StudentModel).all()
    return students


# Read single student
@app.get("/students/{student_id}", response_model=StudentRead)
def get_student(student_id: int, db: Session = Depends(get_db)):
    student = db.get(StudentModel, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


# Update student
@app.put("/students/{student_id}", response_model=StudentRead)
def update_student(student_id: int, payload: StudentCreate, db: Session = Depends(get_db)):
    student = db.get(StudentModel, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    student.first_name = payload.first_name
    student.last_name = payload.last_name
    student.email = payload.email
    student.dob = payload.dob
    db.commit()
    db.refresh(student)
    return student


# Delete student
@app.delete("/students/{student_id}", status_code=204)
def delete_student(student_id: int, db: Session = Depends(get_db)):
    student = db.get(StudentModel, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    db.delete(student)
    db.commit()
    return None
