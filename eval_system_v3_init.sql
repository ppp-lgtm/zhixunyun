/* ========================================================================
   智训云实训评价系统 - 数据库 V3（三角色独立分表 + 关联表版）
   适用场景：全新部署、全新库。
   用法：
     1) mysql -uroot -p < eval_system_v3_init.sql
     2) 或在 Navicat / DBeaver 打开本文件 → 在目标连接上「运行 SQL」
   产物：数据库 eval_system (utf8mb4)，共 15 张表。
   ======================================================================== */

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

/* ---------- 数据库 ---------- */
CREATE DATABASE IF NOT EXISTS `eval_system`
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;
USE `eval_system`;

-- ==============================================================
-- 1) 登录凭据（共享表：teacher / student / mentor 三角色共用登录入口）
-- ==============================================================
DROP TABLE IF EXISTS `login_accounts`;
CREATE TABLE `login_accounts` (
  `id`            INT          NOT NULL AUTO_INCREMENT,
  `username`      VARCHAR(50)  NOT NULL COMMENT '登录用户名，唯一',
  `password_hash` VARCHAR(255) NOT NULL COMMENT '密码哈希',
  `role`          ENUM('teacher','student','mentor') NOT NULL COMMENT 'teacher=教师, student=学生, mentor=企业导师',
  `email`         VARCHAR(100) NOT NULL DEFAULT '',
  `phone`         VARCHAR(30)  NOT NULL DEFAULT '',
  `avatar`        VARCHAR(255) NOT NULL DEFAULT '',
  `status`        ENUM('active','disabled') NOT NULL DEFAULT 'active',
  `extra`         JSON         NULL COMMENT 'last_login_ip、last_login_at、reset_token 等',
  `created_at`    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at`    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE KEY `uk_login_username` (`username`) USING BTREE,
  KEY `idx_login_role`  (`role`)  USING BTREE,
  KEY `idx_login_phone` (`phone`) USING BTREE,
  KEY `idx_login_email` (`email`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='共享登录凭据表（三角色统一入口）';

-- ==============================================================
-- 2) 教师身份
-- ==============================================================
DROP TABLE IF EXISTS `teachers`;
CREATE TABLE `teachers` (
  `id`         INT          NOT NULL AUTO_INCREMENT,
  `account_id` INT          NOT NULL COMMENT '1:1 绑定 login_accounts.id',
  `real_name`  VARCHAR(50)  NOT NULL DEFAULT '',
  `teacher_no` VARCHAR(30)  NULL DEFAULT NULL COMMENT '教师工号；NULL 不参与 UNIQUE，多人未分配也不冲突',
  `title`      VARCHAR(100) NOT NULL DEFAULT '' COMMENT '讲师/副教授 等',
  `department` VARCHAR(100) NOT NULL DEFAULT '' COMMENT '所属学院/部门',
  `status`     ENUM('active','inactive') NOT NULL DEFAULT 'active',
  `joined_at`  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `extra`      JSON         NULL,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE KEY `uk_tea_account` (`account_id`) USING BTREE,
  UNIQUE KEY `uk_tea_no`      (`teacher_no`) USING BTREE COMMENT 'NULL 不违反唯一',
  CONSTRAINT `fk_tea_account` FOREIGN KEY (`account_id`)
    REFERENCES `login_accounts` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='教师身份表';

-- ==============================================================
-- 3) 学生身份
-- ==============================================================
DROP TABLE IF EXISTS `students`;
CREATE TABLE `students` (
  `id`              INT          NOT NULL AUTO_INCREMENT,
  `account_id`      INT          NOT NULL COMMENT '1:1 绑定 login_accounts.id',
  `real_name`       VARCHAR(50)  NOT NULL DEFAULT '',
  `student_no`      VARCHAR(30)  NULL DEFAULT NULL COMMENT '学号；NULL 不参与 UNIQUE，多人未分配也不冲突',
  `grade`           VARCHAR(20)  NOT NULL DEFAULT '' COMMENT '年级',
  `major`           VARCHAR(100) NOT NULL DEFAULT '' COMMENT '专业',
  `class_name`      VARCHAR(100) NOT NULL DEFAULT '' COMMENT '行政班快照，例如 计科2201',
  `enrollment_year` INT          NULL COMMENT '入学年份 2022',
  `status`          ENUM('active','graduated','dropped') NOT NULL DEFAULT 'active',
  `joined_at`       DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `extra`           JSON         NULL,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE KEY `uk_stu_account` (`account_id`) USING BTREE,
  UNIQUE KEY `uk_stu_no`      (`student_no`) USING BTREE COMMENT 'NULL 不违反唯一',
  KEY `idx_stu_grade_major` (`grade`, `major`) USING BTREE,
  CONSTRAINT `fk_stu_account` FOREIGN KEY (`account_id`)
    REFERENCES `login_accounts` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='学生身份表';

-- ==============================================================
-- 4) 企业信息
-- ==============================================================
DROP TABLE IF EXISTS `enterprises`;
CREATE TABLE `enterprises` (
  `id`             INT           NOT NULL AUTO_INCREMENT,
  `name`           VARCHAR(200)  NOT NULL,
  `short_name`     VARCHAR(50)   NOT NULL DEFAULT '',
  `logo`           VARCHAR(500)  NOT NULL DEFAULT '',
  `industry`       VARCHAR(100)  NOT NULL DEFAULT '',
  `scale`          VARCHAR(50)   NOT NULL DEFAULT '' COMMENT '50人以下/50-200/200-1000/1000+',
  `contact_person` VARCHAR(50)   NOT NULL DEFAULT '',
  `contact_phone`  VARCHAR(30)   NOT NULL DEFAULT '',
  `contact_email`  VARCHAR(100)  NOT NULL DEFAULT '',
  `address`        VARCHAR(500)  NOT NULL DEFAULT '',
  `description`    TEXT          NULL COMMENT '企业简介',
  `status`         ENUM('active','inactive') NOT NULL DEFAULT 'active',
  `created_at`     DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `extra`          JSON          NULL,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE KEY `uk_enterprise_name` (`name`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='企业信息表';

-- ==============================================================
-- 5) 企业导师身份（同一 login_account 可以在多家企业挂不同身份）
-- ==============================================================
DROP TABLE IF EXISTS `enterprise_mentors`;
CREATE TABLE `enterprise_mentors` (
  `id`            INT           NOT NULL AUTO_INCREMENT,
  `account_id`    INT           NOT NULL COMMENT 'login_accounts.id',
  `enterprise_id` INT           NOT NULL,
  `real_name`     VARCHAR(50)   NOT NULL DEFAULT '',
  `title`         VARCHAR(100)  NOT NULL DEFAULT '' COMMENT '高级工程师/技术总监/HR 等',
  `department`    VARCHAR(100)  NOT NULL DEFAULT '' COMMENT '所属部门',
  `is_admin`      TINYINT(1)    NOT NULL DEFAULT 0 COMMENT '1=企业管理员；0=普通导师',
  `status`        ENUM('active','inactive') NOT NULL DEFAULT 'active',
  `joined_at`     DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `extra`         JSON          NULL,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE KEY `uk_em_account_enterprise` (`account_id`, `enterprise_id`) USING BTREE,
  KEY `idx_em_enterprise` (`enterprise_id`) USING BTREE,
  CONSTRAINT `fk_em_account`   FOREIGN KEY (`account_id`)
    REFERENCES `login_accounts` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT,
  CONSTRAINT `fk_em_enterprise` FOREIGN KEY (`enterprise_id`)
    REFERENCES `enterprises` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='企业导师身份表（1账号 × 1企业 = 1条身份）';

-- ==============================================================
-- 6) 班级
-- ==============================================================
DROP TABLE IF EXISTS `classes`;
CREATE TABLE `classes` (
  `id`            INT           NOT NULL AUTO_INCREMENT,
  `name`          VARCHAR(100)  NOT NULL,
  `grade`         VARCHAR(20)   NOT NULL DEFAULT '',
  `major`         VARCHAR(100)  NOT NULL DEFAULT '',
  `semester`      VARCHAR(20)   NOT NULL DEFAULT '',
  `course_name`   VARCHAR(100)  NOT NULL DEFAULT '',
  `description`   TEXT          NULL,
  `teacher_id`    INT           NULL COMMENT '班主任（teachers.id）',
  `teacher_name`  VARCHAR(50)   NOT NULL DEFAULT '' COMMENT '冗余快照',
  `enterprise_id` INT           NULL COMMENT '合作企业',
  `invite_code`   VARCHAR(10)   NOT NULL COMMENT '6位邀请码',
  `student_count` INT           NOT NULL DEFAULT 0,
  `status`        ENUM('active','archived') NOT NULL DEFAULT 'active',
  `created_at`    DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `extra`         JSON          NULL,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE KEY `uk_class_invite` (`invite_code`) USING BTREE,
  KEY `idx_class_teacher`    (`teacher_id`)    USING BTREE,
  KEY `idx_class_enterprise` (`enterprise_id`) USING BTREE,
  CONSTRAINT `fk_class_teacher`    FOREIGN KEY (`teacher_id`)
    REFERENCES `teachers` (`id`)       ON DELETE SET NULL ON UPDATE RESTRICT,
  CONSTRAINT `fk_class_enterprise` FOREIGN KEY (`enterprise_id`)
    REFERENCES `enterprises` (`id`)   ON DELETE SET NULL ON UPDATE RESTRICT
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='班级表';

-- ==============================================================
-- 7) 班级成员（学生 × 班级）
-- ==============================================================
DROP TABLE IF EXISTS `class_members`;
CREATE TABLE `class_members` (
  `id`             INT          NOT NULL AUTO_INCREMENT,
  `class_id`       INT          NOT NULL,
  `student_id`     INT          NOT NULL COMMENT 'students.id',
  `student_name`   VARCHAR(50)  NOT NULL DEFAULT '' COMMENT '冗余：学生姓名，列表展示免 join',
  `student_number` VARCHAR(30)  NOT NULL DEFAULT '' COMMENT '冗余：学号，列表展示免 join',
  `joined_at`      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE KEY `uk_cm_class_student` (`class_id`, `student_id`) USING BTREE,
  KEY `idx_cm_student` (`student_id`) USING BTREE,
  CONSTRAINT `fk_cm_class`   FOREIGN KEY (`class_id`)
    REFERENCES `classes`  (`id`) ON DELETE CASCADE ON UPDATE RESTRICT,
  CONSTRAINT `fk_cm_student` FOREIGN KEY (`student_id`)
    REFERENCES `students` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='班级成员表';

-- ==============================================================
-- 8) 企业岗位（企业项目实训来源）
--    注意：job_positions.created_by 直接 FK 到 enterprise_mentors，
--    岗位是"企业导师"创建的，不是 teacher。
-- ==============================================================
DROP TABLE IF EXISTS `job_positions`;
CREATE TABLE `job_positions` (
  `id`                  INT           NOT NULL AUTO_INCREMENT,
  `enterprise_id`       INT           NOT NULL,
  `title`               VARCHAR(200)  NOT NULL,
  `job_type`            VARCHAR(50)   NOT NULL DEFAULT '技术岗',
  `level`               VARCHAR(50)   NOT NULL DEFAULT '初级',
  `salary_range`        VARCHAR(100)  NOT NULL DEFAULT '' COMMENT '薪资范围 8k-12k',
  `city`                VARCHAR(100)  NOT NULL DEFAULT '' COMMENT '工作城市',
  `description`         TEXT          NULL,
  `requirements`        TEXT          NULL,
  `responsibilities`    TEXT          NULL,
  `skill_requirements`  JSON          NULL,
  `tags`                VARCHAR(500)  NOT NULL DEFAULT '',
  `created_by`          INT           NULL COMMENT 'enterprise_mentors.id',
  `status`              ENUM('draft','open','closed') NOT NULL DEFAULT 'open',
  `created_at`          DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at`          DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `ai_generated`        TINYINT(1)    NOT NULL DEFAULT 0,
  `ai_prompt_snapshot`  TEXT          NULL,
  PRIMARY KEY (`id`) USING BTREE,
  KEY `idx_jp_enterprise` (`enterprise_id`) USING BTREE,
  KEY `idx_jp_status`     (`status`)        USING BTREE,
  KEY `idx_jp_creator`    (`created_by`)    USING BTREE,
  CONSTRAINT `fk_jp_enterprise` FOREIGN KEY (`enterprise_id`)
    REFERENCES `enterprises`        (`id`) ON DELETE CASCADE ON UPDATE RESTRICT,
  CONSTRAINT `fk_jp_creator`    FOREIGN KEY (`created_by`)
    REFERENCES `enterprise_mentors` (`id`) ON DELETE SET NULL ON UPDATE RESTRICT
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='企业岗位表';

-- ==============================================================
-- 9) 实训任务（1任务可发布到多班级，由 task_class_ref 完成）
-- ==============================================================
DROP TABLE IF EXISTS `tasks`;
CREATE TABLE `tasks` (
  `id`                     INT           NOT NULL AUTO_INCREMENT,
  `title`                  VARCHAR(200)  NOT NULL,
  `requirements`           TEXT          NULL COMMENT '实训要求',
  `criteria`               VARCHAR(500)  NOT NULL DEFAULT '代码质量,功能完整性,文档规范性,界面设计',
  `criteria_weights`       VARCHAR(500)  NOT NULL DEFAULT '',
  `template_path`          VARCHAR(255)  NULL,
  `status`                 ENUM('draft','published') NOT NULL DEFAULT 'published',
  `created_by`             INT           NULL COMMENT 'teachers.id',
  `total_score`            INT           NOT NULL DEFAULT 100,
  `deadline`               DATETIME      NULL,
  `created_at`             DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `steps`                  JSON          NULL COMMENT '分步实训结构化步骤定义',
  `extra`                  JSON          NULL,
  `origin`                 VARCHAR(30)   NOT NULL DEFAULT 'teacher_manual',
  `linked_job_id`          INT           NULL COMMENT '关联企业岗位 job_positions.id',
  `is_enterprise_project`  TINYINT(1)    NOT NULL DEFAULT 0,
  `ai_generated_job_title` VARCHAR(200)  NOT NULL DEFAULT '',
  PRIMARY KEY (`id`) USING BTREE,
  KEY `idx_tasks_created_by`   (`created_by`)    USING BTREE,
  KEY `idx_tasks_status`       (`status`)        USING BTREE,
  KEY `idx_tasks_linked_job`   (`linked_job_id`) USING BTREE,
  CONSTRAINT `fk_tasks_creator` FOREIGN KEY (`created_by`)
    REFERENCES `teachers`      (`id`) ON DELETE SET NULL ON UPDATE RESTRICT,
  CONSTRAINT `fk_tasks_linked_job` FOREIGN KEY (`linked_job_id`)
    REFERENCES `job_positions` (`id`) ON DELETE SET NULL ON UPDATE RESTRICT
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='实训任务表';

-- ==============================================================
-- 10) 任务↔班级 关联表（拆旧 tasks.class_id 逗号列）
-- ==============================================================
DROP TABLE IF EXISTS `task_class_ref`;
CREATE TABLE `task_class_ref` (
  `task_id`  INT NOT NULL,
  `class_id` INT NOT NULL,
  PRIMARY KEY (`task_id`, `class_id`) USING BTREE,
  KEY `idx_tcr_class` (`class_id`) USING BTREE,
  CONSTRAINT `fk_tcr_task`  FOREIGN KEY (`task_id`)
    REFERENCES `tasks`   (`id`) ON DELETE CASCADE ON UPDATE RESTRICT,
  CONSTRAINT `fk_tcr_class` FOREIGN KEY (`class_id`)
    REFERENCES `classes` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='任务发布到哪些班级（拆旧 tasks.class_id 逗号分隔）';

-- ==============================================================
-- 11) 岗位↔班级 关联表（拆旧 job_positions.linked_classes + class_id）
-- ==============================================================
DROP TABLE IF EXISTS `job_class_ref`;
CREATE TABLE `job_class_ref` (
  `job_id`   INT NOT NULL,
  `class_id` INT NOT NULL,
  PRIMARY KEY (`job_id`, `class_id`) USING BTREE,
  KEY `idx_jcr_class` (`class_id`) USING BTREE,
  CONSTRAINT `fk_jcr_job`   FOREIGN KEY (`job_id`)
    REFERENCES `job_positions` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT,
  CONSTRAINT `fk_jcr_class` FOREIGN KEY (`class_id`)
    REFERENCES `classes`       (`id`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='岗位绑定到哪些班级（拆旧 job_positions.linked_classes）';

-- ==============================================================
-- 12) 评价维度库（挂到任务上）
-- ==============================================================
DROP TABLE IF EXISTS `evaluation_criteria`;
CREATE TABLE `evaluation_criteria` (
  `id`          INT           NOT NULL AUTO_INCREMENT,
  `task_id`     INT           NULL,
  `name`        VARCHAR(100)  NULL,
  `weight`      FLOAT         NOT NULL DEFAULT 25.0,
  `description` TEXT          NULL,
  PRIMARY KEY (`id`) USING BTREE,
  KEY `idx_ec_task` (`task_id`) USING BTREE,
  CONSTRAINT `fk_ec_task` FOREIGN KEY (`task_id`)
    REFERENCES `tasks` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='评价维度标准表';

-- ==============================================================
-- 13) 学生提交记录（DB 层强制：1 学生 × 1 任务 = 1 条）
-- ==============================================================
DROP TABLE IF EXISTS `submissions`;
CREATE TABLE `submissions` (
  `id`             INT          NOT NULL AUTO_INCREMENT,
  `task_id`        INT          NOT NULL,
  `student_id`     INT          NOT NULL COMMENT 'students.id',
  `filename`       VARCHAR(200) NULL,
  `file_path`      VARCHAR(500) NULL,
  `content`        LONGTEXT     NULL COMMENT 'AI 抽取的纯文本（文档长时用 LONGTEXT）',
  `step_evidences` JSON         NULL COMMENT '分步实训的证据按 step_index 对齐',
  `meta`           JSON         NULL COMMENT '提交扩展元数据：sha1、客户端ua、分步index、文件列表',
  `created_at`     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at`     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE KEY `uk_sub_task_student` (`task_id`, `student_id`) USING BTREE,
  KEY `idx_sub_student_created` (`student_id`, `created_at` DESC) USING BTREE,
  CONSTRAINT `fk_sub_task`    FOREIGN KEY (`task_id`)
    REFERENCES `tasks`    (`id`) ON DELETE CASCADE ON UPDATE RESTRICT,
  CONSTRAINT `fk_sub_student` FOREIGN KEY (`student_id`)
    REFERENCES `students` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='学生提交记录表';

-- ==============================================================
-- 14) AI / 教师 评价（1 submission × evaluator_type = 1 条）
--     evaluator_id: AI 则 NULL；teacher 时为 teachers.id
-- ==============================================================
DROP TABLE IF EXISTS `evaluations`;
CREATE TABLE `evaluations` (
  `id`                INT        NOT NULL AUTO_INCREMENT,
  `submission_id`     INT        NOT NULL,
  `evaluator_type`    ENUM('ai','teacher') NOT NULL DEFAULT 'ai',
  `evaluator_id`      INT        NULL COMMENT 'evaluator_type=teacher 时填 teachers.id',
  `total_score`       FLOAT      NULL,
  `dimension_scores`  JSON       NULL,
  `comment`           TEXT       NULL,
  `step_completeness` JSON       NULL,
  `logic_issues`      JSON       NULL,
  `meta`              JSON       NULL COMMENT 'ai_model、评分耗时ms、prompt_tokens 等',
  `created_at`        DATETIME   NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at`        DATETIME   NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE KEY `uk_eval_sub_type` (`submission_id`, `evaluator_type`) USING BTREE,
  KEY `idx_eval_evaluator` (`evaluator_id`) USING BTREE,
  CONSTRAINT `fk_eval_submission` FOREIGN KEY (`submission_id`)
    REFERENCES `submissions` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT,
  CONSTRAINT `fk_eval_evaluator` FOREIGN KEY (`evaluator_id`)
    REFERENCES `teachers`    (`id`) ON DELETE SET NULL ON UPDATE RESTRICT
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='AI + 教师 评价表';

-- ==============================================================
-- 15) 企业评价（1 submission × 1 enterprise = 1 条）
-- ==============================================================
DROP TABLE IF EXISTS `enterprise_evaluations`;
CREATE TABLE `enterprise_evaluations` (
  `id`                  INT                                           NOT NULL AUTO_INCREMENT,
  `submission_id`       INT                                           NOT NULL,
  `mentor_id`           INT                                           NOT NULL COMMENT '企业导师 enterprise_mentors.id',
  `enterprise_id`       INT                                           NOT NULL,
  `total_score`         FLOAT                                         NOT NULL DEFAULT 0,
  `dimension_scores`    JSON                                          NULL,
  `job_fit_score`       FLOAT                                         NOT NULL DEFAULT 0,
  `strength_points`     TEXT                                          NULL,
  `improvement_points`  TEXT                                          NULL,
  `interview_suggest`   ENUM('recommend','maybe','not_recommend')     NOT NULL DEFAULT 'maybe',
  `comment`             TEXT                                          NULL,
  `matched_job_id`      INT                                           NULL,
  `created_at`          DATETIME                                      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at`          DATETIME                                      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE KEY `uk_ee_sub_enterprise` (`submission_id`, `enterprise_id`) USING BTREE,
  KEY `idx_ee_mentor`  (`mentor_id`)       USING BTREE,
  KEY `idx_ee_enterprise` (`enterprise_id`) USING BTREE,
  KEY `idx_ee_job`     (`matched_job_id`)  USING BTREE,
  CONSTRAINT `fk_ee_submission` FOREIGN KEY (`submission_id`)
    REFERENCES `submissions`        (`id`) ON DELETE CASCADE ON UPDATE RESTRICT,
  CONSTRAINT `fk_ee_mentor` FOREIGN KEY (`mentor_id`)
    REFERENCES `enterprise_mentors` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT,
  CONSTRAINT `fk_ee_enterprise` FOREIGN KEY (`enterprise_id`)
    REFERENCES `enterprises`        (`id`) ON DELETE CASCADE ON UPDATE RESTRICT,
  CONSTRAINT `fk_ee_job` FOREIGN KEY (`matched_job_id`)
    REFERENCES `job_positions`      (`id`) ON DELETE SET NULL ON UPDATE RESTRICT
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='企业评价表';

SET FOREIGN_KEY_CHECKS = 1;

/* 执行完毕后，在 MySQL 中执行下面语句验证：
   USE eval_system;
   SHOW TABLES;
   -- 预期 15 张表：
   -- login_accounts / teachers / students / enterprises / enterprise_mentors
   -- classes / class_members / job_positions / tasks / evaluation_criteria
   -- submissions / evaluations / enterprise_evaluations
   -- task_class_ref / job_class_ref
*/
