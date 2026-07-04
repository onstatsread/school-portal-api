from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
import models
from routers import auth_router, admin_router, portal_router

# Create all tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="School Portal API",
    description="Backend for secondary school portal — attendance, grades, 4 user roles",
    version="1.0.0"
)

# Allow GitHub Pages frontend to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to your GitHub Pages URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(admin_router.router)
app.include_router(portal_router.router)


@app.get("/")
def root():
    return {
        "message": "School Portal API is running",
        "version": "1.0.0",
        "docs": "/docs"
    }


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
