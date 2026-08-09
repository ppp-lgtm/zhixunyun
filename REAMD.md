# 知训云 · 软件实训智能评价平台

> 第十五届中国软件杯参赛作品 · 基于AI的软件实训教学智能评价系统

## 项目概述

知训云 —— 一款基于 AI 的软件实训教学智能评价系统。支持**三端协同**（教师端 / 学生端 / 企业端），覆盖实训全流程：

- **教师端**：创建班级、发布任务、配置评价维度、查看学生提交、人工复核评分、数据统计分析、导出报告
- **学生端**：分步提交实训成果（代码/截图/说明）、查看AI即时评分与反馈、追踪个人成长、查看面试邀约
- **企业端**：发布招聘岗位、查看学生成果物、企业终评、岗位匹配推荐、发送面试邀约、生成匹配报告

AI 自动按可配置维度评分（代码质量/文档规范/界面设计/功能完整性），支持三方对标（AI初评 / 教师复评 / 企业终评）同屏对比。

## 技术栈

| 层级 | 技术 |
|-------|-----------|
| 前端 | Vue 3 + TypeScript + Vite + Tailwind CSS 3 + Element Plus |
| 后端 | Python FastAPI + SQLAlchemy ORM + MySQL / SQLite |
| AI | DeepSeek API（文本评价）+ 硅基流动 API（图片OCR识别） |
| 认证 | JWT (HS256) + SHA256 加盐密码哈希 |
| 图表 | ECharts（通过 vue-echarts 封装）+ matplotlib（PDF报告内嵌图表） |
| 报告 | openpyxl（Excel）+ fpdf2（PDF，支持中文字体注册） |
| 图标 | Iconify（`mdi:` 前缀 = Material Design Icons） |

## 快速开始

### 后端 (Python FastAPI)

```bash
cd backend
# 首次：创建虚拟环境并安装依赖
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # 麒麟/Linux/macOS
pip install -r requirements.txt

# 启动开发服务器（热重载，端口 8000）
venv\Scripts\activate && python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
# 或直接使用快捷脚本：
s.bat
```

### 前端 (Vue 3 + Vite)

```bash
cd frontend
npm install        # 首次
npm run dev        # 开发服务器（默认端口 5173）
npm run build      # 生产构建 → dist/
npm run preview    # 预览生产构建
```

### 数据库

- MySQL 连接字符串：`mysql+pymysql://root:root@localhost:3306/eval_system`
- 配置位于 `backend/app/config.py` 和 `backend/app/models/database.py`
- 表由 SQLAlchemy 在首次请求时自动创建（未使用数据库迁移工具）

### 演示数据导入

```bash
cd backend
# 一键导入全部演示数据（自动识别 MySQL/SQLite，幂等可重复执行）
python ..\演示数据\_apply_demo_seed_ALL.py
```

导入后可获得 10 个演示账号（密码统一 `123456`）：

| 角色 | 账号 | 说明 |
|------|------|------|
| 教师 | admin9001 | 管理 2 个演示班级 |
| 企业 | hr9001 | 星云智能 HR，发布 1 个岗位 |
| 学生 | s9001 ~ s9008 | 8 名学生，3 个任务，12 条提交，8 份企业评价 |

详细演示流程见 [演示数据/演示脚本.md](file:///G:/b1提交物/code/zhixunyun/演示数据/演示脚本.md)。

## 架构

### 后端结构

```
backend/app/
├── main.py              # FastAPI 应用入口，CORS，全局异常处理，路由注册
├── config.py            # DATABASE_URL
├── models/
│   ├── database.py      # SQLAlchemy 引擎、SessionLocal、Base、get_db()
│   ├── tables.py        # LoginAccount, Teacher, Student, Task, Submission, Evaluation
│   ├── class_models.py  # Class, ClassMember
│   └── enterprise_models.py  # Enterprise, EnterpriseMentor, JobPosition, EnterpriseEvaluation, InterviewInvitation
├── routers/             # 每个功能域一个文件（共 16 个）
│   ├── auth_router.py       # /api/auth/login, /api/auth/register（角色强隔离，统一401提示）
│   ├── enterprise_router.py # /api/enterprise/*（企业注册/登录/岗位/评价/成果物/面试邀约，~2900行，企业ID隔离）
│   ├── job_match_router.py  # /api/job-match/*（岗位匹配推荐+PDF报告生成，~1680行）
│   ├── upload_eval.py       # /api/upload-eval/（上传+AI评价主流程，分步提交）
│   ├── task_manage.py       # /api/tasks/ 增删改查，AI 生成任务要求
│   ├── class_router.py      # /api/classes/ 增删改查，邀请码加入班级
│   ├── statistics.py        # /api/statistics/*（概览、图表、教学建议）
│   ├── teacher_score.py     # /api/teacher/score（教师复核评分）
│   ├── report.py            # /api/report/excel, /api/report/pdf（美化报告导出）
│   ├── criteria.py          # /api/criteria/ 增删改查
│   ├── evaluate.py          # 旧版评价端点
│   ├── upload.py            # 旧版上传端点
│   ├── user_profile.py      # GET/PUT /api/user/profile/，头像上传，修改密码
│   ├── notifications.py     # /api/notifications/
│   └── search.py            # /api/search/
├── services/
│   ├── file_parser.py       # 解析 docx/pdf/图片文件为文本
│   ├── report_generator.py  # Excel/PDF 报告生成（openpyxl美化, fpdf2多页排版+中文字体）
│   ├── code_analyzer.py     # 代码静态分析（LOC/注释率/圈复杂度/TODO）
│   ├── job_matcher.py       # 岗位匹配算法（技能比对+评分排序）
│   └── step_extractor.py    # 分步实训证据提取与规则校验
└── utils/
    ├── ai_evaluator.py  # DeepSeek + 硅基流动客户端，结构化Rubric评分，JSON安全解析
    ├── auth.py          # JWT 创建/解码，密码加盐哈希/验证
    └── auth_deps.py     # 认证依赖：require_login, require_teacher, require_enterprise 等
```

**API 响应约定**：所有端点返回 `{"success": bool, "data": ..., "error"/"detail": ...}` 格式。`main.py` 中的全局异常处理器捕获未处理异常并以此格式返回 500。

**数据隔离**：企业端所有查询均按 `enterprise_id` 过滤，教师端按 `teacher_id` / 班级归属过滤，确保 A 企业/教师无法查看 B 的数据。

### 前端结构

```
frontend/src/
├── main.ts              # 应用启动：Pinia、Router、Element Plus、ECharts、Iconify
├── App.vue              # 根组件：<router-view />
├── config.ts            # API_BASE = 'http://127.0.0.1:8000'
├── router/index.ts      # 路由定义 + 角色守卫（企业用户自动跳转企业端）
├── layout/
│   └── MainLayout.vue   # 深色侧边栏 + 顶部导航 + <router-view> 外壳
├── views/               # 21 个页面组件（见下方路由表）
├── styles/
│   └── global.css       # Tailwind 指令、自定义组件类、Element Plus 全局覆盖
└── img/
    └── logo.png
```

### 路由表

| 路径 | 组件 | 角色 | 说明 |
|------|-----------|------|-------------|
| `/` | Landing | 公开 | 官方首页 |
| `/login` | Login | 公开 | 三角色选择登录 + 注册弹窗 |
| `/landing` | Landing | 公开 | 演示入口页 |
| `/app` | Home | 教师/学生 | 首页仪表盘（按角色展示不同数据） |
| `/app/task-manage` | TaskManage | 教师 | 创建/管理任务，查看提交情况 |
| `/app/class-manage` | ClassManage | 教师 | 创建/编辑/删除班级 |
| `/app/class-scores` | ClassScores | 教师 | 班级成绩排名表 |
| `/app/criteria` | Criteria | 教师 | 配置评价维度与权重 |
| `/app/statistics` | Statistics | 教师 | 图表、AI 教学建议 |
| `/app/student-tasks` | StudentTasks | 学生 | 查看并提交任务 |
| `/app/my-classes` | MyClasses | 学生 | 加入/查看班级，班级排名 |
| `/app/my-scores` | MyScores | 学生 | 个人成绩记录与成长报告 |
| `/app/upload` | Upload | 学生 | 分步上传文件进行评价 |
| `/app/result/:id` | Result | 两者 | 评价详情（AI/教师/企业三方对标） |
| `/app/interview-invitations` | InterviewInvitations | 学生 | 查看企业面试邀约 |
| `/app/profile` | Profile | 两者 | 编辑资料、修改密码、头像上传 |
| `/app/enterprise/dashboard` | EnterpriseDashboard | 企业 | 企业端首页仪表盘 |
| `/app/enterprise/jobs` | EnterpriseJobs | 企业 | 发布/管理招聘岗位 |
| `/app/enterprise/evaluations` | EnterpriseEvaluations | 企业 | 查看学生成果物 + 企业终评 |
| `/app/enterprise/compare` | EnterpriseCompare | 企业 | 三方对标同屏对比 |
| `/app/enterprise/matching` | EnterpriseMatching | 企业 | 岗位匹配推荐 + 下载PDF报告 |
| `/app/enterprise/student/:studentId` | EnterpriseStudentProfile | 企业 | 候选人详细画像 |

### 数据库表

**核心表**：
- **login_accounts**：id, username, password_hash, role（teacher/student/mentor）, status, email, phone, avatar
- **teachers**：id, account_id, real_name, teacher_no
- **students**：id, account_id, real_name, student_no
- **tasks**：id, title, requirements, criteria, criteria_weights, class_id, total_score, deadline, template_path, created_by
- **submissions**：id, task_id, student_id, filename, file_path, content, class_id, step_evidences（JSON）, meta（JSON）
- **evaluations**：id, submission_id, evaluator_type（ai/teacher）, total_score, dimension_scores（JSON）, comment, step_completeness（JSON）, logic_issues（JSON）
- **evaluation_criteria**：id, task_id, name, weight, description
- **classes**：id, name, grade, major, semester, course_name, teacher_id, invite_code（6位）, status
- **class_members**：id, class_id, student_id, student_name, student_number

**企业端表**：
- **enterprises**：id, name, short_name, industry, scale, contact_phone, contact_email, address, description, account_id
- **enterprise_mentors**：id, account_id, enterprise_id, real_name, title
- **job_positions**：id, enterprise_id, title, description, skill_requirements（JSON）, salary_range, status
- **enterprise_evaluations**：id, submission_id, mentor_id, enterprise_id, total_score, dimension_scores（JSON）, job_fit_score, strength_points, improvement_points, interview_suggest, comment, matched_job_id
- **interview_invitations**：id, enterprise_id, student_id, job_id, mentor_id, status, message, interview_time, created_at

### AI 评价流程

1. 学生分步上传文件 → `POST /api/upload-eval/`（multipart 表单：文件 + 任务要求 + 评价维度 + 学生 ID + 步骤证据）
2. `file_parser.py` 从 docx/pdf/图片中提取文本（图片使用硅基流动视觉 API OCR）
3. `code_analyzer.py` 对代码文件做静态分析（LOC/注释率/圈复杂度/TODO数）
4. `ai_evaluator.py` 将文本 + 维度 + 步骤证据发送给 DeepSeek API，使用结构化 Rubric 评分提示词（含 System Prompt + 分级评分标准 + Few-shot 示例）
5. `_parse_llm_json_safe()` 安全解析 LLM 返回的 JSON（容错处理各种格式异常）
6. 返回结果：各维度评分、总分、评语、步骤完整性、逻辑漏洞
7. 保存到 `submissions` 和 `evaluations` 表，返回给前端
8. 教师可通过 `POST /api/teacher/score` 复核并覆盖评分
9. 企业导师可通过 `/api/enterprise/evaluations` 查看成果物并给出企业终评

### 岗位匹配流程

1. 企业发布岗位（含技能要求 JSON）→ `POST /api/enterprise/jobs`
2. `job_matcher.py` 将学生实训成绩与岗位技能要求比对，计算匹配度
3. 企业端访问 `/app/enterprise/matching` 查看候选人排行榜
4. 点击「下载PDF报告」→ `GET /api/job-match/generate-report?fmt=pdf` 生成多页 PDF（封面 + 核心指标 + 图表 + 候选人排行 + 详细画像）
5. 企业可对候选人发送面试邀约 → `POST /api/enterprise/interviews`

### 报告导出

- **Excel 报告**（`report_generator.py` → `generate_excel`）：表头合并、色板应用、斑马纹、冻结窗格、条件格式、图表插入（柱状图/雷达图），分 Sheet 展示
- **PDF 报告**（`report_generator.py` → `generate_pdf`）：多页排版，封面 + 核心指标卡 + matplotlib 图表 + 候选人排行表 + 详细画像，自动注册系统中文字体（msyh.ttc）
- **文件名编码**：`Content-Disposition` 头使用 `filename*=UTF-8''<urlencode>` 格式，确保中文文件名跨浏览器正确显示

### 前端设计系统 v3（杂志/报告/纸张风 · 取自 frontend_ui_demo.html）

> 设计定位：**编辑杂志式 × 科技可视化** 的实训操作台。以米白纸张、绯红印章、衬线大标题为美学符号，用「试卷批改」的隐喻来传达「诚实、严肃、可溯源」的实训评价调性。UI 概念稿源文件：`frontend_ui_demo.html`。

---

#### 一、色彩体系（Paper & Crimson）

| Token | 色值 | 用途 |
|-------|------|------|
| `--ink` | `#0F1115` 深夜墨色 | 主文字、品牌方块、深色按钮 |
| `--ink-2` | `#1C1F26` | 二级文字、代码背景 |
| `--ink-3` | `#2A2F3A` | 辅助文字、边框线 |
| `--paper` | `#F6F3EC` 米白纸张 | 页面主背景 |
| `--paper-2` | `#EFEADE` 纸张阴面 | 卡片凹陷、输入框底、斑马行 |
| `--line` | `#D9D2C0` 纸边分割 | 全部边框线、分隔线、网格线 |
| `--accent` ★ | `#FF5A1F` 绯红印章 | 品牌主色：印章、按钮、进度条、hover 下划线、强调标签 |
| `--accent-soft` | `#FFE6DA` | 强调标签软底 |
| `--cobalt` | `#3D5AFE` 冷钴蓝 | AI/代码/链接/企业匹配/冷色对比 |
| `--cobalt-soft` | `#DCE2FF` | AI 卡片软底 |
| `--jade` | `#1DB955` 翡翠绿 | 通过/合格/绿色步骤 |
| `--jade-soft` | `#D3F4DF` | 绿色软底 |
| `--signal` | `#E63946` 信号红 | 失败/雷同/错误/警告缺口 |
| `--signal-soft` | `#FBD7DA` | 红色软底 |
| `--amber` | `#F4B740` 琥珀金 | 进行中/部分完成/黄色步骤 |
| `--amber-soft` | `#FBECC8` | 琥珀软底 |

> 主色使用原则：**绯红 (accent) = 品牌/印章/主按钮**，**冷钴蓝 = AI 与科技**，**翡翠绿 = 通过**，**琥珀金 = 进行中**，**信号红 = 错误**。严格保持五色系，不引入额外色。

---

#### 二、字体家族（衬线 × 科技 × 代码，三角）

```
--ff-display: "Playfair Display SC", "Noto Serif SC", serif
     用途：H1/H2 大标题、分数环数字、印章分数、品牌字 —— 衬线小型大写，传达「严肃报告」质感

--ff-sub: "Space Grotesk", "PingFang SC", system-ui, sans-serif
     用途：H3/H4、标签、导航、KPI 小字、UI 组件文字 —— 现代科技无衬线，做功能信息层

--ff-body: "Fraunces", "Noto Serif SC", Georgia, serif
     用途：正文段落、描述文字、任务描述 —— 人文衬线，提升长文阅读舒适度

--ff-mono: "JetBrains Mono", ui-monospace, Consolas, monospace
     用途：代码、任务编号、分数、ID、数据、Tag 编号 —— 等宽字体，工程数据层
```

Google Fonts 引入（`index.html` / 全局 CSS）：
```
Fraunces 300/400/600  +  italic 400
JetBrains Mono 400/600/700
Playfair Display SC 700/900
Space Grotesk 400/500/600/700
```

---

#### 三、视觉令牌（间距 / 圆角 / 阴影）

| Token | 值 | 说明 |
|-------|----|------|
| `--r-sm` | `6px` | 按钮内组件、Tag、小输入框圆角 |
| `--r-md` | `12px` | 输入框、KPI 卡、小部件 |
| `--r-lg` | `22px` | 主卡片（任务卡/登录卡/代码块/对比列） |
| `--r-xl` | `34px` | 大容器 |
| `--shadow-1` | `0 1px 2px rgba(0,0,0,.06), 0 1px 1px rgba(0,0,0,.04)` | 卡片常态阴影（纸面浮起 1 层） |
| `--shadow-2` | `0 10px 24px -10px rgba(0,0,0,.18), 0 2px 6px rgba(0,0,0,.06)` | Hover / 弹层（浮起 2 层） |
| `--shadow-3` | `0 30px 80px -24px rgba(0,0,0,.28), 0 6px 18px rgba(0,0,0,.08)` | 印章 / 强调卡（浮起 3 层） |
| `--page` | `1240px` | 最大内容宽度（报纸式窄栏布局，非满屏铺开） |

---

#### 四、背景叠层（纸张质感，必配）

页面全局 `body` 必须具备 4 层叠层（从上到下 z-index）：

```
Layer 4 (z-index:2): .shell 内容容器
Layer 3 (z-index:1): 颗粒噪点 SVG 叠层  opacity .045  mix-blend-mode:multiply
         → 模拟纸张颗粒感，使用内联 feTurbulence SVG（无外部资源）
Layer 2: 冷钴蓝 1200×600 径向渐变 (10% -10%) + 绯红 900×500 径向渐变 (95% 10%)
Layer 1: 24×24 px 交叉网格 (--line 色 1px) → 工程方格纸底纹
```

---

#### 五、关键装饰母题（Motif）

1. **绯红圆形印章 `.seal`**：大首页 hero 区/总评卡使用。直径约 260px，`conic-gradient` 从 `#FF8A5C → #FF5A1F → #B4360F`，内圈 1.5px 白色虚线，`rotate(-6deg)` + 两个金属图钉（`.seal-tack`）。这是本风格的精神符号。
2. **卡片顶部 3px 渐变条 `.card::after`**：`linear-gradient(90deg, #FF5A1F, transparent 60%)`，每张卡都有，制造从左向右褪色的「编辑报告贴纸」感。
3. **任务左侧 6px 色条 `.task::before`**：`.t-ok` 翡翠绿、`.t-do` 琥珀金、`.t-late` 信号红——即任务清单左边状态色条。
4. **圆形圆锥分数环 `.score-sm` / `.ring`**：`conic-gradient(var(--c) var(--p), #EFEADE 0)`，内嵌 `inset 0 0 0 6px white` 白底，作为所有分数可视化的唯一载体。
5. **导航锚点胶囊 `.chip`**：`<数字> 标题` 的黑色数字前缀，border-radius 999px，hover 反色。

---

#### 六、核心组件库（10 个必备组件）

| 组件 | 类名 | 规格 |
|------|------|------|
| 顶部毛玻璃导航 | `.topbar` + `.topbar-inner` | `backdrop-filter: blur(10px)`，`rgba(246,243,236,.72)`，下边框 1px `--line` |
| 品牌方块 + 字 | `.brand-mark` + `.brand-text` | 44×44 圆角 12 黑方块 + 右下角绯红径向光晕；品牌字为 `Playfair Display SC + Space Grotesk` 双层 |
| 主按钮 `.btn` | 主按钮 / 幽灵 / 强调 | 999px 胶囊，`14px` 字高，hover `translateY(-1px)` + `shadow-3`；强调版用 `--accent` |
| 通用卡片 `.card` | 登录 / KPI / 信息卡 | 白到半透明渐变背景 + `backdrop-filter:blur(6px)` + 顶部 3px 绯红条 + 圆角 22 + shadow-2 |
| 状态 Tag `.tag` | `.ok / .warn / .bad / .co / .ac` | 6 种状态 + 6 种软底色，999px 胶囊，11px JetBrains Mono |
| 任务卡 `.task` | `.t-ok / .t-do / .t-late` | 78px 编号列 + 主内容 + 右侧分数环 `.score-sm`；hover `translateY(-2px)` |
| 步骤时间线 `.steps-timeline` | `.step-row`（`.ok / .part / .bad`） | 左侧歪斜渐变主线（`skewX(-6deg)`）+ 16px 圆形状态节点 + 白内边阴影 |
| 代码块 `.code` | 附 `data-name` 文件名 | `--ink` 深色背景 + 白色内边距 18px，右上角 10px 大写文件名，语法色：`#FF8A5C/#6FC3FF/#D6FF3A/#6B7280/#FFB86B`（关键字/函数/字符串/注释/数字） |
| 三方对比列 `.col` | `.ai / .t / .e` | 三列同宽，顶部 4px 主题色条（钴蓝=AI/绯红=教师/翡翠=企业），48px Playfair Display 超大分数 |
| 岗位匹配卡 `.job` + `.match-pill` | 含亮点/缺口两栏 | 顶部 4px 钴蓝→绯红渐变条；右侧 92px 黑胶囊（分数 `--ff-display` 26px）；下方 `.two-col` 亮点(绿) + 缺口(红) |

---

#### 七、技能/标签三级配色（B1 岗位匹配用）

```
.sk-g (Good 已掌握):    --cobalt-soft   #172FA8 字   B8C4F5 边
.sk-m (Middle 部分):    --jade-soft     #0F6A33 字   B8E7C7 边
.sk-b (Bad 缺口):       --amber-soft    #7C5300 字   EED48E 边
```

---

#### 八、布局（报纸式 1.55 : 1 双栏）

所有 `section` 采用固定 1.55 比 1 双栏：
```css
grid-template-columns: 1.55fr 1fr;
gap: 44px;
max-width: 1240px;
padding: 56px 28px;
```

响应式：
- `≤ 980px`：双栏改单栏；三方对比列改 1 列；圆环 4 个变 2 个；KPI 变 2 列。

---

#### 九、进场动画（Scroll Reveal）

`.reveal` 基类：
```
opacity 0 → 1; translateY(14px) → 0;
transition .6s ease;
```
滚动到视窗内时加 `.on`，整体是「严肃页面，滚动柔和浮现」的杂志质感，**不做弹跳/夸张动效**。

---

#### 十、设计反模式（不要做）

1. ❌ 不要满屏铺开（max-width 永远 1240px，维持报纸式窄栏阅读舒适度）
2. ❌ 不要 Material/Element Plus 的默认大蓝大绿阴影（严格替换为 `--paper/--line/--accent` 五色体系）
3. ❌ 不要用纯黑纯白（所有深/浅色都有纸张/墨色的色温偏移）
4. ❌ 不要 emoji 堆砌（唯一图标符号是：印章图钉 ✓ ✕、SVG 线条图标）
5. ❌ 不要深底文字浅色（代码块唯一例外，其他页面 100% 纸张底色）

### 关键模式

- **认证**：前端将 `token` 和 `user` JSON 存储在 localStorage 中。后端通过 `auth_deps.py` 提供 `require_login` / `require_teacher` / `require_enterprise` 等依赖注入，按角色鉴权。登录失败统一返回 401 + "用户名或密码错误"，前端 catch 分支正确处理并弹出 ElMessage 提示（不暴露控制台红色报错）。
- **数据隔离**：企业端所有查询均过滤 `enterprise_id`（通过 `require_enterprise` 依赖获取当前企业）；教师端按 `teacher_id` / 班级归属过滤。确保 A 企业/教师无法查看 B 的数据。
- **角色强隔离登录**：前端三角色（学生/教师/企业）各自独立表单，登录时带 `expected_role` 参数，后端校验账号角色匹配，不匹配统一返回 401（不暴露"此账号属XX端"信息）。
- **评价标准配置**：同时存储于后端数据库（`evaluation_criteria` 表）和前端 localStorage（`criteria_config`、`current_task_criteria`）。后端是任务的真值来源；localStorage 作为缓存/默认值。
- **API 地址**：定义在 `frontend/src/config.ts` 的 `API_BASE` 常量中，部署时修改此值。
- **文件上传**：存储在 `backend/uploads/`，通过 FastAPI `StaticFiles` 挂载在 `/uploads` 路径下对外提供。
- **文件下载**：通过 axios 请求二进制流（`responseType: 'blob'`），解析 `Content-Disposition` 头获取文件名，使用 `Blob` + `URL.createObjectURL` 实现客户端下载。下载接口支持 `token` 查询参数（用于 `<a>` 标签直接下载场景）。
- **报告**：服务端使用 openpyxl（Excel）和 fpdf2（PDF）生成，以文件下载形式返回。PDF 报告自动扫描注册系统中文字体，生成后清理临时图片文件。

## 演示数据

项目提供完整的演示数据，位于 `演示数据/` 目录：

| 文件 | 说明 |
|------|------|
| `demo_seed.sql` | SQL 种子文件（9 张简单表：账号/班级/任务/企业/岗位/面试邀约等） |
| `_apply_demo_seed_ALL.py` | 一键导入脚本（自动识别 MySQL/SQLite，用 ORM 写入 JSON 复杂表，幂等可重复执行） |
| `演示脚本.md` | 比赛演示流程文档（教师端 + 企业端完整演示步骤） |
| `业务案例_两个.md` | 两个业务案例（教学场景 + 企业招聘场景） |
| `README.md` | 演示数据使用说明 |

## 重要注意事项

- 后端 `ai_evaluator.py` 中包含硬编码的 DeepSeek 和硅基流动 API 密钥——生产环境中应迁移至环境变量。
- 启动后端前必须确保 MySQL 已运行且 `eval_system` 数据库已存在。
- 未使用数据库迁移系统（如 Alembic）——修改表结构需要手动 ALTER TABLE 或删表重建。
- `tasks` 和 `submissions` 表的 `class_id` 列为 `String(500)` 类型，存储逗号分隔的 ID（如 "1,3,5"），不是真正的外键关联。
- 前端 PWA 通过 `vite-plugin-pwa` 在 `vite.config.ts` 中配置。
- 演示数据导入前需确保后端表结构已创建（首次启动后端会自动建表）。

## 近期更新日志

### 2026-08-05（比赛版本）

**Bug 修复**：
- 修复登录错误密码时前端报 401 控制台红色错误 → 统一显示「用户名或密码错误」友好提示
- 修复企业端数据隔离：企业 A 的成果物/评价/岗位只能企业 A 查看，企业 B 无法访问
- 修复教师端数据隔离：教师 A 的班级/任务/提交只能教师 A 查看
- 修复企业评价页面下载提交资料「缺少 Token」错误 → 改用 axios + Authorization 头下载
- 修复 Excel 报表 MergedCell 只读错误 → 先按列分别合并再写入
- 修复 PDF 报告 Content-Disposition 中文编码错误 → filename 字段分离 ASCII 名与 UTF-8 编码名

**功能优化**：
- 企业端岗位匹配「下载文字报告」→ 升级为生成带格式排版的多页 PDF 报告（封面/核心指标/图表/候选人排行/详细画像）
- 实训报告 Excel 表格美化：表头合并、色板、斑马纹、冻结窗格、条件格式、图表插入
- 实训报告 PDF 文件美化：多页排版、中文字体注册、matplotlib 图表内嵌
- AI 评分准确性提升：升级 Prompt（System Prompt + 分级 Rubric + Few-shot 示例）、加固 JSON 输出解析（`_parse_llm_json_safe`）、代码/文档/UI 维度改为 LLM 真评
- 登录页面 UI 优化：登录按钮 X 轴居中、立即注册按钮橙色渐变背景板加大
- 消息通知窗口图标位置修复

**新增**：
- 演示数据一键导入脚本（`_apply_demo_seed_ALL.py`）：自动识别数据库引擎，ORM 写入 JSON 复杂表，幂等可重复执行
- 演示流程文档（`演示脚本.md`）+ 业务案例文档（`业务案例_两个.md`）
- 自主设计任务两方综合评分详情弹窗：隐藏企业评价模块，AI 详细评价和教师评价详情平分空间
