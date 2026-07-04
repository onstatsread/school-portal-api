
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
import models, schemas
from auth import require_role, hash_password

router = APIRouter(prefix="/admin", tags=["Admin"])
admin_only = require_role("admin")


# ── Classes ──────────────────────────────────────────────────────────────────

@router.post("/classes", response_model=schemas.ClassOut)
def create_class(data: schemas.ClassCreate, db: Session = Depends(get_db), _=Depends(admin_only)):
    existing = db.query(models.Class).filter(
        models.Class.name == data.name.upper(),
        models.Class.section == data.section.upper()
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="This class/section already exists")
    cls = models.Class(name=data.name.upper(), section=data.section.upper())
    db.add(cls)
    db.commit()
    db.refresh(cls)
    return cls

@router.get("/classes", response_model=List[schemas.ClassOut])
def list_classes(db: Session = Depends(get_db), _=Depends(admin_only)):
    return db.query(models.Class).order_by(models.Class.name, models.Class.section).all()

@router.delete("/classes/{class_id}")
def delete_class(class_id: int, db: Session = Depends(get_db), _=Depends(admin_only)):
    cls = db.query(models.Class).filter(models.Class.id == class_id).first()
    if not cls:
        raise HTTPException(status_code=404, detail="Class not found")
    db.delete(cls)
    db.commit()
    return {"message": "Class deleted"}


# ── Subjects ─────────────────────────────────────────────────────────────────

@router.post("/subjects", response_model=schemas.SubjectOut)
def create_subject(data: schemas.SubjectCreate, db: Session = Depends(get_db), _=Depends(admin_only)):
    if db.query(models.Subject).filter(models.Subject.code == data.code.upper()).first():
        raise HTTPException(status_code=400, detail="Subject code already exists")
    subject = models.Subject(name=data.name, code=data.code.upper())
    db.add(subject)
    db.commit()
    db.refresh(subject)
    return subject

@router.get("/subjects", response_model=List[schemas.SubjectOut])
def list_subjects(db: Session = Depends(get_db), _=Depends(admin_only)):
    return db.query(models.Subject).order_by(models.Subject.name).all()


# ── Create Student ────────────────────────────────────────────────────────────

@router.post("/create-student")
def create_student(data: schemas.StudentCreate, db: Session = Depends(get_db), _=Depends(admin_only)):
    if db.query(models.User).filter(models.User.email == data.email).first():
        raise HTTPException(status_code=400, detail="Email already in use")
    if db.query(models.User).filter(models.User.username == data.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")
    if db.query(models.Student).filter(models.Student.admission_number == data.admission_number).first():
        raise HTTPException(status_code=400, detail="Admission number already exists")
    if not db.query(models.Class).filter(models.Class.id == data.class_id).first():
        raise HTTPException(status_code=404, detail="Class not found")

    user = models.User(
        full_name=data.full_name, email=data.email, username=data.username,
        password_hash=hash_password(data.password), role="student"
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    student = models.Student(
        user_id=user.id, class_id=data.class_id, admission_number=data.admission_number
    )
    db.add(student)
    db.commit()
    return {"message": "Student created successfully", "user_id": user.id, "username": data.username}


# ── Create Teacher ────────────────────────────────────────────────────────────

@router.post("/create-teacher")
def create_teacher(data: schemas.TeacherCreate, db: Session = Depends(get_db), _=Depends(admin_only)):
    if db.query(models.User).filter(models.User.email == data.email).first():
        raise HTTPException(status_code=400, detail="Email already in use")
    if db.query(models.User).filter(models.User.username == data.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")
    if db.query(models.Teacher).filter(models.Teacher.staff_id == data.staff_id).first():
        raise HTTPException(status_code=400, detail="Staff ID already exists")

    user = models.User(
        full_name=data.full_name, email=data.email, username=data.username,
        password_hash=hash_password(data.password), role="teacher"
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    teacher = models.Teacher(user_id=user.id, staff_id=data.staff_id)
    db.add(teacher)
    db.commit()
    return {"message": "Teacher created successfully", "user_id": user.id}


# ── Create Parent ─────────────────────────────────────────────────────────────

@router.post("/create-parent")
def create_parent(data: schemas.ParentCreate, db: Session = Depends(get_db), _=Depends(admin_only)):
    if db.query(models.User).filter(models.User.email == data.email).first():
        raise HTTPException(status_code=400, detail="Email already in use")
    if db.query(models.User).filter(models.User.username == data.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")

    user = models.User(
        full_name=data.full_name, email=data.email, username=data.username,
        password_hash=hash_password(data.password), role="parent"
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    parent = models.Parent(user_id=user.id, phone=data.phone)
    db.add(parent)
    db.commit()
    return {"message": "Parent created successfully", "user_id": user.id}


# ── Link Parent to Student ────────────────────────────────────────────────────

@router.post("/link-parent-student")
def link_parent_student(data: schemas.LinkParentStudent, db: Session = Depends(get_db), _=Depends(admin_only)):
    parent = db.query(models.Parent).filter(models.Parent.id == data.parent_id).first()
    student = db.query(models.Student).filter(models.Student.id == data.student_id).first()
    if not parent:
        raise HTTPException(status_code=404, detail="Parent not found")
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    existing = db.query(models.ParentStudent).filter(
        models.ParentStudent.parent_id == data.parent_id,
        models.ParentStudent.student_id == data.student_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Already linked")

    link = models.ParentStudent(parent_id=data.parent_id, student_id=data.student_id)
    db.add(link)
    db.commit()
    return {"message": "Parent linked to student successfully"}


# ── Assign Teacher to Subject + Class ─────────────────────────────────────────

@router.post("/assign-teacher")
def assign_teacher(data: schemas.AssignTeacher, db: Session = Depends(get_db), _=Depends(admin_only)):
    existing = db.query(models.TeacherSubjectClass).filter(
        models.TeacherSubjectClass.teacher_id == data.teacher_id,
        models.TeacherSubjectClass.subject_id == data.subject_id,
        models.TeacherSubjectClass.class_id == data.class_id,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Teacher already assigned to this subject/class")

    assignment = models.TeacherSubjectClass(
        teacher_id=data.teacher_id,
        subject_id=data.subject_id,
        class_id=data.class_id
    )
    db.add(assignment)
    db.commit()
    return {"message": "Teacher assigned successfully"}


# ── List Users ────────────────────────────────────────────────────────────────

@router.get("/users")
def list_users(role: str = None, db: Session = Depends(get_db), _=Depends(admin_only)):
    query = db.query(models.User)
    if role:
        query = query.filter(models.User.role == role)
    users = query.order_by(models.User.full_name).all()
    return [{"id": u.id, "full_name": u.full_name, "username": u.username,
             "email": u.email, "role": u.role, "is_active": u.is_active} for u in users]


# ── Deactivate/Activate User ──────────────────────────────────────────────────

@router.patch("/users/{user_id}/toggle-active")
def toggle_user_active(user_id: int, db: Session = Depends(get_db), _=Depends(admin_only)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = not user.is_active
    db.commit()
    status = "activated" if user.is_active else "deactivated"
    return {"message": f"User {status} successfully"}


# ── Reset Password ────────────────────────────────────────────────────────────

@router.patch("/users/{user_id}/reset-password")
def reset_password(user_id: int, new_password: str, db: Session = Depends(get_db), _=Depends(admin_only)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if len(new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    user.password_hash = hash_password(new_password)
    db.commit()
    return {"message": "Password reset successfully"}


# ── Dashboard Stats ───────────────────────────────────────────────────────────

@router.get("/stats")
def get_stats(db: Session = Depends(get_db), _=Depends(admin_only)):
    return {
        "total_students": db.query(models.Student).count(),
        "total_teachers": db.query(models.Teacher).count(),
        "total_parents": db.query(models.Parent).count(),
        "total_classes": db.query(models.Class).count(),
        "total_subjects": db.query(models.Subject).count(),
    }
