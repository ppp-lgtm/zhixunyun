import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Mock pymysql 避免缺驱动时 import 失败（我们只验证模型结构不连库）
from types import ModuleType
_pymysql_mock = ModuleType("pymysql")
_pymysql_mock.paramstyle = "pyformat"
_pymysql_mock.threadsafety = 2
sys.modules.setdefault("pymysql", _pymysql_mock)
sys.modules.setdefault("MySQLdb", _pymysql_mock)
_cursors = ModuleType("pymysql.cursors")
sys.modules["pymysql.cursors"] = _cursors

from app.models.database import Base
from app.models.tables import User, Task, Submission, Evaluation, EvaluationCriteria
from app.models.class_models import Class, ClassMember
from app.models.enterprise_models import Enterprise, EnterpriseMentor, JobPosition, EnterpriseEvaluation

print("=" * 60)
print("阶段 A1 验证报告：模型导入测试")
print("=" * 60)

all_models = [
    ("tables.py - User", User),
    ("tables.py - Task", Task),
    ("tables.py - Submission", Submission),
    ("tables.py - Evaluation", Evaluation),
    ("tables.py - EvaluationCriteria", EvaluationCriteria),
    ("class_models.py - Class", Class),
    ("class_models.py - ClassMember", ClassMember),
    ("enterprise_models.py - Enterprise", Enterprise),
    ("enterprise_models.py - EnterpriseMentor", EnterpriseMentor),
    ("enterprise_models.py - JobPosition", JobPosition),
    ("enterprise_models.py - EnterpriseEvaluation", EnterpriseEvaluation),
]

for name, cls in all_models:
    print(f"  ✓ {name:45s} → 表名: {cls.__tablename__}")

print()

# 检查字段
print("─" * 60)
print("字段检查：")
print("─" * 60)

# 1. users.role 是否有 enterprise
user_role_enum = User.role.type
print(f"  User.role 枚举值: {user_role_enum.enums}")
assert "enterprise" in user_role_enum.enums, "❌ users.role 枚举缺少 enterprise!"
print("  ✓ users.role 包含 'enterprise' 角色 ✅")

# 2. Class.enterprise_id 是否存在
has_enterprise_id = any(c.name == "enterprise_id" for c in Class.__table__.columns)
print(f"  Class 是否有 enterprise_id 字段: {has_enterprise_id}")
assert has_enterprise_id, "❌ Class 缺少 enterprise_id 字段!"
print("  ✓ classes.enterprise_id 外键字段存在 ✅")

# 3. Enterprise 4 张表核心字段
checks = [
    ("enterprises", Enterprise, ["name", "industry", "contact_email", "status"]),
    ("enterprise_mentors", EnterpriseMentor, ["enterprise_id", "user_id", "title", "is_admin"]),
    ("job_positions", JobPosition, ["title", "skill_requirements", "tags", "linked_classes", "status"]),
    ("enterprise_evaluations", EnterpriseEvaluation, ["submission_id", "mentor_id", "enterprise_id",
                                                      "dimension_scores", "job_fit_score", "interview_suggest"]),
]
for tbl, cls, required_cols in checks:
    cols = {c.name for c in cls.__table__.columns}
    missing = [c for c in required_cols if c not in cols]
    if missing:
        print(f"  ❌ {tbl} 缺少字段: {missing}")
        raise AssertionError(f"{tbl} 缺字段")
    print(f"  ✓ {tbl:32s} 核心字段齐全 ✅ ({len(cls.__table__.columns)} 列)")

print()
print("=" * 60)
print("🎉 阶段 A1 全部验证通过！")
print("=" * 60)
print()
print("后续建议：")
print("  1. 如果 MySQL 已运行 eval_system 库，可执行以下命令建表:")
print("     python -c \"from app.models.database import engine, Base;"
      "import app.models.tables, app.models.class_models, app.models.enterprise_models;"
      "Base.metadata.create_all(bind=engine)\"")
print("  2. 用 DESC enterprises; DESC job_positions; 等 SQL 核对字段")
print("  3. 下一阶段：A2（企业端基础 API）或 B1（匹配算法）并行")
