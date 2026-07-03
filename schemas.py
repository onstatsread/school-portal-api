from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import date


# ── Auth ────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    full_name: str
    user_id: int


# ── Users ───────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    username: str
    password: str
    role: str  # student | teacher | admin | parent

class UserOut(BaseModel):
    id: int
    full_name: str
    email: str
    username: str
    role: str
    is_active: bool

    class Config:
        from_attributes = True


# ── Classes & Subjects ──────────────────────────────────────────────────────

class ClassCreate(BaseModel):
    name: str     # e.g. SS1, SS2, SS3, JSS1 ...
    section: str  # A, B, C, D ...

class ClassOut(BaseModel):
    id: int
    name: str
    section: str

    class Config:
        from_attributes = True

class SubjectCreate(BaseModel):
    name: str
    code: str

class SubjectOut(BaseModel):
    id: int
    name: str
    code: str

    class Config:
        from_attributes = True


# ── Profiles ────────────────────────────────────────────────────────────────

class StudentCreate(BaseModel):
    full_name: str
    email: EmailStr
    username: str
    password: str
    class_id: int
    admission_number: str

class TeacherCreate(BaseModel):
    full_name: str
    email: EmailStr
    username: str
    password: str
    staff_id: str

class ParentCreate(BaseModel):
    full_name: str
    email: EmailStr
    username: str
    password: str
    phone: Optional[str] = None

class LinkParentStudent(BaseModel):
    parent_id: int
    student_id: int

class AssignTeacher(BaseModel):
    teacher_id: int
    subject_id: int
    class_id: int


# ── Attendance ───────────────────────────────────────────────────────────────

class AttendanceEntry(BaseModel):
    student_id: int
    status: str  # present | absent | late

class AttendanceBulk(BaseModel):
    date: date
    class_id: int
    records: List[AttendanceEntry]

class AttendanceOut(BaseModel):
    id: int
    student_id: int
    date: date
    status: str

    class Config:
        from_attributes = True


# ── Grades ───────────────────────────────────────────────────────────────────

class GradeEntry(BaseModel):
    student_id: int
    subject_id: int
    term: str      # First | Second | Third
    session: str   # e.g. 2024/2025
    ca_score: float
    exam_score: float

class GradeOut(BaseModel):
    id: int
    student_id: int
    subject_id: int
    term: str
    session: str
    ca_score: float
    exam_score: float
    total: float
    grade: Optional[str]

    class Config:
        from_attributes = True
