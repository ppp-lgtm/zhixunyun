"""Best-effort MySQL column-add migrations: columns that exist in tables.py but
missing from the live MySQL database (because Base.metadata.create_all never
ALTERs) are added here for each table we know about.

This is NOT a real migration framework - it's a one-shot bootstrap we run on
backend start to bring old DB tables up-to-date with the current model.

Run after run.py's database_create_all() has created any missing *tables*.
"""
from __future__ import annotations

from typing import Iterable

# Desired columns by table - mirror app.models.tables definitions.
# Format: (col_name, sql_col_def, nullable)
_DESIRED_COLS: dict[str, list[tuple[str, str]]] = {
    "submissions": [
        # already present in all versions
        ("id", "INT NOT NULL AUTO_INCREMENT PRIMARY KEY"),
        ("task_id", "INT NULL"),
        ("student_id", "INT NULL"),
        ("filename", "VARCHAR(200) NULL"),
        ("file_path", "VARCHAR(500) NULL"),
        ("content", "TEXT NULL"),
        ("created_at", "DATETIME NULL"),
        ("class_id", "VARCHAR(500) NULL"),
        # added later
        ("step_evidences", "JSON NULL"),
        ("meta", "JSON NULL"),
    ],
    "users": [
        ("id", "INT NOT NULL AUTO_INCREMENT PRIMARY KEY"),
        ("username", "VARCHAR(50) NOT NULL UNIQUE"),
        ("password_hash", "VARCHAR(255) NOT NULL"),
        ("real_name", "VARCHAR(100) NULL"),
        ("email", "VARCHAR(150) NULL"),
        ("phone", "VARCHAR(50) NULL"),
        ("role", "VARCHAR(20) NOT NULL"),
        ("avatar", "VARCHAR(500) NULL"),
        ("user_number", "VARCHAR(50) NULL"),
        ("created_at", "DATETIME NULL"),
        ("extra", "JSON NULL"),
    ],
    "classes": [
        ("id", "INT NOT NULL AUTO_INCREMENT PRIMARY KEY"),
        ("name", "VARCHAR(200) NOT NULL"),
        ("teacher_id", "INT NULL"),
        ("enterprise_id", "INT NULL"),
        ("created_at", "DATETIME NULL"),
        ("description", "TEXT NULL"),
        ("extra", "JSON NULL"),
    ],
    "class_members": [
        ("id", "INT NOT NULL AUTO_INCREMENT PRIMARY KEY"),
        ("class_id", "INT NOT NULL"),
        ("student_id", "INT NOT NULL"),
        ("joined_at", "DATETIME NULL"),
    ],
    "tasks": [
        ("id", "INT NOT NULL AUTO_INCREMENT PRIMARY KEY"),
        ("class_id", "INT NOT NULL"),
        ("title", "VARCHAR(255) NOT NULL"),
        ("requirements", "TEXT NULL"),
        ("created_at", "DATETIME NULL"),
        ("deadline", "DATETIME NULL"),
        ("steps_def", "JSON NULL"),
        ("extra", "JSON NULL"),
        # Enterprise 联动新增
        ("origin", "VARCHAR(30) DEFAULT 'teacher_manual'"),
        ("linked_job_id", "INT NULL"),
        ("is_enterprise_project", "TINYINT(1) DEFAULT 0"),
        ("ai_generated_job_title", "VARCHAR(200) DEFAULT ''"),
    ],
    "evaluations": [
        ("id", "INT NOT NULL AUTO_INCREMENT PRIMARY KEY"),
        ("submission_id", "INT NOT NULL"),
        ("evaluator_id", "INT NULL"),
        ("evaluator_type", "VARCHAR(20) NULL"),
        ("score", "FLOAT NULL"),
        ("content", "TEXT NULL"),
        ("created_at", "DATETIME NULL"),
        ("scores", "JSON NULL"),
        ("meta", "JSON NULL"),
    ],
    "attachments": [
        ("id", "INT NOT NULL AUTO_INCREMENT PRIMARY KEY"),
        ("submission_id", "INT NULL"),
        ("filename", "VARCHAR(255) NOT NULL"),
        ("file_path", "VARCHAR(500) NOT NULL"),
        ("file_type", "VARCHAR(50) NULL"),
        ("size_bytes", "INT NULL"),
        ("created_at", "DATETIME NULL"),
        ("step_index", "INT NULL"),
    ],
    # Enterprise tables: create columns too (if table exists already)
    "enterprises": [
        ("id", "INT NOT NULL AUTO_INCREMENT PRIMARY KEY"),
        ("name", "VARCHAR(255) NOT NULL"),
        ("short_name", "VARCHAR(100) NULL"),
        ("logo", "VARCHAR(500) NULL"),
        ("industry", "VARCHAR(200) NULL"),
        ("scale", "VARCHAR(100) NULL"),
        ("contact_person", "VARCHAR(100) NULL"),
        ("contact_phone", "VARCHAR(50) NULL"),
        ("contact_email", "VARCHAR(200) NULL"),
        ("address", "VARCHAR(500) NULL"),
        ("description", "TEXT NULL"),
        ("created_at", "DATETIME NULL"),
        ("extra", "JSON NULL"),
    ],
    "enterprise_mentors": [
        ("id", "INT NOT NULL AUTO_INCREMENT PRIMARY KEY"),
        ("enterprise_id", "INT NOT NULL"),
        # 注：v3 新主键是 account_id（指向 login_accounts）；
        # user_id 是 v2 遗留兼容列，现在写成与 account_id 同值即可，允许 NULL
        ("user_id", "INT NULL"),
        ("account_id", "INT NOT NULL"),
        ("real_name", "VARCHAR(50) NOT NULL DEFAULT ''"),
        ("title", "VARCHAR(200) NULL"),
        ("department", "VARCHAR(200) NULL"),
        ("is_admin", "TINYINT(1) DEFAULT 0"),
        ("status", "ENUM('active','inactive') DEFAULT 'active'"),
        ("joined_at", "DATETIME NULL"),
        ("extra", "JSON NULL"),
    ],
    "job_positions": [
        ("id", "INT NOT NULL AUTO_INCREMENT PRIMARY KEY"),
        ("enterprise_id", "INT NOT NULL"),
        ("title", "VARCHAR(255) NOT NULL"),
        ("description", "TEXT NULL"),
        ("requirements", "TEXT NULL"),
        ("salary", "VARCHAR(100) NULL"),
        ("location", "VARCHAR(255) NULL"),
        ("class_id", "INT NULL"),
        ("created_at", "DATETIME NULL"),
        # 新字段
        ("ai_generated", "TINYINT(1) DEFAULT 0"),
        ("ai_prompt_snapshot", "TEXT NULL"),
    ],
    "enterprise_evaluations": [
        ("id", "INT NOT NULL AUTO_INCREMENT PRIMARY KEY"),
        ("enterprise_id", "INT NOT NULL"),
        ("submission_id", "INT NOT NULL"),
        ("mentor_id", "INT NULL"),
        ("score", "FLOAT NULL"),
        ("content", "TEXT NULL"),
        ("created_at", "DATETIME NULL"),
        ("scores", "JSON NULL"),
    ],
}

# Optional indices we want present
_DESIRED_INDEXES: dict[str, list[tuple[str, Iterable[str], bool]]] = {
    # (index_name, [columns], unique)
    "submissions": [
        ("idx_sub_task", ("task_id",), False),
        ("idx_sub_student", ("student_id",), False),
        ("idx_sub_class", ("class_id",), False),
    ],
    "users": [
        ("uk_users_username", ("username",), True),
        ("idx_users_role", ("role",), False),
    ],
    "classes": [
        ("idx_classes_teacher", ("teacher_id",), False),
        ("idx_classes_enterprise", ("enterprise_id",), False),
    ],
    "class_members": [
        ("uk_cm_class_student", ("class_id", "student_id"), True),
        ("idx_cm_student", ("student_id",), False),
    ],
    "tasks": [("idx_tasks_class", ("class_id",), False)],
    "evaluations": [
        ("idx_eval_sub", ("submission_id",), False),
        ("idx_eval_eval", ("evaluator_id",), False),
    ],
    "attachments": [("idx_att_sub", ("submission_id",), False)],
    "enterprise_mentors": [
        ("idx_em_user", ("user_id",), False),
        ("idx_em_enterprise", ("enterprise_id",), False),
    ],
    "job_positions": [
        ("idx_jp_enterprise", ("enterprise_id",), False),
        ("idx_jp_class", ("class_id",), False),
    ],
    "enterprise_evaluations": [
        ("idx_ee_enterprise", ("enterprise_id",), False),
        ("idx_ee_sub", ("submission_id",), False),
        ("idx_ee_mentor", ("mentor_id",), False),
    ],
}


def _cols_present(cursor, table: str) -> set[str]:
    try:
        cursor.execute(f"SHOW COLUMNS FROM `{table}`")
    except Exception:
        return set()
    return {row[0] for row in cursor.fetchall()}


def _indexes_present(cursor, table: str) -> set[str]:
    try:
        cursor.execute(f"SHOW INDEX FROM `{table}`")
    except Exception:
        return set()
    return {row[2] for row in cursor.fetchall()}


def _table_exists(cursor, table: str) -> bool:
    try:
        cursor.execute(f"SHOW TABLES LIKE '{table}'")
    except Exception:
        return False
    return cursor.fetchone() is not None


def upgrade(conn, *, dry_run: bool = False) -> tuple[int, int]:
    """Run best-effort ALTERs. Returns (num_cols_added, num_indexes_added)."""
    cursor = conn.cursor()
    added_cols = 0
    added_idx = 0
    for table, cols in _DESIRED_COLS.items():
        if not _table_exists(cursor, table):
            # Base.metadata.create_all might still create it next; skip.
            continue
        present = _cols_present(cursor, table)
        for col_name, col_def in cols:
            if col_name in present:
                continue
            sql = f"ALTER TABLE `{table}` ADD COLUMN `{col_name}` {col_def}"
            if dry_run:
                print(f"[MIGRATION DRY-RUN] {sql};")
            else:
                try:
                    cursor.execute(sql)
                    added_cols += 1
                except Exception as e:  # pragma: no cover
                    # e.g. multiple primary keys - just ignore
                    print(f"[WARN] migration ALTER {table}.{col_name} skipped: {e}")

        # indexes
        ip = _indexes_present(cursor, table)
        for name, cols_it, uniq in _DESIRED_INDEXES.get(table, []):
            if name in ip:
                continue
            cols_csv = ",".join(f"`{c}`" for c in cols_it)
            unique_kw = "UNIQUE" if uniq else ""
            sql = (
                f"ALTER TABLE `{table}` ADD {unique_kw} INDEX `{name}` ({cols_csv})"
                .replace("ADD  INDEX", "ADD INDEX")
            )
            if dry_run:
                print(f"[MIGRATION DRY-RUN] {sql};")
            else:
                try:
                    cursor.execute(sql)
                    added_idx += 1
                except Exception as e:  # pragma: no cover
                    print(f"[WARN] migration INDEX {table}.{name} skipped: {e}")

    if not dry_run:
        try:
            conn.commit()
        except Exception:
            pass
    return added_cols, added_idx


if __name__ == "__main__":
    import os
    import sys

    try:
        from pymysql import connect as pyconnect
    except ImportError as e:
        print("[MIGRATION] pymysql not installed, skip:", e)
        sys.exit(0)

    db_url = os.environ.get("DATABASE_URL") or ""
    # mysql+pymysql://root:root@localhost:3306/eval_system?charset=utf8mb4
    host = "localhost"
    port = 3306
    user = "root"
    password = "root"
    database = "eval_system"
    if db_url.startswith("mysql"):
        try:
            from urllib.parse import urlparse, parse_qs, unquote
            u = urlparse(db_url)
            host = u.hostname or host
            port = u.port or port
            user = unquote(u.username or "") or user
            password = unquote(u.password or "") if u.password else password
            database = u.path.lstrip("/") or database
        except Exception:
            pass

    conn = pyconnect(host=host, port=port, user=user, password=password,
                     database=database, charset="utf8mb4")
    try:
        c, i = upgrade(conn, dry_run=False)
        print(f"[MIGRATION] added columns={c} indexes={i}")
    finally:
        conn.close()
