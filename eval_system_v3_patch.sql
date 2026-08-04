/* ========================================================================
   智训云 V3 增量补丁脚本（后端对齐的 4 处修改 + v2→v3 兼容漏项兜底）
   ------------------------------------------------------------------------
   适用场景：
     - 你已执行过 eval_system_v3_init.sql  或  eval_system_v3_upgrade.sql
     - 需要单独打"后端冒烟时补的 4 处小改动 + v3_upgrade 可能漏的列"
     - 脚本幂等：重复执行不会报错，也不会破坏已有数据

   真实列归属（避免再次踩坑）：
     login_accounts(id, username, password_hash, role, email, phone, avatar,
                    status, extra, created_at, updated_at)
          ⚠️ 注意：login_accounts **没有 real_name / user_number 列**！
     students(id, account_id, real_name, student_no, grade, major, ...)
     teachers(id, account_id, real_name, teacher_no, title, department, ...)
     enterprise_mentors(id, account_id, enterprise_id, user_id(兼容),
                        real_name, title, department, is_admin, status, ...)
   即：real_name / 工号学号 全都在 *角色表* 里，不在共享登录表里。

   包含的 4 项补丁（全部用 information_schema 做存在性判断）：
     P1) class_members 补 student_name / student_number（冗余列，列表展示免 join）
         + 回填：只从 students 读（real_name + student_no），不 JOIN login_accounts
     P2) teachers.teacher_no 改为 NULLABLE + 现有空串 '' 统一转 NULL
         （UNIQUE 约束下 NULL 不冲突，允许多人尚未分配工号）
     P3) students.student_no 同上，改 NULLABLE + 空串转 NULL
     P4) enterprise_mentors 兼容层对齐（针对 v3_upgrade 可能遗留的漏项）
         · user_id 若仍是 NOT NULL → 改 NULLABLE
         · 若缺 account_id / real_name / status 列 → 补齐
         · 空值用 account_id 关联的 login_accounts.username 兜底（因为
           login_accounts 没有 real_name，只能拿 username 当展示名兜底）

   用法：
     mysql -uroot -p eval_system < eval_system_v3_patch.sql
   或 用 Navicat / DBeaver 等工具打开，选 eval_system 库后执行。
   ======================================================================== */

USE `eval_system`;

-- 避免非事务性存储过程被 DDL 隐式提交干扰，统一不开启显式事务；每条语句独立判断。

/* =============================================================
   辅助存储过程（与 upgrade 脚本同名，重复定义不影响）
   ============================================================= */
DROP PROCEDURE IF EXISTS `_patch_has_table`;
DROP PROCEDURE IF EXISTS `_patch_has_col`;
DROP PROCEDURE IF EXISTS `_patch_exec`;

DELIMITER $$

CREATE PROCEDURE `_patch_has_table`(IN tbl VARCHAR(128), OUT ret TINYINT)
BEGIN
  SELECT COUNT(*) INTO ret
    FROM information_schema.TABLES
   WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = tbl;
END$$

CREATE PROCEDURE `_patch_has_col`(IN tbl VARCHAR(128), IN col VARCHAR(128), OUT ret TINYINT)
BEGIN
  SELECT COUNT(*) INTO ret
    FROM information_schema.COLUMNS
   WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = tbl AND COLUMN_NAME = col;
END$$

CREATE PROCEDURE `_patch_exec`(IN title VARCHAR(255), IN stmt TEXT)
BEGIN
  -- stmt = '' 时跳过，用于 IF(cond, 'ALTER ...', '') 风格
  IF stmt IS NOT NULL AND stmt <> '' THEN
    SET @_patch_sql = stmt;
    PREPARE s FROM @_patch_sql;
    EXECUTE s;
    DEALLOCATE PREPARE s;
  END IF;
  SELECT title AS `PATCH_STEP`;
END$$

DELIMITER ;


/* =============================================================
   P1) class_members 补 student_name + student_number
   ============================================================= */
CALL `_patch_has_table`('class_members', @_cm_exist);
CALL `_patch_has_table`('students', @_stu_exist);

CALL `_patch_exec`(
  'P1-1: class_members 补 student_name 冗余列',
  IF(@_cm_exist = 1,
    (SELECT IF(COUNT(*)=0,
      CONCAT('ALTER TABLE `class_members` ADD COLUMN `student_name` VARCHAR(50) NOT NULL DEFAULT ',QUOTE(''),' COMMENT ',QUOTE('冗余：学生姓名，列表展示免 join'),' AFTER `student_id`'),
      'SELECT ''SKIP student_name already exists''')
       FROM information_schema.COLUMNS
      WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='class_members' AND COLUMN_NAME='student_name'),
    'SELECT ''SKIP class_members 表不存在'''
  )
);

CALL `_patch_exec`(
  'P1-2: class_members 补 student_number 冗余列',
  IF(@_cm_exist = 1,
    (SELECT IF(COUNT(*)=0,
      CONCAT('ALTER TABLE `class_members` ADD COLUMN `student_number` VARCHAR(30) NOT NULL DEFAULT ',QUOTE(''),' COMMENT ',QUOTE('冗余：学号，列表展示免 join'),' AFTER `student_name`'),
      'SELECT ''SKIP student_number already exists''')
       FROM information_schema.COLUMNS
      WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='class_members' AND COLUMN_NAME='student_number'),
    'SELECT ''SKIP class_members 表不存在'''
  )
);

/* 回填：只 JOIN students（real_name / student_no 本来就在这张表）
   ⚠️ 不再 JOIN login_accounts：它没有 real_name 列！
   多重兜底保证 NOT NULL 列永远不写 NULL：
     原值若非空/非空格 → 保留
     否则 s.real_name / s.student_no → 若为 NULL 兜底成空串 */
CALL `_patch_exec`(
  'P1-3: 回填 class_members.student_name / student_number（从 students 表，正确归属）',
  IF(@_cm_exist = 1 AND @_stu_exist = 1,
    CONCAT(
      'UPDATE `class_members` cm', CHAR(10),
      '  JOIN `students` s ON s.id = cm.student_id', CHAR(10),
      ' SET cm.student_name   = COALESCE(NULLIF(TRIM(cm.student_name),',QUOTE(''),'), IFNULL(s.real_name,',QUOTE(''),'), ',QUOTE(''),'),', CHAR(10),
      '     cm.student_number = COALESCE(NULLIF(TRIM(cm.student_number),',QUOTE(''),'), IFNULL(s.student_no,',QUOTE(''),'), ',QUOTE(''),')', CHAR(10),
      ' WHERE cm.student_name IS NULL OR TRIM(cm.student_name) = ',QUOTE(''),
      '    OR cm.student_number IS NULL OR TRIM(cm.student_number) = ',QUOTE('')
    ),
    'SELECT ''SKIP 所需表（class_members/students）不存在'''
  )
);


/* =============================================================
   P2) teachers.teacher_no 改为 NULLABLE + 空串转 NULL
   ============================================================= */
CALL `_patch_has_table`('teachers', @_tea_exist);

CALL `_patch_exec`(
  'P2-1: teachers.teacher_no 改为 NULLABLE',
  IF(@_tea_exist = 1,
    (SELECT IF(COUNT(*)=1,
      'ALTER TABLE `teachers` MODIFY COLUMN `teacher_no` VARCHAR(30) NULL DEFAULT NULL COMMENT ''工号（唯一，允许NULL，未分配者不参与UNIQUE冲突）''',
      'SELECT ''SKIP teacher_no 已是 NULLABLE''')
       FROM information_schema.COLUMNS
      WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='teachers' AND COLUMN_NAME='teacher_no' AND IS_NULLABLE='NO'),
    'SELECT ''SKIP teachers 表不存在'''
  )
);

CALL `_patch_exec`(
  'P2-2: teachers.teacher_no 空串转 NULL',
  IF(@_tea_exist = 1,
    CONCAT('UPDATE `teachers` SET `teacher_no` = NULL WHERE `teacher_no` = ',QUOTE('')),
    'SELECT ''SKIP teachers 表不存在'''
  )
);


/* =============================================================
   P3) students.student_no 改为 NULLABLE + 空串转 NULL
   ============================================================= */
CALL `_patch_has_table`('students', @_stu_exist);

CALL `_patch_exec`(
  'P3-1: students.student_no 改为 NULLABLE',
  IF(@_stu_exist = 1,
    (SELECT IF(COUNT(*)=1,
      'ALTER TABLE `students` MODIFY COLUMN `student_no` VARCHAR(30) NULL DEFAULT NULL COMMENT ''学号（唯一，允许NULL，未分配者不参与UNIQUE冲突）''',
      'SELECT ''SKIP student_no 已是 NULLABLE''')
       FROM information_schema.COLUMNS
      WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='students' AND COLUMN_NAME='student_no' AND IS_NULLABLE='NO'),
    'SELECT ''SKIP students 表不存在'''
  )
);

CALL `_patch_exec`(
  'P3-2: students.student_no 空串转 NULL',
  IF(@_stu_exist = 1,
    CONCAT('UPDATE `students` SET `student_no` = NULL WHERE `student_no` = ',QUOTE('')),
    'SELECT ''SKIP students 表不存在'''
  )
);


/* =============================================================
   P4) enterprise_mentors 兼容层对齐（v2→v3 漏项兜底）
   ============================================================= */
CALL `_patch_has_table`('enterprise_mentors', @_em_exist);
CALL `_patch_has_table`('login_accounts', @_la_exist);

-- P4-1: user_id NOT NULL → NULLABLE（兼容列，v3 新增数据双写 account_id+user_id=同值即可）
CALL `_patch_exec`(
  'P4-1: enterprise_mentors.user_id 改为 NULLABLE（兼容列，不再做 NOT NULL 约束）',
  IF(@_em_exist = 1,
    (SELECT IF(COUNT(*)=1,
      'ALTER TABLE `enterprise_mentors` MODIFY COLUMN `user_id` INT NULL DEFAULT NULL COMMENT ''兼容列：与 account_id 同值，v3 新数据同步写入；历史数据保留原值''',
      'SELECT ''SKIP user_id 已是 NULLABLE 或不存在''')
       FROM information_schema.COLUMNS
      WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='enterprise_mentors' AND COLUMN_NAME='user_id' AND IS_NULLABLE='NO'),
    'SELECT ''SKIP enterprise_mentors 表不存在'''
  )
);

-- P4-2: 补 account_id 列（极少数部分 upgrade 漏项）
CALL `_patch_exec`(
  'P4-2: enterprise_mentors 补 account_id 列（如缺失）',
  IF(@_em_exist = 1,
    (SELECT IF(COUNT(*)=0,
      'ALTER TABLE `enterprise_mentors` ADD COLUMN `account_id` INT NOT NULL COMMENT ''login_accounts.id（v3 真正的账号 FK）'' AFTER `id`',
      'SELECT ''SKIP account_id 列已存在''')
       FROM information_schema.COLUMNS
      WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='enterprise_mentors' AND COLUMN_NAME='account_id'),
    'SELECT '''''
  )
);

-- P4-3: account_id 回填（存在 user_id 兼容列时，account_id 缺 = user_id；否则保持原状）
CALL `_patch_exec`(
  'P4-3: enterprise_mentors.account_id 回填 = user_id（若有缺且两列共存）',
  IF(@_em_exist = 1,
    (SELECT IF(COUNT(DISTINCT COLUMN_NAME)=2,
      'UPDATE `enterprise_mentors` SET `account_id` = `user_id` WHERE `account_id` IS NULL OR `account_id` = 0',
      'SELECT ''SKIP user_id/account_id 不共存，跳过回填''')
       FROM information_schema.COLUMNS
      WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='enterprise_mentors'
        AND COLUMN_NAME IN ('user_id','account_id')),
    'SELECT '''''
  )
);

-- P4-4: 补 real_name 列（enterprise_mentors 自己的姓名列；v2 升级可能漏）
CALL `_patch_exec`(
  'P4-4: enterprise_mentors 补 real_name 列（如缺失）',
  IF(@_em_exist = 1,
    (SELECT IF(COUNT(*)=0,
      CONCAT('ALTER TABLE `enterprise_mentors` ADD COLUMN `real_name` VARCHAR(50) NOT NULL DEFAULT ',QUOTE(''),' COMMENT ''导师真实姓名'' AFTER `enterprise_id`'),
      'SELECT ''SKIP real_name 列已存在''')
       FROM information_schema.COLUMNS
      WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='enterprise_mentors' AND COLUMN_NAME='real_name'),
    'SELECT '''''
  )
);

/* P4-5: real_name 回填（enterprise_mentors 自身为空时）
   由于 login_accounts **没有 real_name** 列，我们按这个优先级兜底：
     1) enterprise_mentors.real_name 已有值 → 保留（用 NULLIF+TRIM 判断"空"）
     2) 否则 login_accounts.username → 这是登录表里唯一的"可展示名"
     3) 极端情况 username 也 NULL → 空串 */
CALL `_patch_exec`(
  'P4-5: enterprise_mentors.real_name 回填（优先用原值，空则兜底 login_accounts.username）',
  IF(@_em_exist = 1 AND @_la_exist = 1,
    CONCAT(
      'UPDATE `enterprise_mentors` em', CHAR(10),
      '  JOIN `login_accounts` a ON a.id = em.account_id', CHAR(10),
      ' SET em.real_name = COALESCE(NULLIF(TRIM(em.real_name),',QUOTE(''),'), NULLIF(a.username,',QUOTE(''),'), ',QUOTE(''),')', CHAR(10),
      ' WHERE em.real_name IS NULL OR TRIM(em.real_name) = ',QUOTE('')
    ),
    'SELECT ''SKIP enterprise_mentors/login_accounts 不全存在，跳过回填'''
  )
);

-- P4-6: 补 status 列（v3 枚举 active/inactive；v2 可能缺）
CALL `_patch_exec`(
  'P4-6: enterprise_mentors 补 status 列（如缺失）',
  IF(@_em_exist = 1,
    (SELECT IF(COUNT(*)=0,
      'ALTER TABLE `enterprise_mentors` ADD COLUMN `status` ENUM(''active'',''inactive'') NOT NULL DEFAULT ''active'' COMMENT ''导师状态：active=在职；inactive=停用'' AFTER `is_admin`',
      'SELECT ''SKIP status 列已存在''')
       FROM information_schema.COLUMNS
      WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='enterprise_mentors' AND COLUMN_NAME='status'),
    'SELECT '''''
  )
);


/* =============================================================
   P5) job_positions 缺列补齐（针对从 v2 升级过来漏写 ORM 新增兼容列的情况）
        ORM 列定义（enterprise_models.JobPosition）：
          linked_classes VARCHAR(500)  — 旧 CSV 绑定班级的兼容列（v3 逻辑改走 job_class_ref，但仍保留兼容解析）
          class_id INT                 — 旧单列绑定班级的兼容列（nullable）
   ============================================================= */
SET @_jp_exist = 0;
CALL `_patch_has_table`('job_positions', @_jp_exist);

CALL `_patch_exec`(
  'P5-1: job_positions 补 linked_classes 列（如缺失）',
  IF(@_jp_exist = 1,
    (SELECT IF(COUNT(*)=0,
      CONCAT('ALTER TABLE `job_positions` ADD COLUMN `linked_classes` VARCHAR(500) NOT NULL DEFAULT ',QUOTE(''),' COMMENT ''兼容旧版 CSV 绑定班级；v3 优先走 job_class_ref 关联表'' AFTER `tags`'),
      'SELECT ''SKIP linked_classes 列已存在''')
       FROM information_schema.COLUMNS
      WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='job_positions' AND COLUMN_NAME='linked_classes'),
    'SELECT '''''
  )
);

CALL `_patch_exec`(
  'P5-2: job_positions 补 class_id 列（如缺失）',
  IF(@_jp_exist = 1,
    (SELECT IF(COUNT(*)=0,
      'ALTER TABLE `job_positions` ADD COLUMN `class_id` INT NULL DEFAULT NULL COMMENT ''兼容旧版单班级绑定；v3 优先走 job_class_ref 关联表'' AFTER `linked_classes`',
      'SELECT ''SKIP class_id 列已存在''')
       FROM information_schema.COLUMNS
      WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='job_positions' AND COLUMN_NAME='class_id'),
    'SELECT '''''
  )
);

CALL `_patch_exec`(
  'P5-3: job_positions 补 ai_generated 列（如缺失）',
  IF(@_jp_exist = 1,
    (SELECT IF(COUNT(*)=0,
      'ALTER TABLE `job_positions` ADD COLUMN `ai_generated` TINYINT(1) NOT NULL DEFAULT 0 COMMENT ''是否由 AI 生成岗位'' AFTER `updated_at`',
      'SELECT ''SKIP ai_generated 列已存在''')
       FROM information_schema.COLUMNS
      WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='job_positions' AND COLUMN_NAME='ai_generated'),
    'SELECT '''''
  )
);

CALL `_patch_exec`(
  'P5-4: job_positions 补 ai_prompt_snapshot 列（如缺失）',
  IF(@_jp_exist = 1,
    (SELECT IF(COUNT(*)=0,
      'ALTER TABLE `job_positions` ADD COLUMN `ai_prompt_snapshot` TEXT NULL DEFAULT NULL COMMENT ''AI 生成岗位时使用的提示词快照'' AFTER `ai_generated`',
      'SELECT ''SKIP ai_prompt_snapshot 列已存在''')
       FROM information_schema.COLUMNS
      WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='job_positions' AND COLUMN_NAME='ai_prompt_snapshot'),
    'SELECT '''''
  )
);


/* =============================================================
   清理临时存储过程
   ============================================================= */
DROP PROCEDURE IF EXISTS `_patch_has_table`;
DROP PROCEDURE IF EXISTS `_patch_has_col`;
DROP PROCEDURE IF EXISTS `_patch_exec`;


/* =============================================================
   Summary 输出：打完补丁后的表结构快照（便于你核对）
   ============================================================= */
SELECT '=== PATCH APPLIED. Final schema checks ===' AS `PATCH_SUMMARY`;

SELECT TABLE_NAME, COLUMN_NAME, IS_NULLABLE, COLUMN_DEFAULT, COLUMN_TYPE
  FROM information_schema.COLUMNS
 WHERE TABLE_SCHEMA = DATABASE()
   AND (
     (TABLE_NAME='class_members'      AND COLUMN_NAME IN ('student_name','student_number'))
  OR (TABLE_NAME='teachers'           AND COLUMN_NAME = 'teacher_no')
  OR (TABLE_NAME='students'           AND COLUMN_NAME = 'student_no')
  OR (TABLE_NAME='enterprise_mentors' AND COLUMN_NAME IN ('user_id','account_id','real_name','status'))
  OR (TABLE_NAME='job_positions'      AND COLUMN_NAME IN ('linked_classes','class_id','ai_generated','ai_prompt_snapshot'))
   )
 ORDER BY TABLE_NAME, ORDINAL_POSITION;
