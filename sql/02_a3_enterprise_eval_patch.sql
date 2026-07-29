-- ============================================================
-- 知训云 · 阶段 A3 数据库 DDL 补丁脚本
-- 说明：A3 企业评价功能 + 三方评分对比 运行前必须执行的补丁
--       （01_enterprise_tables.sql 仅建了基础表，一些列/索引缺失，
--        不补这些会导致接口报 Unknown column / 并发写入重复评价）
-- 使用方式：
--   ① 先在 Navicat/DBeaver 中选中 eval_system 数据库
--   ② 按"【检查➡️ ALTER】成对"的方式逐条执行，不要一次性全选
--   ③ 最后执行末尾【验证SQL】确认
-- 日期：2026-07-29
-- ============================================================

USE eval_system;

-- ============================================================
-- 【第 1 步 · 必执行】users 表补齐 3 个缺失列
--        SQLAlchemy 模型 (app/models/tables.py) 已经定义了这些列，
--        但早期版本的 eval_system.sql 未创建，不补则 A3 所有接口
--        只要访问 User 对象就会抛 "Unknown column 'user_number'"
-- ============================================================

-- 1.1 user_number 列（学号/工号）
-- 【检查 ➊】➡️ 先执行：
--   SHOW COLUMNS FROM users WHERE Field = 'user_number';
--   → 空结果 = 缺失 → 执行下列 ALTER
--   → 有结果 = 已存在 → 跳过
ALTER TABLE users
    ADD COLUMN user_number VARCHAR(30)  NOT NULL DEFAULT ''
        COMMENT '学号/工号' AFTER real_name;

-- 1.2 email 列
-- 【检查 ➋】➡️ 先执行：
--   SHOW COLUMNS FROM users WHERE Field = 'email';
--   → 空结果 = 缺失 → 执行下列 ALTER
ALTER TABLE users
    ADD COLUMN email VARCHAR(100) NOT NULL DEFAULT ''
        COMMENT '邮箱' AFTER user_number;

-- 1.3 avatar 列
-- 【检查 ➌】➡️ 先执行：
--   SHOW COLUMNS FROM users WHERE Field = 'avatar';
--   → 空结果 = 缺失 → 执行下列 ALTER
ALTER TABLE users
    ADD COLUMN avatar VARCHAR(255) NOT NULL DEFAULT ''
        COMMENT '头像 URL' AFTER email;

-- 1.4 phone 列（A3 Profile 里通过 getattr(user,"phone","") 兜底，
--              但建议补上，后续注册/个人中心会用）
-- 【检查 ➍】➡️ 先执行：
--   SHOW COLUMNS FROM users WHERE Field = 'phone';
--   → 空结果 = 缺失 → 执行下列 ALTER
ALTER TABLE users
    ADD COLUMN phone VARCHAR(30) NOT NULL DEFAULT ''
        COMMENT '手机号' AFTER avatar;


-- ============================================================
-- 【第 2 步 · 必执行】enterprise_evaluations 表：
--        联合唯一约束 + JSON 字段类型检查 + updated_at 列
-- ============================================================

-- 2.1 联合唯一索引：防止"同一企业对同一条提交并发写入多条评价"
--     代码层 create_enterprise_evaluation 做了一次先查再插，
--     但 DB 层必须靠 UNIQUE 真正挡住并发重复。
-- 【检查 ➎】➡️ 先执行：
--   SELECT COUNT(*) AS cnt FROM information_schema.STATISTICS
--    WHERE TABLE_SCHEMA = DATABASE()
--      AND TABLE_NAME   = 'enterprise_evaluations'
--      AND INDEX_NAME   = 'uk_ee_sub_enterprise';
--   → cnt = 0 → 执行下列 ALTER
--   → cnt = 1 → 已存在 → 跳过
-- ※ 如果 enterprise_evaluations 里已经存在重复数据（同 submission_id +
--    同 enterprise_id），此语句会报错 "Duplicate entry"，请先手动清理：
--    SELECT submission_id, enterprise_id, COUNT(*) c
--      FROM enterprise_evaluations GROUP BY submission_id, enterprise_id
--     HAVING c > 1;
--    查出重复组后，保留 id 最大的一条，删除其余。
ALTER TABLE enterprise_evaluations
    ADD UNIQUE KEY uk_ee_sub_enterprise (submission_id, enterprise_id);

-- 2.2 修正 dimension_scores 列的默认值
--     01_enterprise_tables.sql 里 dimension_scores 的默认值是 NULL，
--     但 Python 模型 EnterpriseEvaluation.dimension_scores default=list()
--     为避免"代码写空数组 vs DB 返回 NULL"的判断分支不一致，统一改成 JSON 数组
-- 【检查 ➏】➡️ 先执行：
--   SHOW COLUMNS FROM enterprise_evaluations WHERE Field = 'dimension_scores';
--   → 看 Default 是否为 NULL，若是 → 执行下列 ALTER
--   MySQL 8+ 允许 JSON 列加默认，老版本 MySQL 5.7 不支持 JSON DEFAULT，
--   这时请忽略本步，不影响功能（代码里会兜底）
ALTER TABLE enterprise_evaluations
    MODIFY COLUMN dimension_scores JSON
        DEFAULT (JSON_ARRAY())
        COMMENT '各维度分：[{"name":"专业基础","score":90,"reason":"..."}, ...]';

-- 2.3 补 updated_at 列（模型里暂时没加，但 SQL 先补上方便后续查修改时间）
-- 【检查 ➐】➡️ 先执行：
--   SHOW COLUMNS FROM enterprise_evaluations WHERE Field = 'updated_at';
--   → 空结果 → 执行下列 ALTER
ALTER TABLE enterprise_evaluations
    ADD COLUMN updated_at DATETIME
        DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        AFTER created_at;


-- ============================================================
-- 【第 3 步 · 可选 · 强烈建议】查询辅助索引
--        这些索引不影响正确性，只影响 A3 列表接口的响应速度
--        班级 > 10 个 / 提交量 > 1000 条时能明显感知
-- ============================================================

-- 3.1 submissions 表：按 student_id + created_at 倒序，A3 待评价列表高频查询
-- 【检查 ➑】
--   SHOW INDEX FROM submissions WHERE Key_name = 'idx_sub_student_created';
--   → 空结果 → 执行
ALTER TABLE submissions
    ADD INDEX idx_sub_student_created (student_id, created_at DESC);

-- 3.2 evaluations 表：按 submission_id 查 AI+教师评价（A3 详情/三方对比高频）
-- 【检查 ➒】
--   SHOW INDEX FROM evaluations WHERE Key_name = 'idx_eval_sub_type';
--   → 空结果 → 执行
ALTER TABLE evaluations
    ADD INDEX idx_eval_sub_type (submission_id, evaluator_type);

-- 3.3 class_members 表：按 class_id + student_id 双向查（A3 列表/权限校验）
-- 【检查 ➓】
--   SHOW INDEX FROM class_members WHERE Key_name = 'idx_cm_class_student';
--   → 空结果 → 执行
ALTER TABLE class_members
    ADD INDEX idx_cm_class_student (class_id, student_id);


-- ============================================================
-- 【验证 SQL】全部补丁执行完后逐条跑一下确认
-- ============================================================
-- 1. users 列齐全：
--    SHOW COLUMNS FROM users;
--    → 应能看到：user_number、email、avatar、phone 4 列
--
-- 2. enterprise_evaluations 结构：
--    SHOW COLUMNS FROM enterprise_evaluations;
--    → 应能看到：updated_at、dimension_scores Default 不是 NULL (8.0+)
--
-- 3. 唯一约束存在：
--    SHOW INDEX FROM enterprise_evaluations;
--    → 应有 uk_ee_sub_enterprise 且 Non_unique=0
--
-- 4. 重复写入测试（可选，想验证约束生效就执行）：
--    先找一条已有 submission_id + enterprise_id 组合，手动再插一次：
--    INSERT INTO enterprise_evaluations
--      (submission_id, mentor_id, enterprise_id, total_score, dimension_scores,
--       job_fit_score, strength_points, improvement_points, interview_suggest,
--       comment, matched_job_id)
--    VALUES (<已存在的sub_id>, <某导师>, <已存在的ent_id>, 0, '[]',
--            0, '', '', 'maybe', '', NULL);
--    → 应报错 "Duplicate entry ... for key 'uk_ee_sub_enterprise'"
--
-- 5. 行数：
--    SELECT 'users' t, COUNT(*) c FROM users
--    UNION ALL SELECT 'enterprise_evaluations', COUNT(*) FROM enterprise_evaluations
--    UNION ALL SELECT 'submissions', COUNT(*) FROM submissions;
-- ============================================================
