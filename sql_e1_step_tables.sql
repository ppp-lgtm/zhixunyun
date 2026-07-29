-- ============================================================
-- E1 阶段 SQL：分步实训表改造（MySQL 手动执行）
-- 内容：
--   1) tasks 表新增 steps JSON 列（结构化步骤定义）
--   2) submissions 表新增 step_evidences JSON 列（分步提交证据）
-- 执行前请先备份表，或在 staging 验证
-- ============================================================

-- 1) tasks 加 steps（JSON，可空，默认 NULL 表示按 requirements 文本兜底解析）
ALTER TABLE tasks
    ADD COLUMN steps JSON NULL
    COMMENT 'E1-分步实训：结构化步骤定义 [{"index":1,"title":"步骤1","requirement":"实现登录接口","score_weight":35,"pass_threshold":80}, ...]';

-- 2) submissions 加 step_evidences（JSON，可空）
ALTER TABLE submissions
    ADD COLUMN step_evidences JSON NULL
    COMMENT 'E1-分步实训：分步提交证据 [{"step_index":1,"files":[],"content":"","ai_pass":bool,"ai_score":0-100,"ai_reason":"","images":[]}]';

-- 3) (可选) 想让 tasks.steps 有默认值的话，执行下面一行；否则可跳过。
-- ALTER TABLE tasks ALTER COLUMN steps SET DEFAULT (JSON_ARRAY());
