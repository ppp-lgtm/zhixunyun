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
