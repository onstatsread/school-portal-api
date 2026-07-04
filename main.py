from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import engine, Base, get_db
import models
from routers import auth_router, admin_router, portal_router
from auth import hash_password

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="School Portal API",
    description="Backend for secondary school portal",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(admin_router.router)
app.include_router(portal_router.router)

@app.get("/")
def root():
    return {"message": "School Portal API is running", "version": "1.0.0"}

@app.get("/debug")
def debug():
    from database import SessionLocal
    db = SessionLocal()
    try:
        from models import User, Student, Teacher, Class, Subject
        return {
            "status": "ok",
            "tables": list(Base.metadata.tables.keys()),
            "counts": {
                "users": db.query(User).count(),
                "students": db.query(Student).count(),
                "teachers": db.query(Teacher).count(),
                "classes": db.query(Class).count(),
                "subjects": db.query(Subject).count(),
            }
        }
    except Exception as e:
        return {"status": "error", "detail": str(e)}
    finally:
        db.close()

@app.post("/bootstrap-admin")
def bootstrap_admin(db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(
        models.User.role == models.UserRole.admin
    ).first()
    if existing:
        return {"message": "Admin already exists. This endpoint is disabled."}
    admin = models.User(
        full_name="School Admin",
        email="admin@school.com",
        username="admin",
        password_hash=hash_password("admin1234"),
        role=models.UserRole.admin
    )
    db.add(admin)
    db.commit()
    return {
        "message": "Admin created!",
        "username": "admin",
        "password": "admin1234"
    }
    
