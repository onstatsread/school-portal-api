from sqlalchemy import Column, Integer, String, Boolean, Date, Float, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import enum


class UserRole(str, enum.Enum):
    student = "student"
    teacher = "teacher"
    admin = "admin"
    parent = "parent"


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Class(Base):
    __tablename__ = "classes"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)       # e.g. "SS2"
    section = Column(String, nullable=False)    # e.g. "A"
    students = relationship("Student", back_populates="class_")
    teacher_assignments = relationship("TeacherSubjectClass", back_populates="class_")


class Subject(Base):
    __tablename__ = "subjects"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    code = Column(String, unique=True, nullable=False)


class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    class_id = Column(Integer, ForeignKey("classes.id"))
    admission_number = Column(String, unique=True, nullable=False)
    user = relationship("User")
    class_ = relationship("Class", back_populates="students")
    parent_links = relationship("ParentStudent", back_populates="student")
    attendances = relationship("Attendance", back_populates="student")
    grades = relationship("Grade", back_populates="student")


class Teacher(Base):
    __tablename__ = "teachers"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    staff_id = Column(String, unique=True, nullable=False)
    user = relationship("User")
    assignments = relationship("TeacherSubjectClass", back_populates="teacher")


class TeacherSubjectClass(Base):
    """Which teacher teaches which subject to which class"""
    __tablename__ = "teacher_subject_class"
    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id"))
    subject_id = Column(Integer, ForeignKey("subjects.id"))
    class_id = Column(Integer, ForeignKey("classes.id"))
    teacher = relationship("Teacher", back_populates="assignments")
    subject = relationship("Subject")
    class_ = relationship("Class", back_populates="teacher_assignments")


class Parent(Base):
    __tablename__ = "parents"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    phone = Column(String)
    user = relationship("User")
    children = relationship("ParentStudent", back_populates="parent")


class ParentStudent(Base):
    """Links parents to their children"""
    __tablename__ = "parent_student"
    id = Column(Integer, primary_key=True, index=True)
    parent_id = Column(Integer, ForeignKey("parents.id"))
    student_id = Column(Integer, ForeignKey("students.id"))
    parent = relationship("Parent", back_populates="children")
    student = relationship("Student", back_populates="parent_links")


class Attendance(Base):
    __tablename__ = "attendance"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    date = Column(Date, nullable=False)
    status = Column(String, nullable=False)  # present | absent | late
    marked_by = Column(Integer, ForeignKey("teachers.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    student = relationship("Student", back_populates="attendances")


class Grade(Base):
    __tablename__ = "grades"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    subject_id = Column(Integer, ForeignKey("subjects.id"))
    term = Column(String, nullable=False)     # First | Second | Third
    session = Column(String, nullable=False)  # e.g. "2024/2025"
    ca_score = Column(Float, default=0)       # Continuous Assessment (max 40)
    exam_score = Column(Float, default=0)     # Exam score (max 60)
    total = Column(Float, default=0)          # CA + Exam
    grade = Column(String)                    # A1, B2 ... F9 (Nigerian grading)
    entered_by = Column(Integer, ForeignKey("teachers.id"))
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    student = relationship("Student", back_populates="grades")
    subject = relationship("Subject")
