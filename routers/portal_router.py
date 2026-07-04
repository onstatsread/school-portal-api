from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from database import get_db
import models, schemas
from auth import require_role, get_current_user

router = APIRouter(prefix="/portal", tags=["Portal"])


# ──────────────────────────────────────────────────────────────
# ATTENDANCE
# ──────────────────────────────────────────────────────────────

@router.post("/attendance/bulk")
def mark_attendance_bulk(
    data: schemas.AttendanceBulk,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role("teacher", "admin"))
):
    """Teacher marks attendance for a whole class at once"""
    teacher = db.query(models.Teacher).filter(models.Teacher.user_id == current_user.id).first()
    teacher_id = teacher.id if teacher else None

    results = []
    for entry in data.records:
        # Check if attendance already marked for this student/date
        existing = db.query(models.Attendance).filter(
            models.Attendance.student_id == entry.student_id,
            models.Attendance.date == data.date
        ).first()
        if existing:
            existing.status = entry.status  # Update if already marked
        else:
            record = models.Attendance(
                student_id=entry.student_id,
                date=data.date,
                status=entry.status,
                marked_by=teacher_id
            )
            db.add(record)
        results.append(entry.student_id)

    db.commit()
    return {"message": f"Attendance marked for {len(results)} students", "date": data.date}


@router.get("/attendance/class/{class_id}")
def get_class_attendance(
    class_id: int,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: Session = Depends(get_db),
    _=Depends(require_role("teacher", "admin"))
):
    """Get attendance records for all students in a class"""
    students = db.query(models.Student).filter(models.Student.class_id == class_id).all()
    student_ids = [s.id for s in students]

    query = db.query(models.Attendance).filter(models.Attendance.student_id.in_(student_ids))
    if date_from:
        query = query.filter(models.Attendance.date >= date_from)
    if date_to:
        query = query.filter(models.Attendance.date <= date_to)

    records = query.order_by(models.Attendance.date.desc()).all()
    return [{"id": r.id, "student_id": r.student_id, "date": r.date, "status": r.status} for r in records]


@router.get("/attendance/student/{student_id}")
def get_student_attendance(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Students can view their own; parents can view their child's; teachers/admin view any"""
    if current_user.role.value == "student":
        student = db.query(models.Student).filter(models.Student.user_id == current_user.id).first()
        if not student or student.id != student_id:
            raise HTTPException(status_code=403, detail="You can only view your own attendance")

    elif current_user.role.value == "parent":
        parent = db.query(models.Parent).filter(models.Parent.user_id == current_user.id).first()
        link = db.query(models.ParentStudent).filter(
            models.ParentStudent.parent_id == parent.id,
            models.ParentStudent.student_id == student_id
        ).first()
        if not link:
            raise HTTPException(status_code=403, detail="You can only view your child's attendance")

    records = db.query(models.Attendance).filter(
        models.Attendance.student_id == student_id
    ).order_by(models.Attendance.date.desc()).all()

    total = len(records)
    present = len([r for r in records if r.status == "present"])
    absent = len([r for r in records if r.status == "absent"])
    late = len([r for r in records if r.status == "late"])

    return {
        "summary": {"total": total, "present": present, "absent": absent, "late": late,
                    "attendance_rate": round((present / total * 100) if total else 0, 1)},
        "records": [{"id": r.id, "date": r.date, "status": r.status} for r in records]
    }


# ──────────────────────────────────────────────────────────────
# GRADES
# ──────────────────────────────────────────────────────────────

def compute_grade(total: float) -> str:
    """Nigerian secondary school grading (WAEC scale)"""
    if total >= 75: return "A1"
    elif total >= 70: return "B2"
    elif total >= 65: return "B3"
    elif total >= 60: return "C4"
    elif total >= 55: return "C5"
    elif total >= 50: return "C6"
    elif total >= 45: return "D7"
    elif total >= 40: return "E8"
    else: return "F9"


@router.post("/grades/enter")
def enter_grade(
    data: schemas.GradeEntry,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role("teacher", "admin"))
):
    """Teacher enters or updates a grade"""
    if data.ca_score > 40:
        raise HTTPException(status_code=400, detail="CA score cannot exceed 40")
    if data.exam_score > 60:
        raise HTTPException(status_code=400, detail="Exam score cannot exceed 60")

    teacher = db.query(models.Teacher).filter(models.Teacher.user_id == current_user.id).first()
    teacher_id = teacher.id if teacher else None

    total = data.ca_score + data.exam_score
    grade_str = compute_grade(total)

    existing = db.query(models.Grade).filter(
        models.Grade.student_id == data.student_id,
        models.Grade.subject_id == data.subject_id,
        models.Grade.term == data.term,
        models.Grade.session == data.session
    ).first()

    if existing:
        existing.ca_score = data.ca_score
        existing.exam_score = data.exam_score
        existing.total = total
        existing.grade = grade_str
        existing.entered_by = teacher_id
        db.commit()
        return {"message": "Grade updated", "total": total, "grade": grade_str}

    record = models.Grade(
        student_id=data.student_id,
        subject_id=data.subject_id,
        term=data.term,
        session=data.session,
        ca_score=data.ca_score,
        exam_score=data.exam_score,
        total=total,
        grade=grade_str,
        entered_by=teacher_id
    )
    db.add(record)
    db.commit()
    return {"message": "Grade entered", "total": total, "grade": grade_str}


@router.get("/grades/student/{student_id}")
def get_student_grades(
    student_id: int,
    term: Optional[str] = None,
    session: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get a student's result sheet"""
    if current_user.role.value == "student":
        student = db.query(models.Student).filter(models.Student.user_id == current_user.id).first()
        if not student or student.id != student_id:
            raise HTTPException(status_code=403, detail="You can only view your own grades")

    elif current_user.role.value == "parent":
        parent = db.query(models.Parent).filter(models.Parent.user_id == current_user.id).first()
        link = db.query(models.ParentStudent).filter(
            models.ParentStudent.parent_id == parent.id,
            models.ParentStudent.student_id == student_id
        ).first()
        if not link:
            raise HTTPException(status_code=403, detail="You can only view your child's grades")

    query = db.query(models.Grade).filter(models.Grade.student_id == student_id)
    if term:
        query = query.filter(models.Grade.term == term)
    if session:
        query = query.filter(models.Grade.session == session)

    grades = query.all()
    result = []
    for g in grades:
        subject = db.query(models.Subject).filter(models.Subject.id == g.subject_id).first()
        result.append({
            "subject": subject.name if subject else "Unknown",
            "subject_code": subject.code if subject else "",
            "term": g.term,
            "session": g.session,
            "ca_score": g.ca_score,
            "exam_score": g.exam_score,
            "total": g.total,
            "grade": g.grade
        })

    total_subjects = len(result)
    avg = round(sum(r["total"] for r in result) / total_subjects, 1) if total_subjects else 0
    return {"grades": result, "summary": {"subjects": total_subjects, "average": avg}}


@router.get("/grades/class/{class_id}")
def get_class_grades(
    class_id: int,
    subject_id: int,
    term: str,
    session: str,
    db: Session = Depends(get_db),
    _=Depends(require_role("teacher", "admin"))
):
    """Get all grades for a subject in a class — for result entry/review"""
    students = db.query(models.Student).filter(models.Student.class_id == class_id).all()
    result = []
    for student in students:
        grade = db.query(models.Grade).filter(
            models.Grade.student_id == student.id,
            models.Grade.subject_id == subject_id,
            models.Grade.term == term,
            models.Grade.session == session
        ).first()
        result.append({
            "student_id": student.id,
            "admission_number": student.admission_number,
            "full_name": student.user.full_name if student.user else "",
            "ca_score": grade.ca_score if grade else None,
            "exam_score": grade.exam_score if grade else None,
            "total": grade.total if grade else None,
            "grade": grade.grade if grade else None
        })
    return result


# ──────────────────────────────────────────────────────────────
# STUDENT PROFILE
# ──────────────────────────────────────────────────────────────

@router.get("/student/profile")
def get_my_profile(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role("student"))
):
    student = db.query(models.Student).filter(models.Student.user_id == current_user.id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")
    cls = student.class_
    return {
        "full_name": current_user.full_name,
        "username": current_user.username,
        "email": current_user.email,
        "admission_number": student.admission_number,
        "class": f"{cls.name} {cls.section}" if cls else "Not assigned"
    }


# ──────────────────────────────────────────────────────────────
# TEACHER PROFILE
# ──────────────────────────────────────────────────────────────

@router.get("/teacher/my-classes")
def get_my_classes(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role("teacher"))
):
    teacher = db.query(models.Teacher).filter(models.Teacher.user_id == current_user.id).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher profile not found")

    assignments = db.query(models.TeacherSubjectClass).filter(
        models.TeacherSubjectClass.teacher_id == teacher.id
    ).all()

    return [
        {
            "class_id": a.class_id,
            "class_name": f"{a.class_.name} {a.class_.section}" if a.class_ else "",
            "subject_id": a.subject_id,
            "subject_name": a.subject.name if a.subject else "",
            "student_count": db.query(models.Student).filter(
                models.Student.class_id == a.class_id).count()
        }
        for a in assignments
    ]


# ──────────────────────────────────────────────────────────────
# PARENT — view all children
# ──────────────────────────────────────────────────────────────

@router.get("/parent/children")
def get_my_children(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role("parent"))
):
    parent = db.query(models.Parent).filter(models.Parent.user_id == current_user.id).first()
    if not parent:
        raise HTTPException(status_code=404, detail="Parent profile not found")

    links = db.query(models.ParentStudent).filter(models.ParentStudent.parent_id == parent.id).all()
    children = []
    for link in links:
        s = link.student
        cls = s.class_
        children.append({
            "student_id": s.id,
            "full_name": s.user.full_name if s.user else "",
            "admission_number": s.admission_number,
            "class": f"{cls.name} {cls.section}" if cls else "Not assigned"
        })
    return children
