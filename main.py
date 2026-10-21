from contextlib import asynccontextmanager
from datetime import date
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException, Query, Response, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Date, Integer, String, create_engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

DATABASE_URL = "sqlite:///./students.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    department: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
    phone_number: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    gender: Mapped[str] = mapped_column(String(30), nullable=False)


class StudentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    year: int = Field(ge=1, le=10, description="Academic year")
    department: str = Field(min_length=1, max_length=100)
    date_of_birth: date
    phone_number: str = Field(min_length=7, max_length=20, pattern=r"^[+0-9() -]+$")
    gender: Literal["Male", "Female", "Other", "Prefer not to say"]


class StudentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    year: int | None = Field(default=None, ge=1, le=10)
    department: str | None = Field(default=None, min_length=1, max_length=100)
    date_of_birth: date | None = None
    phone_number: str | None = Field(
        default=None, min_length=7, max_length=20, pattern=r"^[+0-9() -]+$"
    )
    gender: Literal["Male", "Female", "Other", "Prefer not to say"] | None = None


class StudentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    year: int
    department: str
    date_of_birth: date
    phone_number: str
    gender: str


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Student Information API",
    description="CRUD API for student information, backed by SQLite.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/", tags=["Health"])
def health_check():
    return {"status": "ok", "message": "Student Information API is running"}


@app.post(
    "/students",
    response_model=StudentRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Students"],
)
def create_student(payload: StudentCreate, db: Session = Depends(get_db)):
    if payload.date_of_birth > date.today():
        raise HTTPException(status_code=422, detail="Date of birth cannot be in the future")

    student = Student(**payload.model_dump())
    db.add(student)
    try:
        db.commit()
        db.refresh(student)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="A student with this phone number already exists",
        )
    return student


@app.get("/students", response_model=list[StudentRead], tags=["Students"])
def list_students(
    department: str | None = Query(default=None),
    year: int | None = Query(default=None, ge=1, le=10),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    statement = select(Student).order_by(Student.id).offset(skip).limit(limit)
    if department:
        statement = statement.where(Student.department.ilike(f"%{department}%"))
    if year is not None:
        statement = statement.where(Student.year == year)
    return list(db.scalars(statement).all())


@app.get("/students/{student_id}", response_model=StudentRead, tags=["Students"])
def get_student(student_id: int, db: Session = Depends(get_db)):
    student = db.get(Student, student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


@app.patch("/students/{student_id}", response_model=StudentRead, tags=["Students"])
def update_student(
    student_id: int,
    payload: StudentUpdate,
    db: Session = Depends(get_db),
):
    student = db.get(Student, student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")

    changes = payload.model_dump(exclude_unset=True)
    if changes.get("date_of_birth") and changes["date_of_birth"] > date.today():
        raise HTTPException(status_code=422, detail="Date of birth cannot be in the future")

    for field, value in changes.items():
        if value is not None:
            setattr(student, field, value)

    try:
        db.commit()
        db.refresh(student)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="A student with this phone number already exists",
        )
    return student


@app.delete(
    "/students/{student_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Students"],
)
def delete_student(student_id: int, db: Session = Depends(get_db)):
    student = db.get(Student, student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    db.delete(student)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
