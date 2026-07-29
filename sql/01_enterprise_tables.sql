-- ============================================================
-- 知训云 · 阶段 A1 数据库 DDL 脚本
-- 说明：4 张企业端新表 + 2 处旧表字段修改
-- 使用方式：在 MySQL 客户端 (Navicat / DBeaver / mysql CLI)
--          选中 eval_system 数据库，全选执行即可
-- 日期：2026-07-28
-- ============================================================

USE eval_system;

-- -----------------------------------------------------------
-- 【第 1 步】新建 4 张企业端表
-- -----------------------------------------------------------

-- 1.1 企业信息表 enterprises
CREATE TABLE IF NOT EXISTS enterprises (
    id               INT PRIMARY KEY AUTO_INCREMENT,
    name             VARCHAR(200)  NOT NULL UNIQUE COMMENT '企业全称',
    short_name       VARCHAR(50)   DEFAULT '' COMMENT '企业简称',
    logo             VARCHAR(500)  DEFAULT '' COMMENT 'Logo URL',
    industry         VARCHAR(100)  DEFAULT '' COMMENT '所属行业',
    scale            VARCHAR(50)   DEFAULT '' COMMENT '企业规模：50人以下/50-200/200-1000/1000+',
    contact_person   VARCHAR(50)   DEFAULT '' COMMENT '联系人',
    contact_phone    VARCHAR(30)   DEFAULT '' COMMENT '联系电话',
    contact_email    VARCHAR(100)  DEFAULT '' COMMENT '联系邮箱',
    address          VARCHAR(500)  DEFAULT '' COMMENT '地址',
    description      TEXT          COMMENT '企业简介',
    status           ENUM('active', 'inactive') DEFAULT 'active' COMMENT '状态',
    created_at       DATETIME      DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='企业信息表';


-- 1.2 企业导师关联表 enterprise_mentors
CREATE TABLE IF NOT EXISTS enterprise_mentors (
    id             INT PRIMARY KEY AUTO_INCREMENT,
    enterprise_id  INT  NOT NULL COMMENT '关联企业ID',
    user_id        INT  NOT NULL COMMENT '关联用户ID（users表 role=enterprise）',
    real_name      VARCHAR(50)  DEFAULT '' COMMENT '冗余：导师真实姓名',
    title          VARCHAR(100) DEFAULT '' COMMENT '职位：高级工程师/技术总监/HR 等',
    department     VARCHAR(100) DEFAULT '' COMMENT '所属部门',
    is_admin       INT          DEFAULT 0 COMMENT '1=企业管理员，0=普通导师',
    status         ENUM('active', 'inactive') DEFAULT 'active',
    joined_at      DATETIME     DEFAULT CURRENT_TIMESTAMP,
    KEY idx_enterprise (enterprise_id),
    KEY idx_user (user_id),
    CONSTRAINT fk_em_enterprise FOREIGN KEY (enterprise_id) REFERENCES enterprises(id) ON DELETE CASCADE,
    CONSTRAINT fk_em_user       FOREIGN KEY (user_id)       REFERENCES users(id)       ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='企业导师关联表';


-- 1.3 岗位技能要求表 job_positions
CREATE TABLE IF NOT EXISTS job_positions (
    id                 INT PRIMARY KEY AUTO_INCREMENT,
    enterprise_id      INT  NOT NULL COMMENT '所属企业ID',
    title              VARCHAR(200) NOT NULL COMMENT '岗位名称：前端开发工程师/Python后端等',
    job_type           VARCHAR(50)  DEFAULT '技术岗' COMMENT '岗位类型：技术岗/产品岗/设计岗/测试岗',
    level              VARCHAR(50)  DEFAULT '初级' COMMENT '级别：实习/初级/中级/高级',
    salary_range       VARCHAR(100) DEFAULT '' COMMENT '薪资范围：8k-12k',
    city               VARCHAR(100) DEFAULT '' COMMENT '工作城市',
    description        TEXT         COMMENT '岗位描述',
    requirements       TEXT         COMMENT '任职要求（长文本）',
    responsibilities   TEXT         COMMENT '岗位职责（长文本）',
    skill_requirements JSON         COMMENT '技能要求：[{name,weight,threshold},...]',
    tags               VARCHAR(500) DEFAULT '' COMMENT '标签，逗号分隔：Vue3,Python,FastAPI...',
    linked_classes     VARCHAR(500) DEFAULT '' COMMENT '绑定的班级ID，逗号分隔：1,3,5',
    created_by         INT          COMMENT '创建者用户ID',
    status             ENUM('draft', 'open', 'closed') DEFAULT 'open',
    created_at         DATETIME     DEFAULT CURRENT_TIMESTAMP,
    updated_at         DATETIME     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    KEY idx_enterprise (enterprise_id),
    KEY idx_status (status),
    CONSTRAINT fk_jp_enterprise FOREIGN KEY (enterprise_id) REFERENCES enterprises(id) ON DELETE CASCADE,
    CONSTRAINT fk_jp_creator    FOREIGN KEY (created_by)    REFERENCES users(id)       ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='岗位技能要求表';


-- 1.4 企业评价表 enterprise_evaluations
CREATE TABLE IF NOT EXISTS enterprise_evaluations (
    id                  INT PRIMARY KEY AUTO_INCREMENT,
    submission_id       INT NOT NULL COMMENT '关联 submissions.id',
    mentor_id           INT NOT NULL COMMENT '企业导师 users.id',
    enterprise_id       INT NOT NULL COMMENT '所属企业 enterprises.id',
    total_score         FLOAT       DEFAULT 0 COMMENT '企业评价总分',
    dimension_scores    JSON        COMMENT '各维度分：[{"name":"专业基础","score":90,"reason":"扎实"}, ...]（JSON数组，不是对象！）',
    job_fit_score       FLOAT       DEFAULT 0 COMMENT '岗位适配度 0-100',
    strength_points     TEXT        COMMENT '学生亮点（企业视角）',
    improvement_points  TEXT        COMMENT '待提升点',
    interview_suggest   ENUM('recommend', 'maybe', 'not_recommend') DEFAULT 'maybe' COMMENT '面试建议',
    comment             TEXT        COMMENT '综合评语',
    matched_job_id      INT         NULL COMMENT '匹配的岗位ID',
    created_at          DATETIME    DEFAULT CURRENT_TIMESTAMP,
    KEY idx_submission (submission_id),
    KEY idx_mentor (mentor_id),
    KEY idx_enterprise (enterprise_id),
    KEY idx_job (matched_job_id),
    CONSTRAINT fk_ee_submission FOREIGN KEY (submission_id)  REFERENCES submissions(id) ON DELETE CASCADE,
    CONSTRAINT fk_ee_mentor     FOREIGN KEY (mentor_id)      REFERENCES users(id)       ON DELETE CASCADE,
    CONSTRAINT fk_ee_enterprise FOREIGN KEY (enterprise_id)  REFERENCES enterprises(id) ON DELETE CASCADE,
    CONSTRAINT fk_ee_job        FOREIGN KEY (matched_job_id) REFERENCES job_positions(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='企业评价表';


-- ============================================================
-- 【第 2 步】修改旧表（3 条检查 + 3 条 ALTER，分步执行）
--   ⚠️  重要：不要一次复制全部！
--   请先执行下面带 ➡️ 的【检查 SQL】，再根据结果决定是否执行对应【ALTER SQL】
-- ============================================================

-- ──────────────────────────────────────────────────────────
-- 2.1 users.role 枚举新增 'enterprise'
-- ──────────────────────────────────────────────────────────
-- 【检查 ➊】➡️ 先执行这条看 role 的枚举值：
--   SHOW COLUMNS FROM users WHERE Field = 'role';
--   → 如果 Type 里已经包含 'enterprise'，跳过 2.1 的 ALTER
--   → 如果没有，执行下面这条：
ALTER TABLE users
    MODIFY COLUMN role ENUM('teacher', 'student', 'enterprise')
        NOT NULL DEFAULT 'student'
        COMMENT '用户角色：教师/学生/企业导师';


-- ──────────────────────────────────────────────────────────
-- 2.2 classes 表新增 enterprise_id 列（可空）
-- ──────────────────────────────────────────────────────────
-- 【检查 ➋】➡️ 先执行这条看 classes 是否已经有 enterprise_id：
--   SHOW COLUMNS FROM classes WHERE Field = 'enterprise_id';
--   → 有结果 = 列已存在，跳过 2.2 ALTER
--   → 空结果 = 列不存在，执行下面这条：
ALTER TABLE classes
    ADD COLUMN enterprise_id INT NULL COMMENT '合作企业ID' AFTER teacher_name;


-- ──────────────────────────────────────────────────────────
-- 2.3 classes.enterprise_id 外键约束（指向 enterprises.id）
-- ──────────────────────────────────────────────────────────
-- 【检查 ➌】➡️ 先执行这条看外键是否已存在：
--   SELECT COUNT(*) AS cnt FROM information_schema.TABLE_CONSTRAINTS
--    WHERE CONSTRAINT_SCHEMA = DATABASE()
--      AND CONSTRAINT_NAME   = 'fk_classes_enterprise'
--      AND TABLE_NAME        = 'classes';
--   → cnt = 1 → 外键已存在跳过
--   → cnt = 0 → 执行下面这条
--   ※  如果 classes 表已有数据且 enterprise_id 里填了不存在的企业 ID，
--      下面语句会报错！先把 enterprise_id 全设为 NULL 再加外键：
--      UPDATE classes SET enterprise_id = NULL;
ALTER TABLE classes
    ADD CONSTRAINT fk_classes_enterprise
        FOREIGN KEY (enterprise_id)
        REFERENCES enterprises(id)
        ON DELETE SET NULL;


-- -----------------------------------------------------------
-- 【可选第 3 步】插入演示数据（想直接看效果就执行本段）
--   - 企业账号：longke / 密码：123456（密码用 bcrypt 哈希，
--     下面语句直接用 app/utils/auth.py 相同算法的 hash 值写入）
-- -----------------------------------------------------------
-- 建议先不要执行，后续阶段 A2 完成后再配合业务数据插入。

-- ============================================================
-- 执行完以上 SQL 后，用以下语句验证：
--   SHOW TABLES;
--   DESC enterprises;
--   DESC job_positions;
--   DESC enterprise_evaluations;
--   DESC users;            -- 确认 role 枚举含 enterprise
--   DESC classes;          -- 确认出现 enterprise_id 列
-- ============================================================
