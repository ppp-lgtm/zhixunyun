-- ============================================================
-- 知训云 · P0 紧急修复补丁（eval_system.sql 检查出的 2 个严重问题）
-- 使用方式：
--   ① 选中 eval_system 数据库
--   ② 按"【检查➡️ ALTER】成对"执行，不要一次性全选
--   ③ 先跑 1.x（users列补齐），再跑 2.x（假外键清理 + 防重复数据）
-- 日期：2026-07-29
-- ============================================================

USE eval_system;

-- ============================================================
-- 【第 1 步 · 必跑】users 表：phone 列补齐 + 可空性对齐
-- （tables.py User 模型与 eval_system.sql 列对齐）
-- ============================================================

-- 1.1 补 phone 列（User 模型已新增，A3 Profile getattr 但模型未定义导致 AttributeError）
-- 【检查 ➊】➡️  先执行：
--   SHOW COLUMNS FROM users WHERE Field = 'phone';
--   → 空结果 / 不存在 = 缺失 → 执行 ALTER
ALTER TABLE users
    ADD COLUMN phone VARCHAR(30) NOT NULL DEFAULT ''
        COMMENT '手机号' AFTER avatar;

-- 1.2  username / password_hash 设为 NOT NULL（防止裸SQL插入脏数据）
-- 【检查 ➋】➡️  先执行：
--   SHOW COLUMNS FROM users WHERE Field = 'username';
--   → 若 Null 列显示 YES → 执行
--   ※ 如果已有 username=NULL 的行，先清脏数据：DELETE FROM users WHERE username IS NULL;
ALTER TABLE users
    MODIFY COLUMN username VARCHAR(50) NOT NULL COMMENT '登录用户名，唯一';

-- 【检查 ➌】➡️  同理查 password_hash 的 Null 是否为 YES
--   SHOW COLUMNS FROM users WHERE Field = 'password_hash';
--   → 若 Null=YES → 执行
--   ※ 先清脏数据：DELETE FROM users WHERE password_hash IS NULL;
ALTER TABLE users
    MODIFY COLUMN password_hash VARCHAR(255) NOT NULL COMMENT '密码哈希值（SHA256+盐）';

-- 1.3  user_number / email / avatar  默认值由 NULL → 空串（与SQLAlchemy模型 default="" 对齐）
-- 【检查 ➍】➡️  先看 user_number 的 Default：
--   SHOW COLUMNS FROM users WHERE Field = 'user_number';
--   → Default 为 NULL 才执行
ALTER TABLE users
    MODIFY COLUMN user_number VARCHAR(30) NOT NULL DEFAULT ''
        COMMENT '学号（学生）/ 工号（教师）';

ALTER TABLE users
    MODIFY COLUMN email VARCHAR(100) NOT NULL DEFAULT ''
        COMMENT '电子邮箱';

ALTER TABLE users
    MODIFY COLUMN avatar VARCHAR(255) NOT NULL DEFAULT ''
        COMMENT '头像文件路径';

-- 1.4  created_at 默认当前时间（防止裸 INSERT 拿不到时间）
-- 【检查 ➎】➡️  SHOW COLUMNS FROM users WHERE Field = 'created_at';
--   → Default 是 NULL 才执行
ALTER TABLE users
    MODIFY COLUMN created_at DATETIME NULL DEFAULT CURRENT_TIMESTAMP
        COMMENT '注册时间';


-- ============================================================
-- 【  第  2  步  ·  必须执行  ·  清理  Task / Submission 的
--       假  外  键  （  VARCHAR↔INT  类型不匹配，MySQL 初始化会 ERROR 1215）
--  同时为 tasks / submissions / class_members 补 A3 性能索引
-- ============================================================

-- ──────────────────────────────────────────────────────────
-- 2.1  tasks 表：如果存在 tasks_ibfk_2 / fk_tasks_class 这类"class_id 外键"，必须先 DROP
--     （假外键：tasks.class_id VARCHAR(500) → classes.id INT，类型不匹配）
-- ──────────────────────────────────────────────────────────
-- 【检查 ➏】➡️  先查：
--   SELECT CONSTRAINT_NAME FROM information_schema.TABLE_CONSTRAINTS
--    WHERE CONSTRAINT_SCHEMA = DATABASE()
--      AND TABLE_NAME = 'tasks'
--      AND CONSTRAINT_NAME != 'PRIMARY'
--      AND CONSTRAINT_NAME != 'tasks_ibfk_1';
--   → 空结果 = 没有假外键，跳过 DROP
--   → 有结果（如 'tasks_ibfk_2'/'fk_tasks_class' 等）= 对每个名字执行 DROP：
--      ALTER TABLE tasks DROP FOREIGN KEY tasks_ibfk_2;
--      ALTER TABLE tasks DROP FOREIGN KEY fk_tasks_class;
-- （下面是示例模板，把 <NAME> 替换为你查到的 CONSTRAINT_NAME）
-- ALTER TABLE tasks DROP FOREIGN KEY <NAME>;

-- 2.2  submissions 表：同上，清除 submissions.class_id 上可能存在的假外键
-- 【检查 ➐】➡️  先查：
--   SELECT CONSTRAINT_NAME FROM information_schema.TABLE_CONSTRAINTS
--    WHERE CONSTRAINT_SCHEMA = DATABASE()
--      AND TABLE_NAME = 'submissions'
--      AND CONSTRAINT_NAME NOT IN ('PRIMARY', 'submissions_ibfk_1', 'submissions_ibfk_2');
--   → 有结果就 DROP，否则跳过
-- ALTER TABLE submissions DROP FOREIGN KEY <NAME>;

-- 2.3  清理 submissions 表上 class_id 前缀的无效索引（VARCHAR(500)建完整INDEX意义不大）
-- 【检查 ➑】➡️  查：
--   SHOW INDEX FROM submissions WHERE Key_name = 'class_id';
--   → 有结果才执行
ALTER TABLE submissions
    DROP INDEX class_id;

-- 2.4  清理 tasks 表上 class_id 前缀的无效索引（同上）
-- 【检查 ➒】➡️  查：
--   SHOW INDEX FROM tasks WHERE Key_name = 'class_id';
--   → 有结果才执行
ALTER TABLE tasks
    DROP INDEX class_id;

-- 2.5  提交表性能索引（A3 待评价列表高频）
-- 【检查 ➓】➡️  SHOW INDEX FROM submissions WHERE Key_name = 'idx_sub_student_created';
--   → 空结果才执行
ALTER TABLE submissions
    ADD INDEX idx_sub_student_created (student_id, created_at DESC);

-- 2.6  评价表性能索引（A3 详情/三方对比高频）
-- 【检查 ⓫】➡️  SHOW INDEX FROM evaluations WHERE Key_name = 'idx_eval_sub_type';
--   → 空结果才执行
ALTER TABLE evaluations
    ADD INDEX idx_eval_sub_type (submission_id, evaluator_type);

-- 2.7  班级成员性能索引（A3 班级可见范围/权限校验高频）
-- 【检查 ⓬】➡️  SHOW INDEX FROM class_members WHERE Key_name = 'idx_cm_class_student';
--   → 空结果才执行
ALTER TABLE class_members
    ADD INDEX idx_cm_class_student (class_id, student_id);


-- ============================================================
-- 【第  3  步  可选 ·  旧数据清理：users.user_number / email / avatar
--     NULL 回写为空串，避免后续 NULL vs "" 分支判断错乱】
-- ============================================================
--   UPDATE users SET user_number = '' WHERE user_number IS NULL;
--   UPDATE users SET email       = '' WHERE email       IS NULL;
--   UPDATE users SET avatar      = '' WHERE avatar      IS NULL;
--   -- 建议提交完之后再跑：
--   OPTIMIZE TABLE users, submissions, tasks, evaluations, enterprise_evaluations;


-- ============================================================
-- 【验证 SQL】补丁执行完后对照检查
-- ============================================================
-- 1. users 10 列齐全：
--    SHOW COLUMNS FROM users;
--    → 按顺序应看到：id, username, password_hash, role, real_name,
--      user_number, created_at, email, avatar, phone
--    → Null：username/password_hash/role/user_number/email/avatar/phone 全部是 NO
--
-- 2. tasks 假外键已清：
--    SELECT CONSTRAINT_NAME FROM information_schema.TABLE_CONSTRAINTS
--     WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'tasks';
--    → 只应看到 PRIMARY / tasks_ibfk_1（指向 users.id）
--
-- 3. submissions 假外键已清：
--    SELECT CONSTRAINT_NAME FROM information_schema.TABLE_CONSTRAINTS
--     WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'submissions';
--    → 只应看到 PRIMARY / submissions_ibfk_1（tasks.id）/ submissions_ibfk_2（users.id）
--
-- 4. 新索引已建立：
--    SHOW INDEX FROM submissions WHERE Key_name = 'idx_sub_student_created';
--    SHOW INDEX FROM evaluations WHERE Key_name = 'idx_eval_sub_type';
--    SHOW INDEX FROM class_members WHERE Key_name = 'idx_cm_class_student';
--    → 三个查询都应有记录
-- ============================================================
