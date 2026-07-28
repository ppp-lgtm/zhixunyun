from fastapi import APIRouter
from pydantic import BaseModel
from app.utils.ai_evaluator import evaluate

router = APIRouter(prefix="/api/evaluate", tags=["AI评价"])

class EvalRequest(BaseModel):
    task_requirements: str
    student_content: str
    criteria: list = ["代码质量", "文档规范性", "功能实现度"]

@router.post("/")
def ai_evaluate(req: EvalRequest):
    result = evaluate(req.task_requirements, req.student_content, req.criteria)
    return {"success": True, "data": result}