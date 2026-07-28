from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from datetime import datetime
import traceback

from app.models.database import SessionLocal
from app.routers.evaluate import router as evaluate_router
from app.routers.upload import router as upload_router
from app.routers.upload_eval import router as upload_eval_router
from app.routers.report import router as report_router
from app.routers.auth_router import router as auth_router_router
from app.routers.teacher_score import router as teacher_router
from app.routers.criteria import router as criteria_router
from app.routers.statistics import router as stats_router
from app.routers.class_router import router as class_router
from app.routers.user_profile import router as profile_router
from app.routers.task_manage import router as task_manage_router
from app.routers.notifications import router as notif_router
from app.utils.ai_evaluator import is_ai_configured
from app.routers.search import router as search_router
from app.routers.enterprise_router import router as enterprise_router

app = FastAPI(
    title="实训教学评价系统",
    description="基于大模型技术的软件实训教学结果检查评价与报表系统",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    error_detail = traceback.format_exc()
    print(f"[ERROR] {request.method} {request.url}")
    print(error_detail)

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "服务器内部错误，请联系管理员",
            "detail": str(exc) if app.debug else ""
        }
    )

app.include_router(evaluate_router)
app.include_router(upload_router)
app.include_router(upload_eval_router)
app.include_router(report_router)
app.include_router(auth_router_router)
app.include_router(teacher_router)
app.include_router(criteria_router)
app.include_router(stats_router)
app.include_router(class_router)
app.include_router(profile_router)
app.include_router(task_manage_router)
app.include_router(notif_router)
app.include_router(search_router)
app.include_router(enterprise_router)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.get("/")
def hello():
    return {"message": "实训评价系统启动成功！"}

@app.get("/api/health")
def health_check():
    db_ok = False
    db_error = ""
    try:
        from sqlalchemy import text
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        db_ok = True
    except Exception as e:
        db_error = str(e)

    return {
        "status": "ok" if db_ok and is_ai_configured() else "degraded",
        "database": "connected" if db_ok else f"disconnected: {db_error}",
        "ai_configured": is_ai_configured(),
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/test")
def test():
    return {"message": "前后端联通成功！", "status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)