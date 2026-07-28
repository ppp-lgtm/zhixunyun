from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.models.database import SessionLocal
from app.models.tables import Task
from app.models.class_models import Class

router = APIRouter(prefix="/api/search", tags=["全局搜索"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/")
def search(q: str = "", db: Session = Depends(get_db)):
    if not q.strip():
        return {"success": True, "data": []}

    keyword = f"%{q}%"
    results = []

    # 搜任务
    tasks = db.query(Task).filter(Task.title.like(keyword)).limit(5).all()
    for t in tasks:
        results.append({
            "id": t.id,
            "title": t.title,
            "type": "任务",
            "path": "/app/task-manage"
        })

    # 搜班级
    classes = db.query(Class).filter(Class.name.like(keyword)).limit(5).all()
    for c in classes:
        results.append({
            "id": c.id,
            "title": c.name,
            "type": "班级",
            "path": "/app/class-manage"
        })

    return {"success": True, "data": results}