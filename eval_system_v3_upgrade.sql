/* ========================================================================
   智训云实训评价系统 - 存量库 V3 幂等升级脚本（三角色分表 + 关联表 + 关键约束）
   适用场景：数据库 eval_system 已存在，数据来自老版 eval_system.sql。
   安全策略：
     - 全部加/删表、加/删列、加/删索引 都用 information_schema 判断，重复执行不会报错；
     - 只做"新增 / 补齐"，不自动 DROP 旧 users 表，不 DROP 遗留列（怕删错线上数据）；
     - 所有旧列/旧表（如 users、tasks.class_id、submissions.class_id 等）清理，单独写在脚本末尾
       "V3_CLEANUP.md 对应的 DDL"，你确认无误后手动执行。
   用法：
     1) 先备份：mysqldump -uroot -p eval_system > eval_system_before_v3.sql
     2) mysql -uroot -p eval_system < eval_system_v3_upgrade.sql
     3) 看末尾 SELECT 的 summary 确认"本脚本做了哪些变更"
   ======================================================================== */

USE `eval_system`;
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

/* 日志表：记录本次升级做了什么（方便回溯） */
DROP TABLE IF EXISTS `_v3_upgrade_log`;
CREATE TABLE `_v3_upgrade_log` (
  `id`      INT AUTO_INCREMENT PRIMARY KEY,
  `step`    VARCHAR(120) NOT NULL,
  `action`  VARCHAR(200) NOT NULL,
  `done_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

DELIMITER //

/* -------------------------------------------------------------
   工具：执行一段动态 SQL；无预处理语句时用这个做 "DDL IF NOT EXISTS"
   ------------------------------------------------------------- */
DROP PROCEDURE IF EXISTS `_v3_exec` //
CREATE PROCEDURE `_v3_exec`(IN p_step VARCHAR(120), IN p_sql TEXT)
BEGIN
  INSERT INTO `_v3_upgrade_log`(`step`,`action`) VALUES (p_step, LEFT(p_sql,200));
  SET @v = p_sql;
  PREPARE stmt FROM @v; EXECUTE stmt; DEALLOCATE PREPARE stmt;
END //

/* -------------------------------------------------------------
   工具：表存在？
   ------------------------------------------------------------- */
DROP FUNCTION IF EXISTS `_v3_has_table` //
CREATE FUNCTION `_v3_has_table`(p_tbl VARCHAR(128)) RETURNS TINYINT(1)
BEGIN
  RETURN EXISTS(
    SELECT 1 FROM information_schema.TABLES
     WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = p_tbl
  );
END //

/* -------------------------------------------------------------
   工具：某列存在？
   ------------------------------------------------------------- */
DROP FUNCTION IF EXISTS `_v3_has_col` //
CREATE FUNCTION `_v3_has_col`(p_tbl VARCHAR(128), p_col VARCHAR(128)) RETURNS TINYINT(1)
BEGIN
  RETURN EXISTS(
    SELECT 1 FROM information_schema.COLUMNS
     WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = p_tbl AND COLUMN_NAME = p_col
  );
END //

/* -------------------------------------------------------------
   工具：某索引存在？（UNIQUE 或 普通，忽略 primary）
   ------------------------------------------------------------- */
DROP FUNCTION IF EXISTS `_v3_has_idx` //
CREATE FUNCTION `_v3_has_idx`(p_tbl VARCHAR(128), p_idx VARCHAR(128)) RETURNS TINYINT(1)
BEGIN
  RETURN EXISTS(
    SELECT 1 FROM information_schema.STATISTICS
     WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = p_tbl AND INDEX_NAME = p_idx
  );
END //

/* -------------------------------------------------------------
   工具：外键存在？
   ------------------------------------------------------------- */
DROP FUNCTION IF EXISTS `_v3_has_fk` //
CREATE FUNCTION `_v3_has_fk`(p_tbl VARCHAR(128), p_fk VARCHAR(128)) RETURNS TINYINT(1)
BEGIN
  RETURN EXISTS(
    SELECT 1 FROM information_schema.TABLE_CONSTRAINTS
     WHERE CONSTRAINT_SCHEMA = DATABASE()
       AND TABLE_NAME = p_tbl AND CONSTRAINT_NAME = p_fk
       AND CONSTRAINT_TYPE = 'FOREIGN KEY'
  );
END //

/* -------------------------------------------------------------
   工具：动态删除某张表上所有（或指定列前缀的）外键
   用法：CALL _v3_drop_fks_for('submissions','task_id')  删除 submissions 上引用 task_id 的所有 FK
   用法：CALL _v3_drop_fks_for('submissions',NULL)       删除 submissions 上的所有 FK
   ------------------------------------------------------------- */
DROP PROCEDURE IF EXISTS `_v3_drop_fks_for` //
CREATE PROCEDURE `_v3_drop_fks_for`(IN p_tbl VARCHAR(128), IN p_col_prefix VARCHAR(128))
BEGIN
  DECLARE done INT DEFAULT 0;
  DECLARE fk_name VARCHAR(128);
  DECLARE cur CURSOR FOR
    SELECT c.CONSTRAINT_NAME
    FROM information_schema.TABLE_CONSTRAINTS c
    JOIN information_schema.KEY_COLUMN_USAGE  k
      ON c.CONSTRAINT_SCHEMA = k.CONSTRAINT_SCHEMA
     AND c.CONSTRAINT_NAME   = k.CONSTRAINT_NAME
     AND c.TABLE_NAME        = k.TABLE_NAME
   WHERE c.CONSTRAINT_SCHEMA = DATABASE()
     AND c.TABLE_NAME        = p_tbl
     AND c.CONSTRAINT_TYPE   = 'FOREIGN KEY'
     AND (p_col_prefix IS NULL OR k.COLUMN_NAME LIKE CONCAT(p_col_prefix,'%'));
  DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = 1;
  OPEN cur;
  read_loop: LOOP
    FETCH cur INTO fk_name;
    IF done = 1 THEN LEAVE read_loop; END IF;
    SET @ddl = CONCAT('ALTER TABLE `', p_tbl, '` DROP FOREIGN KEY `', fk_name, '`');
    INSERT INTO `_v3_upgrade_log`(`step`,`action`) VALUES (CONCAT('DROP FK ',p_tbl,'.',fk_name), LEFT(@ddl,200));
    PREPARE stmt FROM @ddl; EXECUTE stmt; DEALLOCATE PREPARE stmt;
  END LOOP;
  CLOSE cur;
END //

DELIMITER ;

/* =============================================================
   1) 新建：登录凭据共享表 login_accounts
   ============================================================= */
CALL `_v3_exec`('login_accounts 建表',
  IF(`_v3_has_table`('login_accounts') = 0,
    'CREATE TABLE `login_accounts` (
      `id`            INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
      `username`      VARCHAR(50)  NOT NULL,
      `password_hash` VARCHAR(255) NOT NULL,
      `role`          ENUM(''teacher'',''student'',''mentor'') NOT NULL,
      `email`         VARCHAR(100) NOT NULL DEFAULT '''',
      `phone`         VARCHAR(30)  NOT NULL DEFAULT '''',
      `avatar`        VARCHAR(255) NOT NULL DEFAULT '''',
      `status`        ENUM(''active'',''disabled'') NOT NULL DEFAULT ''active'',
      `extra`         JSON NULL,
      `created_at`    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
      `updated_at`    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
      UNIQUE KEY `uk_login_username` (`username`),
      KEY `idx_login_role`  (`role`),
      KEY `idx_login_phone` (`phone`),
      KEY `idx_login_email` (`email`)
     ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
     COMMENT=''共享登录凭据表（三角色统一登录入口）''',
    'SELECT ''SKIP login_accounts already exists'''
  )
);

/* 回填 login_accounts：从老 users 表迁移（users 表存在才执行） */
CALL `_v3_exec`('login_accounts 回填 users 数据',
  IF(`_v3_has_table`('users') = 1 AND
     (SELECT COUNT(*) FROM `login_accounts`) = 0,
    'INSERT INTO `login_accounts`
        (`id`,`username`,`password_hash`,`role`,`email`,`phone`,`avatar`,`status`,`created_at`,`extra`)
     SELECT
        u.id, u.username, u.password_hash,
        CASE u.role
          WHEN ''teacher''    THEN ''teacher''
          WHEN ''student''    THEN ''student''
          WHEN ''enterprise'' THEN ''mentor''
          ELSE ''student''
        END AS role,
        COALESCE(u.email,''''), COALESCE(u.phone,''''), COALESCE(u.avatar,''''),
        ''active'', COALESCE(u.created_at,NOW()), u.extra
     FROM `users` u',
    'SELECT ''SKIP login_accounts 回填：users 不存在或已回填过'''
  )
);

/* =============================================================
   2) 新建 teachers 并回填
   ============================================================= */
CALL `_v3_exec`('teachers 建表',
  IF(`_v3_has_table`('teachers') = 0,
    'CREATE TABLE `teachers` (
      `id`         INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
      `account_id` INT NOT NULL,
      `real_name`  VARCHAR(50)  NOT NULL DEFAULT '''',
      `teacher_no` VARCHAR(30)  NULL DEFAULT NULL COMMENT ''NULL 不参与 UNIQUE'',
      `title`      VARCHAR(100) NOT NULL DEFAULT '''',
      `department` VARCHAR(100) NOT NULL DEFAULT '''',
      `status`     ENUM(''active'',''inactive'') NOT NULL DEFAULT ''active'',
      `joined_at`  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
      `extra`      JSON NULL,
      UNIQUE KEY `uk_tea_account` (`account_id`),
      UNIQUE KEY `uk_tea_no`      (`teacher_no`),
      CONSTRAINT `fk_tea_account` FOREIGN KEY (`account_id`)
        REFERENCES `login_accounts`(`id`) ON DELETE CASCADE ON UPDATE RESTRICT
     ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci',
    'SELECT ''SKIP teachers already exists'''
  )
);

CALL `_v3_exec`('teachers 回填（老 users.role=teacher）',
  IF(`_v3_has_table`('users') = 1 AND `_v3_has_table`('teachers') = 1 AND
     (SELECT COUNT(*) FROM `teachers`) = 0,
    'INSERT INTO `teachers`(`account_id`,`real_name`,`teacher_no`,`joined_at`)
     SELECT u.id, COALESCE(u.real_name,''''),
            NULLIF(TRIM(COALESCE(u.user_number,'''')),''''), NOW()
     FROM `users` u WHERE u.role = ''teacher''',
    'SELECT '''''
  )
);
/* teachers 已存在的旧行：列可能还是 NOT NULL DEFAULT '' -> 改 NULL + 把空串转 NULL */
CALL `_v3_exec`('teachers.teacher_no 改 NULLABLE（幂等）',
  IF(`_v3_has_table`('teachers') = 1 AND `_v3_has_col`('teachers','teacher_no') = 1,
    'ALTER TABLE `teachers` MODIFY COLUMN `teacher_no` VARCHAR(30) NULL DEFAULT NULL',
    'SELECT '''''
  )
);
CALL `_v3_exec`('teachers 空串 teacher_no 统一转 NULL（避免 UNIQUE 冲突）',
  IF(`_v3_has_table`('teachers') = 1 AND `_v3_has_col`('teachers','teacher_no') = 1,
    'UPDATE `teachers` SET `teacher_no` = NULL WHERE `teacher_no` = ''''',
    'SELECT '''''
  )
);

/* =============================================================
   3) 新建 students 并回填
   ============================================================= */
CALL `_v3_exec`('students 建表',
  IF(`_v3_has_table`('students') = 0,
    'CREATE TABLE `students` (
      `id`              INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
      `account_id`      INT NOT NULL,
      `real_name`       VARCHAR(50)  NOT NULL DEFAULT '''',
      `student_no`      VARCHAR(30)  NULL DEFAULT NULL COMMENT ''NULL 不参与 UNIQUE'',
      `grade`           VARCHAR(20)  NOT NULL DEFAULT '''',
      `major`           VARCHAR(100) NOT NULL DEFAULT '''',
      `class_name`      VARCHAR(100) NOT NULL DEFAULT '''',
      `enrollment_year` INT NULL,
      `status`          ENUM(''active'',''graduated'',''dropped'') NOT NULL DEFAULT ''active'',
      `joined_at`       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
      `extra`           JSON NULL,
      UNIQUE KEY `uk_stu_account` (`account_id`),
      UNIQUE KEY `uk_stu_no`      (`student_no`),
      KEY `idx_stu_grade_major` (`grade`,`major`),
      CONSTRAINT `fk_stu_account` FOREIGN KEY (`account_id`)
        REFERENCES `login_accounts`(`id`) ON DELETE CASCADE ON UPDATE RESTRICT
     ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci',
    'SELECT '''''
  )
);

CALL `_v3_exec`('students 回填（老 users.role=student）',
  IF(`_v3_has_table`('users') = 1 AND `_v3_has_table`('students') = 1 AND
     (SELECT COUNT(*) FROM `students`) = 0,
    'INSERT INTO `students`(`account_id`,`real_name`,`student_no`,`joined_at`)
     SELECT u.id, COALESCE(u.real_name,''''),
            NULLIF(TRIM(COALESCE(u.user_number,'''')),''''), NOW()
     FROM `users` u WHERE u.role = ''student''',
    'SELECT '''''
  )
);
/* students 已存在的旧行：列可能还是 NOT NULL DEFAULT '' -> 改 NULL + 空串转 NULL */
CALL `_v3_exec`('students.student_no 改 NULLABLE（幂等）',
  IF(`_v3_has_table`('students') = 1 AND `_v3_has_col`('students','student_no') = 1,
    'ALTER TABLE `students` MODIFY COLUMN `student_no` VARCHAR(30) NULL DEFAULT NULL',
    'SELECT '''''
  )
);
CALL `_v3_exec`('students 空串 student_no 统一转 NULL（避免 UNIQUE 冲突）',
  IF(`_v3_has_table`('students') = 1 AND `_v3_has_col`('students','student_no') = 1,
    'UPDATE `students` SET `student_no` = NULL WHERE `student_no` = ''''',
    'SELECT '''''
  )
);

/* =============================================================
   4) enterprise_mentors 升级：
      - 如果老表存在 且有 user_id 列但没 account_id 列：补 account_id 列
      - 回填老 enterprise_mentors.user_id → account_id（等于同一个数值，因为
        login_accounts.id 直接复用 users.id）
      - 给新 UK + 新 FK（account_id → login_accounts）
   ============================================================= */
CALL `_v3_exec`('enterprise_mentors 补 account_id 列',
  IF(`_v3_has_table`('enterprise_mentors') = 1 AND
     `_v3_has_col`('enterprise_mentors','user_id') = 1 AND
     `_v3_has_col`('enterprise_mentors','account_id') = 0,
    'ALTER TABLE `enterprise_mentors` ADD COLUMN `account_id` INT NULL AFTER `id`',
    'SELECT '''''
  )
);

CALL `_v3_exec`('enterprise_mentors account_id 列回填 = user_id',
  IF(`_v3_has_table`('enterprise_mentors') = 1 AND
     `_v3_has_col`('enterprise_mentors','account_id') = 1,
    'UPDATE `enterprise_mentors` SET `account_id` = `user_id` WHERE `account_id` IS NULL',
    'SELECT '''''
  )
);

CALL `_v3_exec`('enterprise_mentors account_id NOT NULL 收束',
  IF(`_v3_has_table`('enterprise_mentors') = 1 AND
     `_v3_has_col`('enterprise_mentors','account_id') = 1,
    'ALTER TABLE `enterprise_mentors` MODIFY COLUMN `account_id` INT NOT NULL',
    'SELECT '''''
  )
);

/* 新 UK：account_id + enterprise_id */
CALL `_v3_exec`('enterprise_mentors 新建 UNIQUE(account_id,enterprise_id)',
  IF(`_v3_has_table`('enterprise_mentors') = 1 AND
     `_v3_has_idx`('enterprise_mentors','uk_em_account_enterprise') = 0,
    'ALTER TABLE `enterprise_mentors`
       ADD UNIQUE KEY `uk_em_account_enterprise` (`account_id`,`enterprise_id`)',
    'SELECT '''''
  )
);

/* 新 FK：account_id → login_accounts */
CALL `_v3_exec`('enterprise_mentors 新建 account_id 外键',
  IF(`_v3_has_table`('enterprise_mentors') = 1 AND
     `_v3_has_fk`('enterprise_mentors','fk_em_account_v3') = 0 AND
     `_v3_has_table`('login_accounts') = 1,
    'ALTER TABLE `enterprise_mentors`
       ADD CONSTRAINT `fk_em_account_v3` FOREIGN KEY (`account_id`)
         REFERENCES `login_accounts`(`id`) ON DELETE CASCADE ON UPDATE RESTRICT',
    'SELECT '''''
  )
);

/* enterprise_mentors 缺 extra 就补 */
CALL `_v3_exec`('enterprise_mentors 补 extra JSON 列',
  IF(`_v3_has_table`('enterprise_mentors') = 1 AND
     `_v3_has_col`('enterprise_mentors','extra') = 0,
    'ALTER TABLE `enterprise_mentors` ADD COLUMN `extra` JSON NULL',
    'SELECT '''''
  )
);

/* =============================================================
   5) 新增关联表 task_class_ref / job_class_ref
   ============================================================= */
CALL `_v3_exec`('task_class_ref 建表',
  IF(`_v3_has_table`('task_class_ref') = 0,
    'CREATE TABLE `task_class_ref` (
      `task_id`  INT NOT NULL,
      `class_id` INT NOT NULL,
      PRIMARY KEY(`task_id`,`class_id`),
      KEY `idx_tcr_class` (`class_id`),
      CONSTRAINT `fk_tcr_task`  FOREIGN KEY(`task_id`)
        REFERENCES `tasks`(`id`)   ON DELETE CASCADE ON UPDATE RESTRICT,
      CONSTRAINT `fk_tcr_class` FOREIGN KEY(`class_id`)
        REFERENCES `classes`(`id`) ON DELETE CASCADE ON UPDATE RESTRICT
     ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci',
    'SELECT '''''
  )
);

/* 回填 task_class_ref：把老 tasks.class_id 逗号拆成行（兼容 1..10 个班级） */
CALL `_v3_exec`('task_class_ref 回填（老 tasks.class_id 逗号分隔）',
  IF(`_v3_has_table`('task_class_ref') = 1 AND
     `_v3_has_table`('tasks') = 1 AND
     `_v3_has_col`('tasks','class_id') = 1 AND
     (SELECT COUNT(*) FROM `task_class_ref`) = 0,
    'INSERT IGNORE INTO `task_class_ref`(`task_id`,`class_id`)
     SELECT t.id, CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(t.class_id, '','', n.num), '','', -1) AS UNSIGNED) AS cid
     FROM `tasks` t
     CROSS JOIN (
        SELECT 1 num UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5
        UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9 UNION SELECT 10
     ) n
     WHERE t.class_id IS NOT NULL AND CHAR_LENGTH(t.class_id) > 0
       AND n.num <= 1 + CHAR_LENGTH(t.class_id) - CHAR_LENGTH(REPLACE(t.class_id,'','',''''))',
    'SELECT '''''
  )
);

CALL `_v3_exec`('job_class_ref 建表',
  IF(`_v3_has_table`('job_class_ref') = 0,
    'CREATE TABLE `job_class_ref` (
      `job_id`   INT NOT NULL,
      `class_id` INT NOT NULL,
      PRIMARY KEY(`job_id`,`class_id`),
      KEY `idx_jcr_class` (`class_id`),
      CONSTRAINT `fk_jcr_job`   FOREIGN KEY(`job_id`)
        REFERENCES `job_positions`(`id`) ON DELETE CASCADE ON UPDATE RESTRICT,
      CONSTRAINT `fk_jcr_class` FOREIGN KEY(`class_id`)
        REFERENCES `classes`(`id`)       ON DELETE CASCADE ON UPDATE RESTRICT
     ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci',
    'SELECT '''''
  )
);

/* 回填 job_class_ref：老列 linked_classes 逗号 + 遗留 class_id 单列都拆 */
CALL `_v3_exec`('job_class_ref 回填（老 job_positions 双字段 → 关联表）',
  IF(`_v3_has_table`('job_class_ref') = 1 AND
     `_v3_has_table`('job_positions') = 1 AND
     (SELECT COUNT(*) FROM `job_class_ref`) = 0,
    'INSERT IGNORE INTO `job_class_ref`(`job_id`,`class_id`)
     SELECT j.id, CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(CONCAT_WS('','',j.linked_classes,j.class_id), '','', n.num), '','', -1) AS UNSIGNED) AS cid
     FROM `job_positions` j
     CROSS JOIN (
        SELECT 1 num UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5
        UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9 UNION SELECT 10
     ) n
     WHERE ( (j.linked_classes IS NOT NULL AND CHAR_LENGTH(j.linked_classes) > 0)
             OR j.class_id IS NOT NULL )
       AND n.num <= 1 + CHAR_LENGTH(CONCAT_WS('','',j.linked_classes,j.class_id))
                       - CHAR_LENGTH(REPLACE(CONCAT_WS('','',j.linked_classes,j.class_id),'','',''''))',
    'SELECT '''''
  )
);

/* =============================================================
   6) submissions 补关键列 + UK
   ============================================================= */
CALL `_v3_exec`('submissions 补 meta JSON',
  IF(`_v3_has_table`('submissions') AND NOT `_v3_has_col`('submissions','meta'),
    'ALTER TABLE `submissions` ADD COLUMN `meta` JSON NULL',
    'SELECT '''''
  )
);
CALL `_v3_exec`('submissions 补 updated_at',
  IF(`_v3_has_table`('submissions') AND NOT `_v3_has_col`('submissions','updated_at'),
    'ALTER TABLE `submissions` ADD COLUMN `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP AFTER `created_at`',
    'SELECT '''''
  )
);
CALL `_v3_exec`('submissions 扩 content → LONGTEXT',
  IF(`_v3_has_table`('submissions') AND `_v3_has_col`('submissions','content'),
    'ALTER TABLE `submissions` MODIFY COLUMN `content` LONGTEXT NULL',
    'SELECT '''''
  )
);
/* 唯一约束：先清洗脏数据再建 UK（保留 task × student 最新的那条 submission，其他 UPDATE class_id 到新表即可） */
CALL `_v3_exec`('submissions 清洗：同 (task_id,student_id) 仅保留最新 id',
  IF(`_v3_has_table`('submissions') AND `_v3_has_idx`('submissions','uk_sub_task_student') = 0,
    'DELETE s1 FROM `submissions` s1
       JOIN `submissions` s2
         ON s1.task_id = s2.task_id AND s1.student_id = s2.student_id AND s1.id < s2.id',
    'SELECT '''''
  )
);
CALL `_v3_exec`('submissions 新建 UNIQUE(task_id, student_id)',
  IF(`_v3_has_table`('submissions') AND `_v3_has_idx`('submissions','uk_sub_task_student') = 0,
    'ALTER TABLE `submissions`
       ADD UNIQUE KEY `uk_sub_task_student` (`task_id`,`student_id`)',
    'SELECT '''''
  )
);
/* submissions 旧 FK 级联从 RESTRICT 改成 CASCADE（删任务 / 学生账号时 submission 一起清）
   先动态删除所有旧的 task_id / student_id FK（不依赖 ibfk_1 这类自动名），再建新约束 */
CALL `_v3_drop_fks_for`('submissions', 'task_id');
CALL `_v3_drop_fks_for`('submissions', 'student_id');
CALL `_v3_exec`('submissions FK task_id→CASCADE',
  IF(`_v3_has_table`('submissions') AND `_v3_has_fk`('submissions','fk_sub_task_v3') = 0 AND
     `_v3_has_table`('tasks'),
    'ALTER TABLE `submissions`
       ADD CONSTRAINT `fk_sub_task_v3` FOREIGN KEY (`task_id`)
         REFERENCES `tasks`(`id`) ON DELETE CASCADE ON UPDATE RESTRICT',
    'SELECT '''''
  )
);
CALL `_v3_exec`('submissions FK student_id（改指向 students.id CASCADE）',
  IF(`_v3_has_table`('submissions') AND `_v3_has_fk`('submissions','fk_sub_student_v3') = 0 AND
     `_v3_has_table`('students'),
    'ALTER TABLE `submissions`
       ADD CONSTRAINT `fk_sub_student_v3` FOREIGN KEY (`student_id`)
         REFERENCES `students`(`id`) ON DELETE CASCADE ON UPDATE RESTRICT',
    'SELECT '''''
  )
);

/* =============================================================
   7) evaluations 补关键列 + UK + FK CASCADE
   ============================================================= */
CALL `_v3_exec`('evaluations 补 evaluator_id INT',
  IF(`_v3_has_table`('evaluations') AND NOT `_v3_has_col`('evaluations','evaluator_id'),
    'ALTER TABLE `evaluations` ADD COLUMN `evaluator_id` INT NULL AFTER `evaluator_type`',
    'SELECT '''''
  )
);
CALL `_v3_exec`('evaluations 补 meta JSON',
  IF(`_v3_has_table`('evaluations') AND NOT `_v3_has_col`('evaluations','meta'),
    'ALTER TABLE `evaluations` ADD COLUMN `meta` JSON NULL',
    'SELECT '''''
  )
);
CALL `_v3_exec`('evaluations 补 updated_at',
  IF(`_v3_has_table`('evaluations') AND NOT `_v3_has_col`('evaluations','updated_at'),
    'ALTER TABLE `evaluations`
       ADD COLUMN `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP AFTER `created_at`',
    'SELECT '''''
  )
);
/* 清洗同一 submission 同 evaluator_type 的重复评价，只保留最新一条 */
CALL `_v3_exec`('evaluations 去重保留最新 id',
  IF(`_v3_has_table`('evaluations') AND `_v3_has_idx`('evaluations','uk_eval_sub_type') = 0,
    'DELETE e1 FROM `evaluations` e1
       JOIN `evaluations` e2
         ON e1.submission_id = e2.submission_id
        AND e1.evaluator_type = e2.evaluator_type
        AND e1.id < e2.id',
    'SELECT '''''
  )
);
CALL `_v3_exec`('evaluations 新建 UNIQUE(submission_id,evaluator_type)',
  IF(`_v3_has_table`('evaluations') AND `_v3_has_idx`('evaluations','uk_eval_sub_type') = 0,
    'ALTER TABLE `evaluations`
       ADD UNIQUE KEY `uk_eval_sub_type` (`submission_id`,`evaluator_type`)',
    'SELECT '''''
  )
);
/* FK：evaluations.submission_id 从 RESTRICT → CASCADE（与 enterprise_evaluations 统一） */
CALL `_v3_drop_fks_for`('evaluations', 'submission_id');
CALL `_v3_exec`('evaluations FK submission CASCADE',
  IF(`_v3_has_table`('evaluations') AND `_v3_has_fk`('evaluations','fk_eval_submission_v3') = 0 AND
     `_v3_has_table`('submissions'),
    'ALTER TABLE `evaluations`
       ADD CONSTRAINT `fk_eval_submission_v3` FOREIGN KEY (`submission_id`)
         REFERENCES `submissions`(`id`) ON DELETE CASCADE ON UPDATE RESTRICT',
    'SELECT '''''
  )
);
/* FK：evaluator_id → teachers.id（evaluator_type=teacher 时才非空）
   注：evaluator_id 是新增列，旧库不会有 FK，无需先删除 */
CALL `_v3_exec`('evaluations FK evaluator_id→teachers',
  IF(`_v3_has_table`('evaluations') AND
     `_v3_has_col`('evaluations','evaluator_id') AND
     `_v3_has_fk`('evaluations','fk_eval_evaluator_v3') = 0 AND `_v3_has_table`('teachers'),
    'ALTER TABLE `evaluations`
       ADD CONSTRAINT `fk_eval_evaluator_v3` FOREIGN KEY (`evaluator_id`)
         REFERENCES `teachers`(`id`) ON DELETE SET NULL ON UPDATE RESTRICT,
       ADD KEY `idx_eval_evaluator` (`evaluator_id`)',
    'SELECT '''''
  )
);

/* =============================================================
   8) classes / class_members / job_positions / enterprise_evaluations
      等其他存量 FK 对齐到新角色表
   ============================================================= */
/* classes：先删 teacher_id 上所有旧 FK（原指向 users.id），重建指向 teachers.id */
CALL `_v3_drop_fks_for`('classes', 'teacher_id');
CALL `_v3_exec`('classes.teacher_id FK 改指向 teachers.id',
  IF(`_v3_has_table`('classes') AND `_v3_has_fk`('classes','fk_class_teacher_v3') = 0 AND
     `_v3_has_table`('teachers'),
    'ALTER TABLE `classes`
       ADD CONSTRAINT `fk_class_teacher_v3` FOREIGN KEY (`teacher_id`)
         REFERENCES `teachers`(`id`) ON DELETE SET NULL ON UPDATE RESTRICT',
    'SELECT '''''
  )
);
/* class_members：删 student_id 上的旧 FK（原指向 users.id），重建指向 students.id */
CALL `_v3_drop_fks_for`('class_members', 'student_id');
CALL `_v3_exec`('class_members.student_id FK 改指向 students.id',
  IF(`_v3_has_table`('class_members') AND
     `_v3_has_fk`('class_members','fk_cm_student_v3') = 0 AND `_v3_has_table`('students'),
    'ALTER TABLE `class_members`
       ADD CONSTRAINT `fk_cm_student_v3` FOREIGN KEY (`student_id`)
         REFERENCES `students`(`id`) ON DELETE CASCADE ON UPDATE RESTRICT',
    'SELECT '''''
  )
);
/* class_members：确保有 denorm 列（旧库可能有、可能没有，幂等补齐） */
CALL `_v3_exec`('class_members ADD student_name（冗余列，列表免 join）',
  IF(`_v3_has_table`('class_members') AND `_v3_has_col`('class_members','student_name') = 0,
    'ALTER TABLE `class_members` ADD COLUMN `student_name` VARCHAR(50) NOT NULL DEFAULT ''''',
    'SELECT '''''
  )
);
CALL `_v3_exec`('class_members ADD student_number（冗余列，列表免 join）',
  IF(`_v3_has_table`('class_members') AND `_v3_has_col`('class_members','student_number') = 0,
    'ALTER TABLE `class_members` ADD COLUMN `student_number` VARCHAR(30) NOT NULL DEFAULT ''''',
    'SELECT '''''
  )
);
/* 回填 class_members denorm 列（从 login_accounts + students） */
CALL `_v3_exec`('回填 class_members.student_name / student_number（空值才填）',
  IF(`_v3_has_table`('class_members') AND `_v3_has_table`('students') AND `_v3_has_table`('login_accounts'),
    'UPDATE `class_members` cm
       JOIN `students` s   ON s.id = cm.student_id
       JOIN `login_accounts` a ON a.id = s.account_id
      SET cm.student_name   = COALESCE(NULLIF(cm.student_name,''''), s.real_name),
          cm.student_number = COALESCE(NULLIF(cm.student_number,''''), s.student_no)
      WHERE (cm.student_name = '''' OR cm.student_number = '''')',
    'SELECT '''''
  )
);
/* job_positions：删 created_by 上旧 FK（原 fk_jp_creator），重建指向 enterprise_mentors.id */
CALL `_v3_drop_fks_for`('job_positions', 'created_by');
CALL `_v3_exec`('job_positions.created_by FK 改指向 enterprise_mentors.id',
  IF(`_v3_has_table`('job_positions') AND
     `_v3_has_fk`('job_positions','fk_jp_creator_v3') = 0 AND
     `_v3_has_table`('enterprise_mentors'),
    'ALTER TABLE `job_positions`
       ADD CONSTRAINT `fk_jp_creator_v3` FOREIGN KEY (`created_by`)
         REFERENCES `enterprise_mentors`(`id`) ON DELETE SET NULL ON UPDATE RESTRICT',
    'SELECT '''''
  )
);
/* enterprise_evaluations：删 mentor_id 上旧 FK（原 fk_ee_mentor），重建指向 enterprise_mentors.id */
CALL `_v3_drop_fks_for`('enterprise_evaluations', 'mentor_id');
CALL `_v3_exec`('enterprise_evaluations.mentor_id FK 改指向 enterprise_mentors.id',
  IF(`_v3_has_table`('enterprise_evaluations') AND
     `_v3_has_fk`('enterprise_evaluations','fk_ee_mentor_v3') = 0 AND
     `_v3_has_table`('enterprise_mentors'),
    'ALTER TABLE `enterprise_evaluations`
       ADD CONSTRAINT `fk_ee_mentor_v3` FOREIGN KEY (`mentor_id`)
         REFERENCES `enterprise_mentors`(`id`) ON DELETE CASCADE ON UPDATE RESTRICT',
    'SELECT '''''
  )
);
/* tasks.created_by FK 改指向 teachers.id（原 FK 指向 users.id） */
CALL `_v3_drop_fks_for`('tasks', 'created_by');
CALL `_v3_exec`('tasks.created_by FK 改指向 teachers.id',
  IF(`_v3_has_table`('tasks') AND
     `_v3_has_fk`('tasks','fk_tasks_creator_v3') = 0 AND `_v3_has_table`('teachers'),
    'ALTER TABLE `tasks`
       ADD CONSTRAINT `fk_tasks_creator_v3` FOREIGN KEY (`created_by`)
         REFERENCES `teachers`(`id`) ON DELETE SET NULL ON UPDATE RESTRICT',
    'SELECT '''''
  )
);

/* =============================================================
   9) enterprises 补 extra JSON（当前 SQL 里有，但 ORM 没声明，保留一致性）
   ============================================================= */
CALL `_v3_exec`('enterprises 补 extra JSON',
  IF(`_v3_has_table`('enterprises') AND NOT `_v3_has_col`('enterprises','extra'),
    'ALTER TABLE `enterprises` ADD COLUMN `extra` JSON NULL',
    'SELECT '''''
  )
);
CALL `_v3_exec`('classes 补 extra JSON',
  IF(`_v3_has_table`('classes') AND NOT `_v3_has_col`('classes','extra'),
    'ALTER TABLE `classes` ADD COLUMN `extra` JSON NULL',
    'SELECT '''''
  )
);
CALL `_v3_exec`('tasks 补 extra JSON',
  IF(`_v3_has_table`('tasks') AND NOT `_v3_has_col`('tasks','extra'),
    'ALTER TABLE `tasks` ADD COLUMN `extra` JSON NULL',
    'SELECT '''''
  )
);
CALL `_v3_exec`('users 兼容列 extra JSON（如果还没清旧 users）',
  IF(`_v3_has_table`('users') AND NOT `_v3_has_col`('users','extra'),
    'ALTER TABLE `users` ADD COLUMN `extra` JSON NULL',
    'SELECT '''''
  )
);

/* =============================================================
   10) 清理重复索引（每张表如果存在两份相同，就删一份留一份规范名）
   ============================================================= */
CALL `_v3_exec`('class_members 删重复索引 idx_cm_class_student（保留唯一键 uk_cm_class_student）',
  IF(`_v3_has_table`('class_members') AND
     `_v3_has_idx`('class_members','idx_cm_class_student'),
    'ALTER TABLE `class_members` DROP INDEX `idx_cm_class_student`',
    'SELECT '''''
  )
);
CALL `_v3_exec`('class_members 删重复索引 class_id（保留 uk_cm_class_student）',
  IF(`_v3_has_table`('class_members') AND `_v3_has_idx`('class_members','class_id'),
    'ALTER TABLE `class_members` DROP INDEX `class_id`',
    'SELECT '''''
  )
);
CALL `_v3_exec`('class_members 删重复 idx_cm_student（保留 student_id）',
  IF(`_v3_has_table`('class_members') AND `_v3_has_idx`('class_members','idx_cm_student'),
    'ALTER TABLE `class_members` DROP INDEX `idx_cm_student`',
    'SELECT '''''
  )
);
CALL `_v3_exec`('classes 删重复 teacher_id（保留 idx_classes_teacher）',
  IF(`_v3_has_table`('classes') AND `_v3_has_idx`('classes','teacher_id'),
    'ALTER TABLE `classes` DROP INDEX `teacher_id`',
    'SELECT '''''
  )
);
CALL `_v3_exec`('users 删重复 username（保留 uk_users_username）',
  IF(`_v3_has_table`('users') AND `_v3_has_idx`('users','username') AND
     `_v3_has_idx`('users','uk_users_username'),
    'ALTER TABLE `users` DROP INDEX `username`',
    'SELECT '''''
  )
);

SET FOREIGN_KEY_CHECKS = 1;

/* =============================================================
   升级结果 summary
   ============================================================= */
SELECT
  'login_accounts'  AS tbl,
  `_v3_has_table`('login_accounts') AS created,
  (SELECT COUNT(*) FROM `login_accounts`) AS rows_cnt
UNION ALL SELECT 'teachers', `_v3_has_table`('teachers'), (SELECT COUNT(*) FROM `teachers`)
UNION ALL SELECT 'students', `_v3_has_table`('students'), (SELECT COUNT(*) FROM `students`)
UNION ALL SELECT 'enterprise_mentors（补 account_id 列）',
         `_v3_has_col`('enterprise_mentors','account_id'),
         (SELECT COUNT(*) FROM `enterprise_mentors`)
UNION ALL SELECT 'task_class_ref（拆 tasks.class_id）',
         `_v3_has_table`('task_class_ref'), (SELECT COUNT(*) FROM `task_class_ref`)
UNION ALL SELECT 'job_class_ref（拆 job_positions 双列）',
         `_v3_has_table`('job_class_ref'), (SELECT COUNT(*) FROM `job_class_ref`)
UNION ALL SELECT 'submissions UK(task_id,student_id)',
         `_v3_has_idx`('submissions','uk_sub_task_student'), 0
UNION ALL SELECT 'evaluations UK(submission_id,evaluator_type)',
         `_v3_has_idx`('evaluations','uk_eval_sub_type'), 0
;

SELECT * FROM `_v3_upgrade_log` ORDER BY `id`;

/* =====================================================================
   【V3 收尾 · 手动执行】下方 DDL 是清理 2026 老库遗留字段/表，
   你先在测试库比对一遍数据，确认：
     - login_accounts.id === 老 users.id 1:1 映射
     - teachers / students 数量 === 老 users 对应 role 数
     - task_class_ref / job_class_ref 回填后 JOIN 班级数量对得上
   然后把下方注释里的 DDL 复制出来执行。
   ===================================================================== */
/*
ALTER TABLE `evaluations`
  DROP COLUMN `score`, DROP COLUMN `content`, DROP COLUMN `scores`;

ALTER TABLE `enterprise_evaluations`
  DROP COLUMN `score`, DROP COLUMN `content`, DROP COLUMN `scores`;

ALTER TABLE `job_positions`
  DROP COLUMN `salary`, DROP COLUMN `location`,
  DROP COLUMN `class_id`, DROP COLUMN `linked_classes`;

ALTER TABLE `tasks`
  DROP COLUMN `class_id`, DROP COLUMN `steps_def`;

ALTER TABLE `submissions`
  DROP COLUMN `class_id`;

-- 三角色分表完成后，最后删老 users 表（非常谨慎！）
-- DROP TABLE `users`;
*/
