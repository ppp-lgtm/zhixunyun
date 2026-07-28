# CLAUDE.md

此文件为 Claude Code (claude.ai/code) 在此仓库中工作时提供指引。

## 项目概述

知训云 —— 一款基于 AI 的软件实训教学智能评价系统。教师创建班级、发布任务，学生提交实训成果（docx/pdf/图片），AI 自动按可配置维度评分。支持教师人工复核、数据统计分析、评价报告导出。

## 技术栈

| 层级 | 技术 |
|-------|-----------|
| 前端 | Vue 3 + TypeScript + Vite + Tailwind CSS 3 + Element Plus |
| 后端 | Python FastAPI + SQLAlchemy ORM + MySQL |
| AI | DeepSeek API（文本评价）+ 硅基流动 API（图片识别） |
| 认证 | JWT (HS256) + SHA256 加盐密码哈希 |
| 图表 | ECharts（通过 vue-echarts 封装） |
| 图标 | Iconify（`mdi:` 前缀 = Material Design Icons） |

## 常用命令

### 后端 (Python FastAPI)

```bash
cd backend
# 首次：创建虚拟环境并安装依赖
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     #麒麟
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

## 架构

### 后端结构

```
backend/app/
├── main.py              # FastAPI 应用入口，CORS，全局异常处理，路由注册
├── config.py            # DATABASE_URL
├── models/
│   ├── database.py      # SQLAlchemy 引擎、SessionLocal、Base、get_db()
│   ├── tables.py        # User, Task, Submission, Evaluation, EvaluationCriteria
│   └── class_models.py  # Class, ClassMember
├── routers/             # 每个功能域一个文件
│   ├── auth_router.py   # POST /api/auth/login, /api/auth/register
│   ├── upload_eval.py   # POST /api/upload-eval/（上传+评价主流程）
│   ├── task_manage.py   # /api/tasks/ 增删改查，AI 生成任务要求端点
│   ├── class_router.py  # /api/classes/ 增删改查，邀请码加入班级
│   ├── statistics.py    # GET /api/statistics/*（概览、图表、岗位匹配、教学建议）
│   ├── teacher_score.py # POST /api/teacher/score
│   ├── report.py        # POST /api/report/excel, /api/report/pdf
│   ├── criteria.py      # /api/criteria/ 增删改查
│   ├── evaluate.py      # 旧版评价端点
│   ├── upload.py         # 旧版上传端点
│   ├── user_profile.py  # GET/PUT /api/user/profile/，头像上传，修改密码
│   ├── notifications.py # GET /api/notifications/
│   └── search.py        # GET /api/search/
├── services/
│   ├── file_parser.py   # 解析 docx/pdf/图片文件为文本
│   └── report_generator.py  # Excel/PDF 报告生成（openpyxl, fpdf2）
└── utils/
    ├── ai_evaluator.py  # DeepSeek + 硅基流动客户端，evaluate() 函数
    └── auth.py          # JWT 创建/解码，密码加盐哈希/验证
```

**API 响应约定**：所有端点返回 `{"success": bool, "data": ..., "error"/"detail": ...}` 格式。`main.py` 中的全局异常处理器捕获未处理异常并以此格式返回 500。

### 前端结构

```
frontend/src/
├── main.ts              # 应用启动：Pinia、Router、Element Plus、ECharts、Iconify
├── App.vue              # 根组件：<router-view />
├── config.ts            # API_BASE = 'http://127.0.0.1:8000'
├── router/index.ts      # 路由定义：/ → LandingPage，/login → Login，/app/* → MainLayout 子路由
├── layout/
│   └── MainLayout.vue   # 深色侧边栏 + 顶部导航 + <router-view> 外壳
├── views/               # 15 个页面组件（见下方路由表）
├── styles/
│   └── global.css       # Tailwind 指令、自定义组件类、Element Plus 全局覆盖
└── img/
    └── logo.png
```

### 路由表

| 路径 | 组件 | 角色 | 说明 |
|------|-----------|------|-------------|
| `/` | LandingPage | 公开 | 官方首页 |
| `/login` | Login | 公开 | 登录 + 注册弹窗 |
| `/app` | Home | 两者 | 首页仪表盘（按角色展示不同数据） |
| `/app/task-manage` | TaskManage | 教师 | 创建/管理任务，查看提交情况 |
| `/app/class-manage` | ClassManage | 教师 | 创建/编辑/删除班级 |
| `/app/class-scores` | ClassScores | 教师 | 班级成绩排名表 |
| `/app/criteria` | Criteria | 教师 | 配置评价维度与权重 |
| `/app/statistics` | Statistics | 两者 | 图表、AI 教学建议、岗位匹配 |
| `/app/student-tasks` | StudentTasks | 学生 | 查看并提交任务 |
| `/app/my-classes` | MyClasses | 学生 | 加入/查看班级，班级排名 |
| `/app/my-scores` | MyScores | 学生 | 个人成绩记录与成长报告 |
| `/app/upload` | Upload | 学生 | 上传文件进行评价 |
| `/app/result/latest` | Result | 两者 | 评价详情（AI评分/教师评分/智能核查三个标签页） |
| `/app/profile` | Profile | 两者 | 编辑资料、修改密码、头像上传 |

### 数据库表

- **users**：id, username, password_hash, role（teacher/student）, real_name, user_number, email, avatar
- **tasks**：id, title, requirements, criteria（逗号分隔）, criteria_weights, class_id, total_score, deadline, template_path
- **submissions**：id, task_id, student_id, filename, file_path, content, class_id
- **evaluations**：id, submission_id, evaluator_type（ai/teacher）, total_score, dimension_scores（JSON）, comment, step_completeness（JSON）, logic_issues（JSON）
- **evaluation_criteria**：id, task_id, name, weight, description
- **classes**：id, name, grade, major, semester, course_name, teacher_id, invite_code（6位）, status
- **class_members**：id, class_id, student_id, student_name, student_number

### AI 评价流程

1. 学生上传文件 → `POST /api/upload-eval/`（multipart 表单：文件 + 任务要求 + 评价维度 + 学生 ID）
2. `file_parser.py` 从 docx/pdf/图片中提取文本（图片使用硅基流动视觉 API）
3. `ai_evaluator.py` 将文本 + 维度发送给 DeepSeek API，使用结构化 JSON 提示词
4. 返回结果解析为各维度评分、总分、评语、步骤完整性、逻辑漏洞
5. 保存到 `submissions` 和 `evaluations` 表，返回给前端
6. 教师可通过 `POST /api/teacher/score` 复核并覆盖评分

### 前端设计系统

- **色彩体系**：主色 = 靛蓝 (#4F46E5)，强调色 = 琥珀 (#F59E0B)，表面色 = 板岩灰阶。定义在 `tailwind.config.js`，含 50–900 色阶。
- **组件类**（定义于 `global.css`）：`.card`、`.card-hover`、`.btn-primary`、`.btn-accent`、`.btn-ghost`、`.stat-card`、`.badge-*`、`.glass`
- **Element Plus** 全局覆盖：统一圆角、阴影和焦点环样式。
- **页面过渡**：`fade-slide`（translateX + scale）在 MainLayout 的 `<router-view>` 中生效。
- **字体**：Plus Jakarta Sans + Noto Sans SC（中文），通过 Google Fonts 在 `global.css` 中加载。

### 关键模式

- **认证**：前端将 `token` 和 `user` JSON 存储在 localStorage 中。无请求拦截器——每个请求自行读取 localStorage。后端认证按端点独立实现（非中间件强制）。
- **评价标准配置**：同时存储于后端数据库（`evaluation_criteria` 表）和前端 localStorage（`criteria_config`、`current_task_criteria`）。后端是任务的真值来源；localStorage 作为缓存/默认值。
- **API 地址**：定义在 `frontend/src/config.ts` 的 `API_BASE` 常量中，部署时修改此值。
- **文件上传**：存储在 `backend/uploads/`，通过 FastAPI `StaticFiles` 挂载在 `/uploads` 路径下对外提供。
- **报告**：服务端使用 openpyxl（Excel）和 fpdf2（PDF）生成，以文件下载形式返回。

## 重要注意事项

- 后端 `ai_evaluator.py` 中包含硬编码的 DeepSeek 和硅基流动 API 密钥——生产环境中应迁移至环境变量。
- 启动后端前必须确保 MySQL 已运行且 `eval_system` 数据库已存在。
- 未使用数据库迁移系统（如 Alembic）——修改表结构需要手动 ALTER TABLE 或删表重建。
- `tasks` 和 `submissions` 表的 `class_id` 列为 `String(500)` 类型，存储逗号分隔的 ID（如 "1,3,5"），不是真正的外键关联。
- 前端 PWA 通过 `vite-plugin-pwa` 在 `vite.config.ts` 中配置。
