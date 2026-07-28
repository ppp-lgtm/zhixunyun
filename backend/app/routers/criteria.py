from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from app.models.database import SessionLocal
from app.models.tables import EvaluationCriteria, Task

router = APIRouter(prefix="/api/criteria", tags=["评价标准"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class CriteriaCreate(BaseModel):
    task_id: int
    name: str
    weight: float = 25.0
    description: str = ""


class CriteriaItem(BaseModel):
    name: str
    weight: float = 25.0
    description: str = ""


class CriteriaUpdate(BaseModel):
    name: Optional[str] = None
    weight: Optional[float] = None
    description: Optional[str] = None


# 获取某个任务的所有评价标准
@router.get("/{task_id}")
def get_criteria(task_id: int, db: Session = Depends(get_db)):
    criteria_list = db.query(EvaluationCriteria).filter(
        EvaluationCriteria.task_id == task_id
    ).all()
    return {
        "success": True,
        "data": [
            {"id": c.id, "name": c.name, "weight": c.weight, "description": c.description}
            for c in criteria_list
        ]
    }


# 创建评价标准
@router.post("/")
def create_criteria(req: CriteriaCreate, db: Session = Depends(get_db)):
    c = EvaluationCriteria(
        task_id=req.task_id,
        name=req.name,
        weight=req.weight,
        description=req.description
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return {"success": True, "data": {"id": c.id, "name": c.name, "weight": c.weight}}


# 更新评价标准
@router.put("/{criteria_id}")
def update_criteria(criteria_id: int, req: CriteriaUpdate, db: Session = Depends(get_db)):
    c = db.query(EvaluationCriteria).filter(EvaluationCriteria.id == criteria_id).first()
    if not c:
        raise HTTPException(404, "标准不存在")
    if req.name is not None:
        c.name = req.name
    if req.weight is not None:
        c.weight = req.weight
    if req.description is not None:
        c.description = req.description
    db.commit()
    return {"success": True, "message": "更新成功"}


# 删除评价标准
@router.delete("/{criteria_id}")
def delete_criteria(criteria_id: int, db: Session = Depends(get_db)):
    c = db.query(EvaluationCriteria).filter(EvaluationCriteria.id == criteria_id).first()
    if not c:
        raise HTTPException(404, "标准不存在")
    db.delete(c)
    db.commit()
    return {"success": True, "message": "已删除"}


# 保存整套标准（自动创建任务）
@router.post("/batch/{task_id}")
def batch_save(task_id: int, criteria_list: List[CriteriaItem], db: Session = Depends(get_db)):
    # 确保任务存在，不存在则创建
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        task = Task(id=task_id, title="默认实训任务", requirements="请配置实训要求", status="published")
        db.add(task)
        db.flush()

    # 删除旧标准
    db.query(EvaluationCriteria).filter(EvaluationCriteria.task_id == task_id).delete()

    # 批量创建
    for item in criteria_list:
        c = EvaluationCriteria(
            task_id=task_id,
            name=item.name,
            weight=item.weight,
            description=item.description
        )
        db.add(c)
    db.commit()
    return {"success": True, "message": f"已保存 {len(criteria_list)} 条标准"}