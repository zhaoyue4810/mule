# 心测 XinCe 技术落地方案（终稿）

> 说明：本文档继续保留为目标技术方案参考，不再作为项目实时状态来源。当前真实完成度、验证结果与优先级请以 `STATUS.md`、`PLAN.md`、`PROJECT.md` 为准。

> 适用对象：架构师、前后端开发、测试、产品、AI 工程人员、大模型编码代理
>
> 本文档不是概念性架构图，而是可执行的研发说明书。开发人员或大模型应能基于本文档，按阶段逐步完成整个项目的开发。

| 项目 | 内容 |
|------|------|
| 项目名称 | 心测 XinCe — 灵魂手册 |
| 文档版本 | v3.0（FastAPI + YAML 配置化终稿） |
| 日期 | 2026-03-13 |
| 架构模式 | 前后端分离（微信小程序 + Web H5 + Python 后端） |
| 后端框架 | FastAPI + SQLAlchemy + Celery |
| 配置策略 | 题型定义 / 试题内容 / 交互提示 全部 YAML 配置驱动 |
| AI 能力 | 阿里云百炼 + 火山引擎大模型 API |

---

## 目录

1. [产品分析与迁移原则](#1-产品分析与迁移原则)
2. [最终产品形态](#2-最终产品形态)
3. [后端技术选型：为什么选 FastAPI](#3-后端技术选型为什么选-fastapi)
4. [总体技术架构](#4-总体技术架构)
5. [工程目录结构](#5-工程目录结构)
6. [YAML 配置驱动设计](#6-yaml-配置驱动设计)
7. [后端领域设计（FastAPI）](#7-后端领域设计fastapi)
8. [数据库设计](#8-数据库设计)
9. [RESTful API 接口设计](#9-restful-api-接口设计)
10. [15 种题型组件化落地](#10-15-种题型组件化落地)
11. [测试内容数据模型与版本策略](#11-测试内容数据模型与版本策略)
12. [docx / html 导入方案](#12-docx--html-导入方案)
13. [前端架构设计](#13-前端架构设计)
14. [AI 大模型集成方案](#14-ai-大模型集成方案)
15. [报告与评分引擎](#15-报告与评分引擎)
16. [AI 在测试与 QA 中的应用](#16-ai-在测试与-qa-中的应用)
17. [管理后台设计](#17-管理后台设计)
18. [安全、隐私与合规](#18-安全隐私与合规)
19. [性能与可观测性](#19-性能与可观测性)
20. [部署架构](#20-部署架构)
21. [自动化测试策略](#21-自动化测试策略)
22. [开发实施路线图](#22-开发实施路线图)
23. [大模型执行指导](#23-大模型执行指导)
24. [风险与应对](#24-风险与应对)
25. [附录](#25-附录)

---

## 1. 产品分析与迁移原则

### 1.1 产品定位

心测（XinCe）是一款面向 18-35 岁年轻用户的移动端心理测试应用，核心理念是将专业心理学测评与趣味交互体验结合。产品哲学为"温暖专业主义"——在专业心理量表和纯娱乐星座之间找到平衡。

### 1.2 现有原型分析

当前原型为纯前端单文件 HTML 应用（约 4500 行），已包含完整业务闭环：

| 模块 | 内容 |
|------|------|
| 测试系统 | 8 套完整测试（bigfive/mbti/ennea/love/bff/career/couple/work），15 种交互类型 |
| 灵魂画像 | 5 维度雷达图（情感洞察力/理性思维/社交魅力/创造力/内心力量），4 等级进阶 |
| 双人匹配 | 邀请链接机制 + 对比雷达图 + 契合度算分 |
| 勋章系统 | 16 枚个人勋章 + 10 枚双人勋章，铜/银/金/钻四级 |
| 运势日历 | GitHub 风格热力图，月/年视图，手动心情记录 |
| 吉祥物 | 小测精灵，7 种表情状态，微反馈系统，记忆系统 |
| 七大 v3.0 功能 | 每日灵魂一问、音效触感、分享卡片、人设名片、小测记忆、时光胶囊、灵魂碎片 |

原型本地持久化键：`xc_state`、`xc_calendar`、`xc_memory`、`xc_notif_prefs`、`xc_priv_prefs`、`xc_ob`

### 1.3 工程化迁移原则

从架构视角看，这个项目不是"把 HTML 拆文件"，而是把"单文件展示原型"迁移为"数据驱动的产品平台"。

**五项核心原则：**

1. **保留产品体验，不保留单文件实现方式。** `index.html` 视为高保真原型与初始化数据源，不直接复用 DOM 代码。
2. **`xince-design-doc.docx` 视为产品规则与设计规范来源。**
3. **测试内容、报告模板、勋章规则、画像规则全部从前端代码中抽离到 YAML 配置与后端数据库。** 所有数据必须结构化存储、版本化管理、可回滚。
4. **小程序优先。** 如果某个交互在小程序和 H5 的实现成本不同，以小程序可落地版本为基准，再给 H5 增强效果。
5. **先单体分层，后续再考虑微服务。** 首期采用"单体应用 + 清晰业务模块 + 可拆边界"的方式。

### 1.4 localStorage 迁移映射

| 原型键 | 新方案归属 |
|--------|-----------|
| `xc_state` | 拆分为 `xc_user` + `xc_test_record` + 客户端偏好缓存 |
| `xc_calendar` | 后端表 `xc_calendar_entry` |
| `xc_memory` | 后端表 `xc_user_memory` |
| `xc_notif_prefs` | 后端表 `xc_user_setting` |
| `xc_priv_prefs` | 后端表 `xc_user_setting` |
| `xc_ob` | 后端字段 `xc_user.onboarding_completed` |

---

## 2. 最终产品形态

### 2.1 端侧规划

| 端 | 技术栈 | 定位 |
|----|--------|------|
| 微信小程序 | uni-app + Vue 3 + TypeScript + Pinia | 主产品，承担核心用户增长、测试、报告、分享、匹配 |
| H5 Web 应用 | 与小程序共用 uni-app 项目编译 | 分享落地页、活动页、PC 预览、调试验收 |
| 管理后台 | Vue 3 + Element Plus + SQLAdmin | 内容导入、题库维护、审核、运营配置、AI 任务审查 |

选择 uni-app 的原因：
1. 小程序优先时，uni-app 在微信生态与 H5 双端交付上成本最低，一套代码两端输出。
2. 当前原型大量是移动端交互，适合统一做移动优先组件体系。
3. 后台也是 Vue 体系，团队上下文统一。

### 2.2 分阶段产品范围

**P0：可上线 MVP**
- 微信登录 + Onboarding
- 测试列表 / 详情 / 答题 / 报告
- 文档导入与题库管理
- 基础画像 + AI 结果分析
- 基础分享 + 基础管理后台

**P1：增强体验**
- 双人匹配 + 匹配报告
- 勋章系统（16 + 10 枚）
- 日历热力图
- 小测 AI 伴随
- 通知、设置、个人中心强化

**P2：高差异化**
- 小测记忆系统 + 时光胶囊 + 灵魂碎片
- 人设名片 + 每日灵魂一问
- AI 测试分析工作台

---

## 3. 后端技术选型：为什么选 FastAPI

### 3.1 候选框架对比

| 维度 | FastAPI | Django + DRF | Flask |
|------|---------|-------------|-------|
| 异步支持 | 原生 async/await，天然适配 AI 流式调用 | Django 4.1+ 部分支持，DRF 尚未完全异步 | 需 Quart 或额外适配 |
| 学习曲线 | 低，类型提示即文档 | 中高，ORM/Admin/中间件概念多 | 低，但需自行拼装 |
| API 文档 | 自动生成 OpenAPI (Swagger/ReDoc) | 需 drf-spectacular 配置 | 需 flask-apispec |
| 性能 | 基于 Starlette + uvicorn，Python 异步框架中最快一档 | WSGI 为主，ASGI 尚不成熟 | WSGI，单线程 |
| ORM | 自由选择（推荐 SQLAlchemy 2.0 异步） | 内置 Django ORM，成熟但异步支持弱 | 自由选择 |
| Admin 后台 | SQLAdmin（第三方，够用） | 内置 Django Admin，功能强大 | Flask-Admin |
| 类型安全 | Pydantic 校验请求/响应，编译期可查错 | Serializer 运行时校验 | 手动 |
| 生态成熟度 | 高，GitHub 80k+ stars，活跃维护 | 最高，20 年历史 | 高 |
| AI/LLM 集成 | httpx 异步 + SSE 原生支持，LangChain/OpenAI SDK 均 Python 优先 | 可用但异步链路断裂多 | 可用 |

### 3.2 选择 FastAPI 的决策依据

1. **AI 场景需要原生异步。** 本项目大量使用大模型 API（百炼/火山），测试结果分析、微反馈、流式输出都依赖 async I/O。FastAPI 的 async/await 是一等公民，不需要额外适配层。

2. **自动 API 文档降低前后端协作成本。** FastAPI 基于类型提示自动生成 OpenAPI 文档，前端和大模型代理可以直接读 Swagger 理解接口契约，减少沟通成本。

3. **Pydantic 校验前移。** 请求/响应模型用 Pydantic 定义，类型错误在入口即拦截，减少运行时 bug。与 TypeScript 前端的类型理念一致。

4. **轻量启动，不过度设计。** 相比 Django 全家桶，FastAPI 只引入需要的组件。首期项目规模不需要 Django ORM 的复杂迁移体系和内置 Admin。SQLAlchemy + Alembic 提供同等能力且更灵活。

5. **部署简单。** `uvicorn app.main:app` 一行启动，Docker 镜像小，资源占用低。对于 2C4G 的初期服务器配置友好。

### 3.3 不选 Django 的原因

Django + DRF 是成熟方案，但在本项目场景下存在两个实际问题：
- **异步链路断裂。** Django ORM 不支持 async，在 async view 中调用 ORM 需要 `sync_to_async` 包装，AI 流式接口的代码会变得复杂。
- **内置 Admin 对本项目价值有限。** 本项目管理后台需求是内容审核、导入预览、AI 监控等定制功能，Django Admin 的默认 CRUD 界面帮助不大，最终仍需自建前端。

### 3.4 核心 Python 依赖清单

```
# pyproject.toml / requirements.txt
fastapi>=0.115
uvicorn[standard]>=0.30
sqlalchemy[asyncio]>=2.0
asyncpg>=0.29               # PostgreSQL 异步驱动 (如用 MySQL 则换 aiomysql)
alembic>=1.13                # 数据库迁移
pydantic>=2.5
pydantic-settings>=2.1
python-jose[cryptography]    # JWT
passlib[bcrypt]              # 密码哈希
httpx>=0.27                  # 异步 HTTP 客户端 (调用 AI API)
redis[hiredis]>=5.0          # Redis 异步客户端
celery[redis]>=5.3           # 异步任务队列
python-docx>=1.1             # docx 解析
beautifulsoup4>=4.12         # html 解析
pyyaml>=6.0                  # YAML 配置加载
watchfiles>=0.21             # YAML 热重载 (开发环境)
oss2>=2.18                   # 阿里云 OSS SDK
slowapi>=0.1                 # 接口限流
loguru>=0.7                  # 结构化日志
sqladmin>=0.17               # SQLAlchemy Admin 面板
python-multipart             # 文件上传支持
pytest>=8.0                  # 测试框架
pytest-asyncio               # 异步测试
locust>=2.20                 # 压测 (可选)
```

---

## 4. 总体技术架构

### 4.1 架构图

```
┌──────────────────────────────────────────────────────────────┐
│                        客户端层                               │
│  ┌──────────────────────────────────────────────────┐        │
│  │      uni-app + Vue 3 + TypeScript + Pinia        │        │
│  │  ┌───────────────┐    ┌───────────────┐          │        │
│  │  │ 微信小程序(主端)│    │  H5 Web(副端)  │          │        │
│  │  └───────┬───────┘    └───────┬───────┘          │        │
│  │          └────────┬───────────┘                   │        │
│  │                   │                               │        │
│  │        ┌──────────▼──────────┐                   │        │
│  │        │   shared-logic 层    │                   │        │
│  │        │ (stores/services/    │                   │        │
│  │        │  utils/types)       │                   │        │
│  │        └─────────────────────┘                   │        │
│  └──────────────────────────────────────────────────┘        │
│                                                               │
│  ┌──────────────────────────────┐                            │
│  │  管理后台 (Vue3+ElementPlus) │                            │
│  │  + SQLAdmin (数据管理)       │                            │
│  └──────────────┬───────────────┘                            │
└─────────────────┼────────────────────────────────────────────┘
                  │ HTTPS
┌─────────────────▼────────────────────────────────────────────┐
│                Nginx (反向代理 + SSL + 限流)                   │
└─────────────────┬────────────────────────────────────────────┘
                  │
┌─────────────────▼────────────────────────────────────────────┐
│              FastAPI (Python 3.11+ / uvicorn)                 │
│  ┌──────────┬──────────┬──────────┬──────────┬────────────┐  │
│  │ app.auth │ app.     │ app.     │ app.     │ app.       │  │
│  │          │ content  │ test     │ report   │ match      │  │
│  ├──────────┼──────────┼──────────┼──────────┼────────────┤  │
│  │ app.     │ app.     │ app.     │ app.     │ app.       │  │
│  │ soul     │ badge    │ calendar │ importing│ ai         │  │
│  ├──────────┼──────────┼──────────┴──────────┴────────────┤  │
│  │ app.     │ app.     │ app.ops                          │  │
│  │ user     │ qa       │(运营位/Banner/推荐)               │  │
│  └──────────┴──────────┴─────────────────────────────────┘  │
│                                                               │
│  ┌──────────────────────────────────────────────┐            │
│  │          YAML 配置层 (server/config/)         │            │
│  │  题型定义 / 试题内容 / 交互提示 / 勋章规则      │            │
│  └──────────────────────────────────────────────┘            │
└─────────────────┬────────────────────────────────────────────┘
                  │
┌─────────────────▼────────────────────────────────────────────┐
│                     数据 & AI 层                               │
│  ┌────────┐ ┌───────┐ ┌──────────┐ ┌─────────────────────┐  │
│  │MySQL   │ │Redis  │ │阿里云 OSS │ │   AI Gateway         │  │
│  │8.0+    │ │7.0+   │ │(图片/文件)│ │ ┌───────┐ ┌───────┐ │  │
│  │(或PG16)│ │       │ │          │ │ │百炼   │ │火山   │ │  │
│  │        │ │       │ │          │ │ │(主)   │ │(备)   │ │  │
│  └────────┘ └───────┘ └──────────┘ │ └───────┘ └───────┘ │  │
│                                     └─────────────────────┘  │
│  ┌──────────────────┐                                        │
│  │ Celery + Redis /  │                                        │
│  │ 异步任务队列       │                                        │
│  └──────────────────┘                                        │
└──────────────────────────────────────────────────────────────┘
```

### 4.2 技术选型总表

| 层级 | 技术 | 版本 | 说明 |
|------|------|------|------|
| 前端框架 | uni-app + Vue 3 | 3.0+ / HBuilderX | 一套代码编译小程序 + H5 |
| 前端语言 | TypeScript | 5.x | 类型安全，前后端共享类型 |
| 状态管理 | Pinia | 2.x | 按业务域拆 store |
| 图表 | ECharts | 5.4+ | 雷达图/柱状图/热力图 |
| 后端框架 | FastAPI | 0.115+ | Python 高性能异步 Web 框架，原生 OpenAPI 文档 |
| ORM | SQLAlchemy 2.0 + Alembic | 2.0+ | 异步 ORM + 数据库迁移 |
| 数据库 | MySQL 8.0+ 或 PostgreSQL 16+ | - | 推荐 PostgreSQL，JSON 支持更好 |
| 缓存 | Redis | 7.0+ | 会话/排行榜/限流/AI缓存 |
| 对象存储 | 阿里云 OSS | - | 图片/分享卡片/导入文件 |
| AI - 阿里云 | 百炼（DashScope） | - | qwen-max / qwen-plus |
| AI - 火山引擎 | 豆包（方舟） | - | doubao-pro-32k / doubao-lite |
| 任务调度 | Celery + Redis | - | 异步任务：AI 分析/胶囊到期/定时聚合 |
| 管理后台 | SQLAdmin + Vue 3 + Element Plus | - | SQLAdmin 数据管理 + 自定义前端 |
| 文档解析 | python-docx + BeautifulSoup4 | - | docx/html 导入 |
| 配置管理 | PyYAML + watchfiles | - | YAML 配置驱动题型/试题/提示 |

### 4.3 架构原则

1. 前后端分离，用户态 API (`/api/app/*`) 与后台管理 API (`/api/admin/*`) 分离。
2. AI 调用不散落在业务代码中，统一经 `AI Gateway` 模块。
3. **测试内容全部 YAML 配置化**：题型定义、每套试题的题目与选项、答题过程中的交互提示，均通过 YAML 文件声明，运行时加载到内存并同步到数据库。
4. 报告生成与 AI 分析采用异步任务，不阻塞主提交流程。
5. 不一开始做微服务——需求频繁变化阶段，单体仓库更利于端到端交付。

---

## 5. 工程目录结构

```text
xince/
├── docs/
│   ├── implementation_plan.md          # 本文档
│   ├── api/                            # API 文档
│   └── prompts/                        # AI Prompt 模板（版本化）
├── apps/
│   ├── xince-app/                      # uni-app 主项目（小程序 + H5）
│   │   ├── src/
│   │   │   ├── pages/                  # 页面
│   │   │   │   ├── index/              # 首页 (tabBar)
│   │   │   │   ├── discover/           # 发现页 (tabBar)
│   │   │   │   ├── matchhub/           # 匹配中心 (tabBar)
│   │   │   │   ├── profile/            # 个人中心 (tabBar)
│   │   │   │   ├── test-detail/
│   │   │   │   ├── test-taking/        # 答题页（核心）
│   │   │   │   ├── report/
│   │   │   │   ├── match-report/
│   │   │   │   ├── soul/
│   │   │   │   ├── persona-card/
│   │   │   │   ├── calendar/
│   │   │   │   ├── search/
│   │   │   │   ├── edit-profile/
│   │   │   │   ├── settings/
│   │   │   │   ├── notifications/
│   │   │   │   └── onboarding/
│   │   │   ├── components/
│   │   │   │   ├── xc-mascot/          # 小测吉祥物
│   │   │   │   ├── interaction/        # 15 种交互组件
│   │   │   │   │   ├── SwipeCard.vue
│   │   │   │   │   ├── BubbleSelect.vue
│   │   │   │   │   ├── EmojiSlider.vue
│   │   │   │   │   ├── VersusPick.vue
│   │   │   │   │   ├── StarRate.vue
│   │   │   │   │   ├── ScenarioPick.vue
│   │   │   │   │   ├── TarotCards.vue
│   │   │   │   │   ├── HotCold.vue
│   │   │   │   │   ├── Constellation.vue
│   │   │   │   │   ├── FortuneWheel.vue
│   │   │   │   │   ├── ScratchCard.vue
│   │   │   │   │   ├── RankDrag.vue
│   │   │   │   │   ├── PressureHold.vue
│   │   │   │   │   ├── Plot2d.vue
│   │   │   │   │   └── ColorPick.vue
│   │   │   │   ├── soul-card/
│   │   │   │   ├── badge-item/
│   │   │   │   ├── calendar-mini/
│   │   │   │   ├── share-card/
│   │   │   │   └── bottom-sheet/
│   │   │   ├── stores/                 # Pinia 状态管理
│   │   │   │   ├── auth.ts
│   │   │   │   ├── user.ts
│   │   │   │   ├── test.ts
│   │   │   │   ├── report.ts
│   │   │   │   ├── soul.ts
│   │   │   │   ├── match.ts
│   │   │   │   ├── badge.ts
│   │   │   │   ├── calendar.ts
│   │   │   │   └── config.ts
│   │   │   ├── services/               # API 请求层
│   │   │   ├── utils/
│   │   │   └── styles/
│   │   │       └── variables.scss      # 设计系统变量
│   │   ├── manifest.json
│   │   └── pages.json
│   └── xince-admin/                    # 管理后台
├── server/                                # Python 后端
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                        # FastAPI 应用入口
│   │   ├── core/                          # 核心基础设施
│   │   │   ├── config.py                  # Pydantic Settings（读取 .env）
│   │   │   ├── database.py                # SQLAlchemy async engine & session
│   │   │   ├── security.py                # JWT 签发/校验、密码哈希
│   │   │   ├── deps.py                    # 全局依赖（get_db, get_current_user）
│   │   │   ├── redis.py                   # Redis 连接池
│   │   │   └── yaml_loader.py             # YAML 配置加载与热重载
│   │   ├── config/                        # ★ YAML 配置文件目录
│   │   │   ├── interaction_types.yaml     # 15 种题型定义
│   │   │   ├── tests/                     # 每套测试的 YAML
│   │   │   │   ├── bigfive.yaml
│   │   │   │   ├── mbti.yaml
│   │   │   │   ├── ennea.yaml
│   │   │   │   ├── love.yaml
│   │   │   │   ├── bff.yaml
│   │   │   │   ├── career.yaml
│   │   │   │   ├── couple.yaml
│   │   │   │   └── work.yaml
│   │   │   ├── prompts/                   # 交互提示与微反馈模板
│   │   │   │   ├── micro_feedback.yaml
│   │   │   │   ├── mascot_responses.yaml
│   │   │   │   └── encouragement.yaml
│   │   │   ├── badges.yaml                # 勋章定义与规则
│   │   │   ├── soul_fragments.yaml        # 灵魂碎片定义
│   │   │   └── daily_questions.yaml       # 每日灵魂一问题库
│   │   ├── models/                        # SQLAlchemy ORM 模型
│   │   │   ├── user.py
│   │   │   ├── test.py
│   │   │   ├── record.py
│   │   │   ├── report.py
│   │   │   ├── match.py
│   │   │   ├── badge.py
│   │   │   ├── calendar.py
│   │   │   ├── soul.py
│   │   │   ├── ai.py
│   │   │   ├── importing.py
│   │   │   └── qa.py
│   │   ├── schemas/                       # Pydantic 请求/响应模型
│   │   │   ├── user.py
│   │   │   ├── test.py
│   │   │   ├── record.py
│   │   │   ├── report.py
│   │   │   ├── match.py
│   │   │   └── ai.py
│   │   ├── api/                           # 路由层
│   │   │   ├── app/                       # 用户端 API (/api/app/*)
│   │   │   │   ├── auth.py
│   │   │   │   ├── user.py
│   │   │   │   ├── test.py
│   │   │   │   ├── record.py
│   │   │   │   ├── report.py
│   │   │   │   ├── match.py
│   │   │   │   ├── soul.py
│   │   │   │   ├── badge.py
│   │   │   │   ├── calendar.py
│   │   │   │   └── ops.py
│   │   │   └── admin/                     # 管理端 API (/api/admin/*)
│   │   │       ├── content.py
│   │   │       ├── importing.py
│   │   │       ├── prompt.py
│   │   │       ├── qa.py
│   │   │       └── dashboard.py
│   │   ├── services/                      # 业务逻辑层
│   │   │   ├── score_engine.py
│   │   │   ├── match_engine.py
│   │   │   ├── ai_gateway.py
│   │   │   ├── report_service.py
│   │   │   ├── badge_engine.py
│   │   │   ├── import_service.py
│   │   │   ├── soul_service.py
│   │   │   └── yaml_sync_service.py       # YAML → DB 同步服务
│   │   └── tasks/                         # Celery 异步任务
│   │       ├── celery_app.py
│   │       ├── ai_tasks.py
│   │       ├── report_tasks.py
│   │       └── capsule_tasks.py
│   ├── alembic/                           # 数据库迁移
│   │   ├── alembic.ini
│   │   └── versions/
│   ├── tests/                             # pytest 测试
│   │   ├── conftest.py
│   │   ├── test_score_engine.py
│   │   ├── test_api_auth.py
│   │   ├── test_api_test.py
│   │   └── test_yaml_loader.py
│   ├── pyproject.toml                     # 项目依赖（Poetry）
│   ├── .env.example                       # 环境变量模板
│   └── Dockerfile
├── packages/
│   ├── shared-types/                   # 前后端共用 TS 类型定义
│   ├── shared-test-schema/             # 测试内容 JSON Schema
│   └── shared-prompts/                 # 统一 AI Prompt 模板
├── scripts/
│   ├── import/                         # 数据导入脚本
│   ├── yaml_validate.py                # YAML 配置校验工具
│   ├── mock/                           # Mock 数据
│   └── ci/                             # CI/CD 脚本
└── assets/
    └── design-tokens/                  # 设计 Token
```

---

## 6. YAML 配置驱动设计

本项目的核心设计决策之一是将**题型定义、每套试题的完整内容、答题过程中的交互提示**全部抽离为 YAML 配置文件。这样做的好处：

1. **产品迭代不需改代码。** 新增测试、调整题目顺序、修改提示文案只需编辑 YAML 并重载。
2. **版本可控。** YAML 文件纳入 Git 管理，每次修改都有 diff 记录。
3. **大模型友好。** YAML 比数据库 SQL 更易被大模型生成和校验。
4. **开发调试快。** 开发环境支持热重载，改完 YAML 立即生效。

### 6.1 配置文件总览

```
server/app/config/
├── interaction_types.yaml     # 15 种题型的组件定义与默认配置
├── tests/                     # 每套测试的完整定义（题目、选项、维度、人格）
│   ├── bigfive.yaml
│   ├── mbti.yaml
│   ├── ennea.yaml
│   ├── love.yaml
│   ├── bff.yaml
│   ├── career.yaml
│   ├── couple.yaml
│   └── work.yaml
├── prompts/                   # 答题过程中的文案与提示
│   ├── micro_feedback.yaml    # 小测吉祥物微反馈模板
│   ├── mascot_responses.yaml  # 吉祥物表情与对话
│   └── encouragement.yaml     # 鼓励文案（进度提示、完成祝贺）
├── badges.yaml                # 勋章定义与解锁规则
├── soul_fragments.yaml        # 灵魂碎片定义
└── daily_questions.yaml       # 每日灵魂一问题库
```

### 6.2 题型定义 (`interaction_types.yaml`)

定义 15 种交互类型的组件名称、默认配置、评分方式和前端组件映射。

```yaml
# server/app/config/interaction_types.yaml
# 每种题型的基础定义，前端根据 component 字段加载对应 Vue 组件

interaction_types:
  swipe:
    label: "滑动选择"
    component: "SwipeCard"
    scoring_method: "binary"        # 左=0, 右=1
    default_config:
      leftLabel: "不认同"
      rightLabel: "认同"
      threshold: 60                 # 滑动判定阈值(px)

  bubble:
    label: "气泡选择"
    component: "BubbleSelect"
    scoring_method: "preset_value"  # 选项预设值 0-1
    default_config:
      columns: 2

  slider:
    label: "滑块评分"
    component: "EmojiSlider"
    scoring_method: "normalize"     # 归一化到 0-1
    default_config:
      min: 1
      max: 5
      labels: ["完全不符", "非常符合"]
      emojis: ["😔", "😐", "🙂", "😊", "😄"]

  versus:
    label: "二选一"
    component: "VersusPick"
    scoring_method: "binary"        # A=1, B=0
    default_config:
      topColor: "purple-p"
      bottomColor: "pink-p"

  star:
    label: "星级评分"
    component: "StarRate"
    scoring_method: "normalize"
    default_config:
      maxStars: 5
      labels: ["完全不符合", "不太符合", "一般", "比较符合", "非常符合"]

  scenario:
    label: "场景选择"
    component: "ScenarioPick"
    scoring_method: "preset_value"
    default_config:
      tipText: "选择你最自然的反应"

  tarot:
    label: "塔罗翻牌"
    component: "TarotCards"
    scoring_method: "preset_value"
    default_config:
      cardCount: 3

  hotcold:
    label: "冷热温度"
    component: "HotCold"
    scoring_method: "normalize"     # 0-100 归一化
    default_config:
      minLabel: "冰冷"
      maxLabel: "火热"
      emojis: ["❄️", "🧊", "😐", "🔥", "☀️"]

  constellation:
    label: "星座连线"
    component: "Constellation"
    scoring_method: "word_map"
    default_config:
      positions: []                 # 由题目级 config 覆盖

  fortune:
    label: "转盘"
    component: "FortuneWheel"
    scoring_method: "sector_map"
    default_config:
      sectorColors: ["#9B7ED8", "#E8729A", "#F2A68B", "#7CC5B2"]

  scratch:
    label: "刮刮卡"
    component: "ScratchCard"
    scoring_method: "preset_value"
    default_config:
      canvasWidth: 260
      canvasHeight: 180
      revealThreshold: 0.35

  rank:
    label: "拖拽排序"
    component: "RankDrag"
    scoring_method: "position_normalize"  # 排序位置归一化

  pressure:
    label: "长按感应"
    component: "PressureHold"
    scoring_method: "duration_normalize"  # 按压时长归一化
    default_config:
      maxDuration: 3000
      levels: 5

  plot2d:
    label: "二维坐标"
    component: "Plot2d"
    scoring_method: "xy_map"        # x/y 分别映射两个维度
    default_config:
      xMin: "内向"
      xMax: "外向"
      yMin: "感性"
      yMax: "理性"
      gridSize: 240

  colorpick:
    label: "色彩选择"
    component: "ColorPick"
    scoring_method: "hue_map"       # 色相值映射
    default_config:
      hueMap:
        0: "热情"
        60: "乐观"
        120: "平和"
        180: "沉稳"
        240: "忧郁"
        300: "神秘"
```

### 6.3 测试内容定义 (`tests/*.yaml`)

每套测试一个 YAML 文件，包含完整的题目、选项、维度、人格定义。

```yaml
# server/app/config/tests/mbti.yaml

test_code: mbti
title: "MBTI 16型人格"
category: personality
emoji: "🧩"
is_match_enabled: false
duration_hint: "约10分钟"
cover_gradient: "linear-gradient(135deg, #9B7ED8 0%, #E8729A 100%)"
report_template_code: report_personality_v1

dimensions:
  - code: EI
    name: "外向-内向"
    max_score: 100
  - code: SN
    name: "实感-直觉"
    max_score: 100
  - code: TF
    name: "思考-情感"
    max_score: 100
  - code: JP
    name: "判断-知觉"
    max_score: 100

questions:
  - code: mbti_q1
    seq: 1
    text: "参加社交活动后，你通常感到？"
    interaction_type: versus
    emoji: "🎭"
    config:                         # 覆盖 interaction_types.yaml 中的默认配置
      topColor: "#EDE5F9"
      bottomColor: "#FDE6EF"
    dim_weights:
      EI: 1.0
    options:
      - code: A
        label: "精力充沛想继续"
        emoji: "⚡"
        value: 1.0
        score_rules:
          - dimension_code: EI
            score: 4
      - code: B
        label: "需要独处恢复"
        emoji: "🛋️"
        value: 0.0
        score_rules:
          - dimension_code: EI
            score: 1

  - code: mbti_q2
    seq: 2
    text: "你更容易被什么吸引？"
    interaction_type: bubble
    emoji: "✨"
    dim_weights:
      SN: 0.8
    options:
      - code: A
        label: "具体的事实和细节"
        value: 0.2
        score_rules:
          - dimension_code: SN
            score: 2
      - code: B
        label: "可能性和想象"
        value: 0.8
        score_rules:
          - dimension_code: SN
            score: 4
      - code: C
        label: "两者兼具"
        value: 0.5
        score_rules:
          - dimension_code: SN
            score: 3

  # ... 更多题目

personas:
  - key: INTJ
    name: "策略大师"
    emoji: "🏛️"
    rarity_percent: 2
    description: "独立思考者，善于规划长远目标..."
    soul_signature: "以理性之光照亮未来之路"
    keywords: ["战略", "独立", "远见"]
    dim_pattern:
      EI: [0, 45]
      SN: [55, 100]
      TF: [0, 45]
      JP: [55, 100]
    capsule_prompt: "给三个月后的策略大师写一封信..."

  - key: ENFP
    name: "梦想探险家"
    emoji: "🦋"
    rarity_percent: 18
    description: "充满创意和热情的灵魂..."
    soul_signature: "用热情点亮每一种可能"
    keywords: ["创意", "热情", "共情"]
    dim_pattern:
      EI: [55, 100]
      SN: [55, 100]
      TF: [55, 100]
      JP: [0, 45]
    capsule_prompt: "给未来的梦想探险家描述你现在的世界..."

  # ... 更多人格
```

### 6.4 答题交互提示 (`prompts/*.yaml`)

答题过程中的吉祥物微反馈、鼓励文案、进度提示全部配置化。

```yaml
# server/app/config/prompts/micro_feedback.yaml
# 小测吉祥物在答题过程中的即时反馈模板
# 这些模板用于：AI 降级时的兜底文案 / 低延迟场景直接使用

# 按交互类型分组的微反馈
by_interaction_type:
  swipe:
    right:
      - "果断！✨"
      - "很有主见~"
      - "嗯嗯，记住了"
    left:
      - "也是一种选择~"
      - "了解了！"
      - "这很真实"
  bubble:
    - "有意思的选择~"
    - "这说明了很多呢"
    - "小测记下了！"
  slider:
    low:   # value < 0.3
      - "诚实面对自己👍"
      - "了解~"
    mid:   # 0.3 <= value <= 0.7
      - "中庸之道~"
      - "平衡的你"
    high:  # value > 0.7
      - "感受很强烈呢！"
      - "这很你~"
  versus:
    - "二选一最见真心"
    - "好纠结对吧~"
    - "直觉最准！"
  star:
    - "每颗星都有意义~"
    - "打分就是认识自己"
  scenario:
    - "场景里藏着性格密码"
    - "你的选择很独特"
  pressure:
    short: # < 1s
      - "闪电反应！⚡"
    long:  # > 2s
      - "深思熟虑型~"
  default:
    - "继续加油~"
    - "小测在认真听"
    - "越答越了解你了"

# 按答题进度的鼓励文案
by_progress:
  start:     # 前 20%
    - "旅程开始啦～"
    - "让我们一起探索吧"
  quarter:   # 25%
    - "已经完成四分之一了！"
    - "节奏不错～"
  half:      # 50%
    - "一半了！你很棒"
    - "马上就能看到结果了"
  almost:    # 80%
    - "快到终点了！"
    - "最后几道题～"
  last:      # 最后一题
    - "最后一题！✨"
    - "答案即将揭晓～"
```

```yaml
# server/app/config/prompts/mascot_responses.yaml
# 吉祥物"小测"在不同场景下的表情和对话

emotions:
  happy:
    emoji: "😊"
    triggers: ["完成测试", "解锁勋章", "获得碎片"]
    greetings:
      - "太棒了！"
      - "小测为你骄傲~"
  curious:
    emoji: "🤔"
    triggers: ["开始测试", "浏览新测试"]
    greetings:
      - "准备好探索自己了吗？"
      - "这个测试很有趣哦~"
  surprised:
    emoji: "😮"
    triggers: ["高分", "稀有人格", "天作之合"]
    greetings:
      - "哇！这个结果很特别！"
      - "了不起的发现！"
  thinking:
    emoji: "🧐"
    triggers: ["查看报告", "灵魂画像"]
    greetings:
      - "让我仔细看看..."
      - "你的灵魂很有深度呢"
  sleepy:
    emoji: "😴"
    triggers: ["深夜访问"]
    greetings:
      - "这么晚还在探索呀~"
      - "夜深了，记得休息哦"
  encouraging:
    emoji: "💪"
    triggers: ["答题中途", "连续打卡"]
    greetings:
      - "加油！你可以的"
      - "坚持就是了解自己"
  warm:
    emoji: "🤗"
    triggers: ["首次登录", "长时间未访问"]
    greetings:
      - "欢迎来到心测世界~"
      - "好久不见，想你了~"
```

```yaml
# server/app/config/prompts/encouragement.yaml
# 完成测试后的祝贺文案（按测试类别分组）

completion_messages:
  personality:
    - "探索人格的旅途永远令人着迷"
    - "你又更了解自己了一点"
  emotion:
    - "情绪是了解内心的窗口"
    - "感谢你真诚面对自己的感受"
  relationship:
    - "关系是两颗灵魂的碰撞"
    - "了解自己的关系模式是成长的开始"
  fun:
    - "有趣的灵魂总在探索！"
    - "放松享受，这就是心测的意义"

# 分享引导文案
share_prompts:
  - "想让朋友也了解你的灵魂吗？"
  - "分享给好友，开启灵魂对话"
  - "你的结果值得被看见~"
```

### 6.5 YAML 加载机制

```python
# server/app/core/yaml_loader.py
import yaml
from pathlib import Path
from typing import Any
from functools import lru_cache
from loguru import logger

CONFIG_DIR = Path(__file__).parent.parent / "config"


class YamlConfigStore:
    """
    YAML 配置管理器

    职责:
    - 启动时加载所有 YAML 配置到内存
    - 提供按路径查询配置的接口
    - 开发环境支持 watchfiles 热重载
    - 提供 YAML → DB 同步接口 (用于初始化和配置变更)
    """

    def __init__(self):
        self._store: dict[str, Any] = {}
        self._loaded = False

    def load_all(self):
        """启动时加载所有配置"""
        # 加载题型定义
        self._store["interaction_types"] = self._load_file("interaction_types.yaml")

        # 加载所有测试
        self._store["tests"] = {}
        tests_dir = CONFIG_DIR / "tests"
        if tests_dir.exists():
            for f in tests_dir.glob("*.yaml"):
                data = self._load_file(f"tests/{f.name}")
                if data and "test_code" in data:
                    self._store["tests"][data["test_code"]] = data

        # 加载提示配置
        self._store["prompts"] = {}
        prompts_dir = CONFIG_DIR / "prompts"
        if prompts_dir.exists():
            for f in prompts_dir.glob("*.yaml"):
                key = f.stem  # micro_feedback, mascot_responses, encouragement
                self._store["prompts"][key] = self._load_file(f"prompts/{f.name}")

        # 加载勋章、碎片、每日一问
        for name in ["badges", "soul_fragments", "daily_questions"]:
            path = CONFIG_DIR / f"{name}.yaml"
            if path.exists():
                self._store[name] = self._load_file(f"{name}.yaml")

        self._loaded = True
        logger.info(f"YAML configs loaded: {len(self._store['tests'])} tests, "
                     f"{len(self._store.get('interaction_types', {}).get('interaction_types', {}))} interaction types")

    def _load_file(self, relative_path: str) -> dict:
        path = CONFIG_DIR / relative_path
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def get_interaction_types(self) -> dict:
        return self._store.get("interaction_types", {}).get("interaction_types", {})

    def get_test(self, test_code: str) -> dict | None:
        return self._store.get("tests", {}).get(test_code)

    def get_all_tests(self) -> dict[str, dict]:
        return self._store.get("tests", {})

    def get_prompt(self, category: str) -> dict:
        return self._store.get("prompts", {}).get(category, {})

    def get_micro_feedback(self, interaction_type: str, value: Any = None) -> str:
        """根据题型和答案值获取微反馈文案（AI 降级兜底用）"""
        import random
        fb = self.get_prompt("micro_feedback")
        by_type = fb.get("by_interaction_type", {})

        if interaction_type in by_type:
            pool = by_type[interaction_type]
            if isinstance(pool, dict):
                # 有子分类 (如 slider 的 low/mid/high)
                if interaction_type == "swipe":
                    key = "right" if value == "right" else "left"
                    pool = pool.get(key, pool.get("default", []))
                elif interaction_type == "slider":
                    if value is not None and float(value) < 0.3:
                        pool = pool.get("low", [])
                    elif value is not None and float(value) > 0.7:
                        pool = pool.get("high", [])
                    else:
                        pool = pool.get("mid", [])
                elif interaction_type == "pressure":
                    pool = pool.get("short" if value and float(value) < 1 else "long", [])
                else:
                    pool = list(pool.values())[0] if pool else []
            return random.choice(pool) if pool else "继续加油~"
        return random.choice(fb.get("by_interaction_type", {}).get("default", ["继续加油~"]))

    def reload(self):
        """热重载全部配置"""
        logger.info("Reloading YAML configs...")
        self.load_all()


# 全局单例
yaml_config = YamlConfigStore()
```

### 6.6 YAML 与数据库的关系

**YAML 是配置源，数据库是运行时存储。**

```
YAML 文件 (Git 管理)
   │
   │  启动时 / 手动触发
   ▼
yaml_sync_service.py
   │
   │  对比差异，增量同步
   ▼
数据库表 (xc_test, xc_question, xc_option, ...)
   │
   │  API 查询
   ▼
前端展示
```

**同步策略：**

1. **应用启动时**自动执行 YAML → DB 同步（仅同步 DRAFT 状态的新版本，不覆盖已 PUBLISHED 的数据）。
2. **管理后台**提供"从 YAML 重新同步"按钮，运营可手动触发。
3. **已发布版本不受 YAML 变更影响。** YAML 修改只会创建新的 DRAFT 版本。
4. **数据库作为运行时权威。** 一旦数据同步到数据库并发布，API 查询走数据库，不直接读 YAML。
5. **YAML 热重载**仅影响内存中的配置（如微反馈文案兜底），不自动修改数据库。

```python
# server/app/services/yaml_sync_service.py (核心逻辑伪代码)

async def sync_test_from_yaml(test_code: str, db: AsyncSession):
    """将单个 YAML 测试同步为数据库 DRAFT 版本"""
    yaml_data = yaml_config.get_test(test_code)
    if not yaml_data:
        raise ValueError(f"Test {test_code} not found in YAML config")

    # 1. 查找或创建 xc_test
    test = await get_or_create_test(db, yaml_data)

    # 2. 创建新 DRAFT 版本
    version = await create_draft_version(db, test, yaml_data)

    # 3. 同步维度
    await sync_dimensions(db, version.id, yaml_data["dimensions"])

    # 4. 同步题目与选项
    for q in yaml_data["questions"]:
        question = await sync_question(db, version.id, q)
        for opt in q.get("options", []):
            await sync_option(db, question.id, opt)

    # 5. 同步人格定义
    for p in yaml_data.get("personas", []):
        await sync_persona(db, version.id, p)

    await db.commit()
    return version
```

### 6.7 YAML 校验

提供命令行工具校验 YAML 配置的完整性：

```bash
# 校验所有配置文件
python scripts/yaml_validate.py

# 校验单个测试
python scripts/yaml_validate.py --test mbti
```

校验规则：
1. 每道题的 `interaction_type` 必须在 `interaction_types.yaml` 中有定义
2. 选项的 `dimension_code` 必须在该测试的 `dimensions` 列表中存在
3. 每个 persona 的 `dim_pattern` 键必须与 `dimensions` 的 code 一致
4. `seq` 字段不能重复
5. `value` 字段在 0-1 范围内
6. 必须有至少一个 persona

---

## 7. 后端领域设计（FastAPI）

### 7.1 模块划分

在 FastAPI 项目中按业务域划分 Python 包，每个域独立管理 router / service / schema：

| 模块 | 职责 |
|------|------|
| `app.api.app.auth` | 小程序登录、Token、微信会话、H5 手机号登录 |
| `app.api.app.user` | 用户资料、设置、隐私偏好、Onboarding |
| `app.api.admin.content` | 测试主数据、题目、选项、维度、报告模板、内容版本管理 |
| `app.api.admin.importing` | docx/html 导入、解析任务、预览与审核 |
| `app.api.app.test` | 开始测试、提交答案、评分引擎、历史记录 |
| `app.api.app.report` | 报告快照、AI 分析关联、分享卡片数据 |
| `app.api.app.soul` | 灵魂画像、碎片、等级、人设名片 |
| `app.api.app.match` | 邀请码、双人记录、匹配报告 |
| `app.api.app.badge` | 勋章定义、成就规则引擎、用户勋章 |
| `app.api.app.calendar` | 心情/运势日历、每日灵魂一问 |
| `app.services.ai_gateway` | AI Gateway、Prompt 模板、供应商路由、任务日志 |
| `app.api.admin.qa` | 自动化测试结果收集、AI 测试分析 |
| `app.api.app.ops` | 运营位、推荐、Banner、Push 配置 |

### 7.2 核心服务接口

#### 7.2.1 评分引擎 (ScoreEngine)

```python
class ScoreEngine:
    """
    核心评分引擎 - 将原始答案映射为维度分数和人格类型

    评分流程:
      1. 遍历每道题的答案
      2. 根据题目配置的维度权重, 将答案值映射到各维度
      3. 各维度得分 = sum(答案值 × 权重) / 权重总和 × 100
      4. 综合评分 = 各维度加权平均
      5. 人格匹配 = 找到得分模式最接近的 persona 模板

    15 种交互类型的答案值提取 (由 interaction_types.yaml 的 scoring_method 驱动):
      binary:              swipe 右=1.0/左=0.0, versus A=1.0/B=0.0
      preset_value:        bubble/scenario/tarot/fortune/constellation/scratch 选项预设值 0-1
      normalize:           slider/star/hotcold 原始值归一化到 0-1
      duration_normalize:  pressure 按压时长归一化
      position_normalize:  rank 排序位置归一化
      xy_map:              plot2d x/y坐标分别映射到两个维度
      hue_map:             colorpick 色相值映射
    """

    def __init__(self, yaml_config: YamlConfigStore):
        self.interaction_types = yaml_config.get_interaction_types()

    def calculate(
        self,
        test: TestModel,
        questions: list[QuestionModel],
        answers: dict[int, Any],
    ) -> ScoreResult:
        ...
```

#### 7.2.2 匹配算法

```python
"""
匹配分数计算:
  similarity_score = 100 - avg(|scoreA[i] - scoreB[i]|) for each dimension
  complement_score = 基于特定维度的互补性加权
  match_score = 0.6 * similarity_score + 0.4 * complement_score

匹配等级:
  >=95: 天作之合
  >=85: 灵魂共振
  >=75: 默契搭档
  >=60: 性格各异
  <60: 奇妙碰撞
"""
```

#### 7.2.3 AI 分析服务

```python
from abc import ABC, abstractmethod
from app.schemas.ai import AiAnalysisResult


class AiAnalysisService(ABC):
    """
    AI 大模型分析服务
    双引擎策略: 优先阿里云百炼, 降级火山引擎
    异步处理: 通过 Celery 异步任务解耦, 结果写入数据库后推送通知
    微反馈降级: AI 超时时从 YAML 配置读取预设文案
    """

    @abstractmethod
    async def generate_test_analysis(self, record_id: int) -> AiAnalysisResult:
        """测试结果深度分析 (异步, qwen-max / doubao-pro-32k)"""
        ...

    @abstractmethod
    async def generate_match_analysis(self, match_id: int) -> AiAnalysisResult:
        """匹配报告 AI 点评 (异步)"""
        ...

    @abstractmethod
    async def generate_micro_feedback(
        self, interaction_type: str, answer_value: Any, memory: UserMemorySchema
    ) -> str:
        """
        答题微反馈 (同步, <200ms, qwen-plus / doubao-lite)
        超时降级: 从 yaml_config.get_micro_feedback() 获取预设文案
        """
        ...

    @abstractmethod
    async def generate_soul_insight(self, user_id: int) -> str:
        """灵魂画像 AI 解读 (异步, 800-1200字)"""
        ...

    @abstractmethod
    async def generate_capsule_prompt(
        self, persona: str, scores: dict[str, int]
    ) -> str:
        """时光胶囊 AI 引导语 (同步)"""
        ...
```

### 7.3 关键中间件使用

#### Redis 使用场景

| 场景 | Key 模式 | 数据类型 | TTL |
|------|----------|----------|-----|
| 用户 Token 缓存 | `token:{userId}` | String | 7d |
| 匹配邀请码 | `match:code:{code}` | Hash | 24h |
| 测试排行榜 | `rank:test:{testId}` | Sorted Set | - |
| 每日灵魂一问缓存 | `daily:soul:{date}` | String | 25h |
| 接口限流计数 | `rate:{userId}:{api}` | String | 1min |
| AI 结果缓存 | `ai:analysis:{recordId}` | String | 7d |
| 热门测试列表缓存 | `hot:tests:{category}` | List | 5min |
| 用户在线答题状态 | `taking:{userId}` | Hash | 1h |
| YAML 配置版本 | `config:version` | String | - |

### 7.4 关键配置

```bash
# .env 环境变量配置
# 数据库
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/xince
# 如使用 MySQL: DATABASE_URL=mysql+aiomysql://user:pass@localhost:3306/xince

# Redis
REDIS_URL=redis://localhost:6379/0

# 微信小程序
WX_APPID=your_appid
WX_SECRET=your_secret

# JWT
JWT_SECRET_KEY=your-jwt-secret
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=10080  # 7 天

# AI 模型 - 阿里云百炼
DASHSCOPE_API_KEY=your_key
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
DASHSCOPE_DEFAULT_MODEL=qwen-max
DASHSCOPE_LITE_MODEL=qwen-plus

# AI 模型 - 火山引擎
VOLC_API_KEY=your_key
VOLC_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
VOLC_DEFAULT_MODEL=doubao-pro-32k
VOLC_LITE_MODEL=doubao-lite-32k
VOLC_ENDPOINT_ID=your_endpoint_id

# OSS
OSS_ENDPOINT=your_endpoint
OSS_BUCKET=your_bucket
OSS_ACCESS_KEY_ID=your_ak
OSS_ACCESS_KEY_SECRET=your_sk

# YAML 配置
YAML_HOT_RELOAD=true   # 开发环境开启热重载
```

```python
# app/core/config.py
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 数据库
    database_url: str
    redis_url: str = "redis://localhost:6379/0"

    # 微信
    wx_appid: str = ""
    wx_secret: str = ""

    # JWT
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 10080

    # AI - 百炼
    dashscope_api_key: str = ""
    dashscope_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    dashscope_default_model: str = "qwen-max"
    dashscope_lite_model: str = "qwen-plus"

    # AI - 火山
    volc_api_key: str = ""
    volc_base_url: str = "https://ark.cn-beijing.volces.com/api/v3"
    volc_default_model: str = "doubao-pro-32k"
    volc_lite_model: str = "doubao-lite-32k"
    volc_endpoint_id: str = ""

    # OSS
    oss_endpoint: str = ""
    oss_bucket: str = ""
    oss_access_key_id: str = ""
    oss_access_key_secret: str = ""

    # YAML
    yaml_hot_reload: bool = False

    class Config:
        env_file = ".env"


settings = Settings()
```

---

## 8. 数据库设计

### 8.1 ER 关系概览

```
xc_user ──1:N── xc_test_record ──1:N── xc_test_answer
   │                │
   │                └──1:1── xc_ai_analysis
   │                └──N:1── xc_test_version
   │
   ├──1:N── xc_user_badge
   ├──1:N── xc_calendar_entry
   ├──1:N── xc_time_capsule
   ├──1:N── xc_user_soul_fragment
   ├──1:N── xc_match_participant ──N:1── xc_match_session
   ├──1:1── xc_user_memory
   └──1:1── xc_user_setting

xc_test ──1:N── xc_test_version ──1:N── xc_question ──1:N── xc_option
xc_test_version ──1:N── xc_test_persona
xc_test_version ──1:N── xc_dimension

xc_badge_definition (字典表, 可从 badges.yaml 同步)
xc_daily_soul_question (字典表, 可从 daily_questions.yaml 同步)
xc_soul_fragment_definition (字典表, 可从 soul_fragments.yaml 同步)

xc_import_task ──1:N── xc_import_source_file
xc_import_task ──1:1── xc_import_preview
```

### 8.2 核心表 DDL

> 以下 DDL 以 PostgreSQL 16+ 为基准。如使用 MySQL 8.0+，请将 `BIGSERIAL` 改为 `BIGINT AUTO_INCREMENT`，`BOOLEAN` 改为 `TINYINT`，`TIMESTAMPTZ` 改为 `DATETIME`，并添加 `ENGINE=InnoDB DEFAULT CHARSET=utf8mb4`。

#### 用户域

```sql
CREATE TABLE xc_user (
    id                  BIGSERIAL PRIMARY KEY,
    openid              VARCHAR(64) UNIQUE,
    unionid             VARCHAR(64),
    phone               VARCHAR(20),
    nickname            VARCHAR(50) NOT NULL DEFAULT '探索者',
    avatar_type         SMALLINT DEFAULT 0,
    avatar_value        VARCHAR(255) DEFAULT '🧠',
    bio                 VARCHAR(200) DEFAULT '',
    gender              SMALLINT DEFAULT 0,
    birth_year          INT,
    birth_month         INT,
    onboarding_completed BOOLEAN DEFAULT FALSE,
    sound_enabled       BOOLEAN DEFAULT TRUE,
    status              SMALLINT DEFAULT 1,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_xc_user_openid ON xc_user(openid);
CREATE INDEX idx_xc_user_phone ON xc_user(phone);

-- updated_at 自动更新触发器
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_xc_user_updated
    BEFORE UPDATE ON xc_user FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TABLE xc_user_setting (
    id                  BIGSERIAL PRIMARY KEY,
    user_id             BIGINT UNIQUE NOT NULL REFERENCES xc_user(id),
    notif_match         BOOLEAN DEFAULT TRUE,
    notif_result        BOOLEAN DEFAULT TRUE,
    notif_friend        BOOLEAN DEFAULT TRUE,
    notif_system        BOOLEAN DEFAULT TRUE,
    privacy_show_profile BOOLEAN DEFAULT TRUE,
    privacy_show_history BOOLEAN DEFAULT TRUE,
    privacy_allow_match  BOOLEAN DEFAULT TRUE,
    privacy_anonymous    BOOLEAN DEFAULT FALSE
);

CREATE TABLE xc_user_memory (
    id              BIGSERIAL PRIMARY KEY,
    user_id         BIGINT UNIQUE NOT NULL REFERENCES xc_user(id),
    test_count      INT DEFAULT 0,
    avg_duration    INT DEFAULT 0,
    avg_score       DECIMAL(5,2) DEFAULT 0,
    fav_categories  JSONB,
    know_level      INT DEFAULT 0,
    last_test_at    TIMESTAMPTZ,
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE TRIGGER trg_xc_user_memory_updated
    BEFORE UPDATE ON xc_user_memory FOR EACH ROW EXECUTE FUNCTION update_updated_at();
```

#### 内容域（含版本管理）

```sql
CREATE TABLE xc_test (
    id              BIGSERIAL PRIMARY KEY,
    test_code       VARCHAR(50) UNIQUE NOT NULL,
    title           VARCHAR(100) NOT NULL,
    category        VARCHAR(20) NOT NULL,
    emoji           VARCHAR(10),
    is_match_enabled BOOLEAN DEFAULT FALSE,
    participant_count BIGINT DEFAULT 0,
    sort_order      INT DEFAULT 0,
    yaml_source     VARCHAR(100),                                    -- 对应的 YAML 文件名 (如 "mbti")
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_xc_test_category ON xc_test(category);

CREATE TABLE xc_test_version (
    id              BIGSERIAL PRIMARY KEY,
    test_id         BIGINT NOT NULL REFERENCES xc_test(id),
    version         INT NOT NULL DEFAULT 1,
    status          VARCHAR(20) NOT NULL DEFAULT 'DRAFT',
    description     VARCHAR(500),
    duration_hint   VARCHAR(20),
    cover_gradient  VARCHAR(200),
    report_template_code VARCHAR(50),
    published_at    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (test_id, version)
);
CREATE INDEX idx_xc_test_version_status ON xc_test_version(status);

CREATE TABLE xc_dimension (
    id              BIGSERIAL PRIMARY KEY,
    version_id      BIGINT NOT NULL REFERENCES xc_test_version(id),
    dim_code        VARCHAR(50) NOT NULL,
    dim_name        VARCHAR(50) NOT NULL,
    max_score       INT DEFAULT 100,
    sort_order      INT DEFAULT 0
);
CREATE INDEX idx_xc_dimension_version ON xc_dimension(version_id);

CREATE TABLE xc_question (
    id              BIGSERIAL PRIMARY KEY,
    version_id      BIGINT NOT NULL REFERENCES xc_test_version(id),
    question_code   VARCHAR(50),
    seq             INT NOT NULL,
    question_text   VARCHAR(500) NOT NULL,
    interaction_type VARCHAR(20) NOT NULL,
    emoji           VARCHAR(10),
    config          JSONB,
    dim_weights     JSONB NOT NULL
);
CREATE INDEX idx_xc_question_version_seq ON xc_question(version_id, seq);

CREATE TABLE xc_option (
    id              BIGSERIAL PRIMARY KEY,
    question_id     BIGINT NOT NULL REFERENCES xc_question(id),
    option_code     VARCHAR(20),
    seq             INT NOT NULL,
    label           VARCHAR(200) NOT NULL,
    emoji           VARCHAR(10),
    value           DECIMAL(5,2) NOT NULL,
    score_rules     JSONB,
    ext_config      JSONB
);
CREATE INDEX idx_xc_option_question ON xc_option(question_id);

CREATE TABLE xc_test_persona (
    id              BIGSERIAL PRIMARY KEY,
    version_id      BIGINT NOT NULL REFERENCES xc_test_version(id),
    persona_key     VARCHAR(50) NOT NULL,
    persona_name    VARCHAR(100) NOT NULL,
    emoji           VARCHAR(10),
    rarity_percent  INT,
    description     TEXT,
    soul_signature  VARCHAR(200),
    keywords        JSONB,
    dim_pattern     JSONB NOT NULL,
    capsule_prompt  VARCHAR(300)
);
CREATE INDEX idx_xc_test_persona_version ON xc_test_persona(version_id);
```

#### 答题与报告域

```sql
CREATE TABLE xc_test_record (
    id              BIGSERIAL PRIMARY KEY,
    user_id         BIGINT NOT NULL REFERENCES xc_user(id),
    test_id         BIGINT NOT NULL REFERENCES xc_test(id),
    version_id      BIGINT NOT NULL REFERENCES xc_test_version(id),
    persona_id      BIGINT,
    scores          JSONB NOT NULL,
    total_score     INT,
    duration        INT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_xc_test_record_user_time ON xc_test_record(user_id, created_at DESC);
CREATE INDEX idx_xc_test_record_test ON xc_test_record(test_id);

CREATE TABLE xc_test_answer (
    id              BIGSERIAL PRIMARY KEY,
    record_id       BIGINT NOT NULL REFERENCES xc_test_record(id),
    question_id     BIGINT NOT NULL,
    answer_value    JSONB NOT NULL,
    answered_at     TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_xc_test_answer_record ON xc_test_answer(record_id);

CREATE TABLE xc_report_snapshot (
    id              BIGSERIAL PRIMARY KEY,
    record_id       BIGINT UNIQUE NOT NULL REFERENCES xc_test_record(id),
    dimension_scores JSONB NOT NULL,
    overall_score   INT,
    persona_code    VARCHAR(50),
    report_json     JSONB NOT NULL,
    ai_text         TEXT,
    share_card_url  VARCHAR(500),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE xc_ai_analysis (
    id              BIGSERIAL PRIMARY KEY,
    type            VARCHAR(20) NOT NULL,
    ref_id          BIGINT NOT NULL,
    model_used      VARCHAR(50),
    provider        VARCHAR(20),
    prompt_version  VARCHAR(20),
    prompt_tokens   INT,
    output_tokens   INT,
    content         TEXT NOT NULL,
    status          SMALLINT DEFAULT 2,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_xc_ai_analysis_ref ON xc_ai_analysis(type, ref_id);
```

#### 匹配域

```sql
CREATE TABLE xc_match_session (
    id              BIGSERIAL PRIMARY KEY,
    match_code      VARCHAR(10) UNIQUE NOT NULL,
    test_id         BIGINT NOT NULL,
    status          SMALLINT DEFAULT 0,
    match_score     INT,
    similarity_score INT,
    complement_score INT,
    tier            VARCHAR(20),
    expires_at      TIMESTAMPTZ NOT NULL,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    completed_at    TIMESTAMPTZ
);
CREATE INDEX idx_xc_match_code ON xc_match_session(match_code);

CREATE TABLE xc_match_participant (
    id              BIGSERIAL PRIMARY KEY,
    match_id        BIGINT NOT NULL REFERENCES xc_match_session(id),
    user_id         BIGINT NOT NULL,
    record_id       BIGINT,
    role            VARCHAR(10) NOT NULL,
    UNIQUE (match_id, user_id)
);
```

#### 勋章、日历、胶囊、碎片域

```sql
CREATE TABLE xc_badge_definition (
    id              BIGSERIAL PRIMARY KEY,
    badge_key       VARCHAR(50) UNIQUE NOT NULL,
    name            VARCHAR(50) NOT NULL,
    emoji           VARCHAR(10) NOT NULL,
    description     VARCHAR(200),
    type            VARCHAR(10) NOT NULL,
    unlock_rule     JSONB NOT NULL,
    sort_order      INT DEFAULT 0,
    yaml_source     VARCHAR(50)                                      -- 标记来自 YAML 同步
);

CREATE TABLE xc_user_badge (
    id              BIGSERIAL PRIMARY KEY,
    user_id         BIGINT NOT NULL,
    badge_id        BIGINT NOT NULL,
    tier            SMALLINT DEFAULT 1,
    unlock_count    INT DEFAULT 1,
    unlocked_at     TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (user_id, badge_id)
);
CREATE INDEX idx_xc_user_badge_user ON xc_user_badge(user_id);

CREATE TABLE xc_calendar_entry (
    id              BIGSERIAL PRIMARY KEY,
    user_id         BIGINT NOT NULL,
    date            DATE NOT NULL,
    mood_level      SMALLINT,
    test_record_id  BIGINT,
    source          VARCHAR(20) DEFAULT 'manual',
    UNIQUE (user_id, date)
);

CREATE TABLE xc_daily_soul_question (
    id              BIGSERIAL PRIMARY KEY,
    question_text   VARCHAR(300) NOT NULL,
    options         JSONB NOT NULL,
    insights        JSONB NOT NULL,
    sort_order      INT DEFAULT 0,
    yaml_source     VARCHAR(50)
);

CREATE TABLE xc_daily_soul_answer (
    id              BIGSERIAL PRIMARY KEY,
    user_id         BIGINT NOT NULL,
    question_id     BIGINT NOT NULL,
    answer_index    SMALLINT NOT NULL,
    answer_date     DATE NOT NULL,
    UNIQUE (user_id, answer_date)
);

CREATE TABLE xc_time_capsule (
    id              BIGSERIAL PRIMARY KEY,
    user_id         BIGINT NOT NULL,
    message         TEXT NOT NULL,
    persona_name    VARCHAR(100),
    persona_emoji   VARCHAR(10),
    lock_days       INT NOT NULL,
    unlock_date     DATE NOT NULL,
    is_read         BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_xc_time_capsule_unlock ON xc_time_capsule(unlock_date, is_read);

CREATE TABLE xc_soul_fragment_definition (
    id              BIGSERIAL PRIMARY KEY,
    fragment_key    VARCHAR(50) UNIQUE NOT NULL,
    name            VARCHAR(50) NOT NULL,
    emoji           VARCHAR(10),
    category        VARCHAR(30) NOT NULL,
    required_test_code VARCHAR(50),
    insight         VARCHAR(500),
    sort_order      INT DEFAULT 0,
    yaml_source     VARCHAR(50)
);

CREATE TABLE xc_user_soul_fragment (
    id              BIGSERIAL PRIMARY KEY,
    user_id         BIGINT NOT NULL,
    fragment_id     BIGINT NOT NULL,
    collected_at    TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (user_id, fragment_id)
);
```

#### 导入域

```sql
CREATE TABLE xc_import_task (
    id              BIGSERIAL PRIMARY KEY,
    file_type       VARCHAR(10) NOT NULL,
    file_url        VARCHAR(500) NOT NULL,
    status          VARCHAR(20) DEFAULT 'PENDING',
    parse_log       TEXT,
    ai_log          TEXT,
    preview_json    JSONB,
    operator_id     BIGINT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
```

#### AI 与 QA 域

```sql
CREATE TABLE xc_ai_prompt_template (
    id              BIGSERIAL PRIMARY KEY,
    template_code   VARCHAR(50) UNIQUE NOT NULL,
    scene           VARCHAR(30) NOT NULL,
    system_prompt   TEXT NOT NULL,
    user_prompt_tpl TEXT NOT NULL,
    model_tier      VARCHAR(10) DEFAULT 'PRO',
    temperature     DECIMAL(3,2) DEFAULT 0.70,
    max_tokens      INT DEFAULT 2000,
    version         INT DEFAULT 1,
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE xc_qa_run (
    id              BIGSERIAL PRIMARY KEY,
    run_type        VARCHAR(20),
    total_cases     INT,
    passed          INT,
    failed          INT,
    ai_summary      TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE xc_qa_case_result (
    id              BIGSERIAL PRIMARY KEY,
    run_id          BIGINT NOT NULL REFERENCES xc_qa_run(id),
    case_name       VARCHAR(200),
    status          VARCHAR(10),
    error_log       TEXT,
    screenshot_url  VARCHAR(500)
);
```

---

## 9. RESTful API 接口设计

### 9.1 接口规范

| 项目 | 规范 |
|------|------|
| 用户端基础路径 | `/api/app/` |
| 管理端基础路径 | `/api/admin/` |
| 鉴权方式 | JWT Bearer Token |
| 响应格式 | `{"code": 0, "msg": "success", "data": {...}}` |
| 错误码 | 0=成功, 401=未登录, 403=无权限, 500=服务器错误, 1001-1999=业务错误 |
| 分页 | `page`(从1开始), `size`(默认20) |
| 时间 | ISO 8601 |

### 9.2 用户端 API

#### 认证

```
POST /api/app/auth/wx-login              微信小程序登录
POST /api/app/auth/phone-login           手机号验证码登录(H5)
POST /api/app/auth/refresh-token         刷新 Token
```

**POST /api/app/auth/wx-login**

```json
// 请求
{ "code": "0a3xxx..." }

// 响应
{
  "code": 0,
  "data": {
    "token": "eyJhbGciOiJIUz...",
    "isNewUser": true,
    "userInfo": {
      "id": 10001, "nickname": "探索者", "avatar": "🧠",
      "onboardingCompleted": false
    }
  }
}
```

#### 用户

```
GET  /api/app/user/profile               获取用户资料
PUT  /api/app/user/profile               更新资料
POST /api/app/user/onboarding            完成新用户引导
PUT  /api/app/user/settings              更新设置(通知/隐私)
GET  /api/app/user/stats                 获取统计数据
```

#### 测试

```
GET  /api/app/test/home                  首页数据(精选+推荐+快速入口)
GET  /api/app/test/list                  测试列表(?category=&sort=hot&page=1&size=20)
GET  /api/app/test/{testCode}            测试详情(含题目)
POST /api/app/test/session/start         开始测试(返回 sessionId + 题目列表)
POST /api/app/test/session/{sid}/answer  逐题提交(可选，用于断点续答)
POST /api/app/test/session/{sid}/submit  提交全部答案
GET  /api/app/test/search                搜索(?q=关键词)
GET  /api/app/test/recommend             推荐测试(基于记忆)
```

**POST /api/app/test/session/{sid}/submit**

```json
// 请求
{
  "answers": {
    "101": "right",           // swipe
    "102": 0.75,              // bubble
    "103": 3,                 // slider/star: 1-5
    "104": "A",               // versus
    "105": 1,                 // scenario: 选项索引
    "106": 2,                 // tarot: 牌索引
    "107": 68,                // hotcold: 0-100
    "108": 0,                 // constellation: 词索引
    "109": 3,                 // fortune: 扇区索引
    "110": 1,                 // scratch: 选项索引
    "111": [2,0,3,1],         // rank: 排序数组
    "112": 4,                 // pressure: 1-5
    "113": {"x":0.6,"y":0.3}, // plot2d
    "114": 180                // colorpick: 色相 0-360
  },
  "duration": 245
}

// 响应
{
  "code": 0,
  "data": {
    "recordId": 50001,
    "persona": { "name": "梦幻织梦者", "emoji": "🦋", "rarity": 18 },
    "scores": { "情感洞察力": 82, "理性思维": 65, "社交魅力": 71, "创造力": 88, "内心力量": 74 },
    "totalScore": 76,
    "newBadges": [{ "id": 1, "name": "初次觉醒", "emoji": "🌟", "tier": 1 }],
    "newFragment": { "key": "big5", "name": "大五之光", "category": "personality" },
    "aiAnalysisReady": false
  }
}
```

#### 报告

```
GET  /api/app/report/{recordId}          完整报告
GET  /api/app/report/{recordId}/ai-status AI分析状态(轮询, 支持 SSE)
GET  /api/app/report/{recordId}/share-card 分享卡片图片URL
GET  /api/app/report/history             历史列表
```

#### 画像

```
GET  /api/app/soul/profile               灵魂画像
GET  /api/app/soul/persona-card          人设名片数据
GET  /api/app/soul/fragments             碎片收集进度
```

#### 匹配

```
POST /api/app/match/invite               创建匹配(返回匹配码)
GET  /api/app/match/invite/{code}        查询匹配信息
POST /api/app/match/invite/{code}/join   加入匹配
GET  /api/app/match/report/{matchId}     匹配报告
GET  /api/app/match/history              匹配历史
```

#### 勋章 / 日历

```
GET  /api/app/badge/list                 勋章列表(含解锁状态)
GET  /api/app/calendar/month             月历数据(?year=&month=)
GET  /api/app/calendar/year              年热力图
POST /api/app/calendar/mood              手动记录心情
GET  /api/app/calendar/stats             统计(连续/活跃/平均)
GET  /api/app/daily-soul/today           今日问题
POST /api/app/daily-soul/answer          提交答案
```

#### 时光胶囊

```
POST /api/app/capsules                   创建
GET  /api/app/capsules                   列表
GET  /api/app/capsules/check             检查可解锁
PUT  /api/app/capsules/{id}/read         标记已读
```

#### AI 交互

```
POST /api/app/ai/companion/message       答题微反馈(低延迟)
POST /api/app/ai/report/retry            重试生成AI分析
GET  /api/app/ai/soul-insight            灵魂画像AI解读
```

#### 通知

```
GET  /api/app/notifications              通知列表
PUT  /api/app/notifications/read-all     全部已读
GET  /api/app/notifications/unread       未读数
```

### 9.3 管理端 API

```
POST /api/admin/import/upload            上传文件
POST /api/admin/import/{taskId}/parse    触发解析
GET  /api/admin/import/{taskId}/preview  预览解析结果
POST /api/admin/import/{taskId}/approve  审核通过
POST /api/admin/import/{taskId}/reject   审核拒绝

GET  /api/admin/test/page                测试列表(分页)
POST /api/admin/test/save                保存/编辑测试
POST /api/admin/test/publish             发布测试版本
POST /api/admin/test/offline             下线测试
POST /api/admin/test/sync-yaml           从 YAML 重新同步测试数据

GET  /api/admin/ai/task/page             AI任务列表
GET  /api/admin/ai/prompt/list           Prompt模板列表
PUT  /api/admin/ai/prompt/{id}           编辑Prompt

GET  /api/admin/qa/run/page              QA执行记录
GET  /api/admin/qa/run/{runId}/summary   AI分析总结

POST /api/admin/config/reload            重新加载 YAML 配置
GET  /api/admin/config/status            查看 YAML 配置版本与状态
```

### 9.4 重要接口约束

1. 提交流程必须是"先同步保存记录+生成基础报告，再异步生成 AI 结果"。
2. 报告接口返回"结构化报告 + AI 文本 + 状态"三部分，AI 部分可能为 null。
3. AI 状态接口必须支持**轮询与 SSE** 两种模式。
4. 所有分享页必须使用已落库的报告快照，不现场拼装。

---

## 10. 15 种题型组件化落地

### 10.1 统一接口

所有题型必须做成"配置驱动组件"，统一输出标准答案结构，不在组件里做业务评分。题型定义来自 `interaction_types.yaml`，每道题的具体配置来自 `tests/*.yaml`。

```ts
interface QuestionRenderPayload {
  questionId: number
  questionType: string  // swipe|bubble|slider|versus|star|...
  title: string
  description?: string
  options?: Array<{
    optionId: number
    label: string
    emoji?: string
    value?: number
    ext?: Record<string, any>
  }>
  config?: Record<string, any>  // 合并后的配置 (interaction_types 默认 + 题目级覆盖)
}

// 所有组件统一 emit
emit('commit', { questionId: number, value: any })
```

### 10.2 题型落地表

| 题型 | 小程序实现 | 关键注意点 | 评分方式 |
|------|-----------|-----------|---------|
| `swipe` | `touchstart/touchmove/touchend` + transform | `catch:touchmove` 阻止页面滚动 | 左右映射 0/1 |
| `bubble` | `@tap` + CSS animation | 直接适配 | 选项预设值 |
| `slider` | 自定义 `<movable-view>` | 原生 slider 样式受限, 需自绘 | 1-5 归一化 |
| `versus` | `@tap` 分屏点击 | 直接适配 | A=1, B=0 |
| `star` | `@tap` 循环渲染 5 星 | 直接适配 | 1-5 归一化 |
| `scenario` | `@tap` 文字选项 | 直接适配 | 选项预设值 |
| `tarot` | `@tap` + CSS rotateY 翻转 | 测试 `perspective` 低版本兼容性, 备 2D 降级 | 选项预设值 |
| `hotcold` | `@touchmove` 计算 Y 偏移 | 阻止页面滚动 | 0-100 归一化 |
| `constellation` | `<canvas>` 绘制星点+连线 | 小程序不支持内联 SVG, 必须用 Canvas | 词语映射 |
| `fortune` | `<canvas>` 转盘 + 旋转动画 | CSS animation 性能有限, 用 Canvas 动画 | 落点映射 |
| `scratch` | `<canvas type="2d">` + touch | 使用新版 Canvas 2D API | 揭示项映射 |
| `rank` | `@touchmove` 拖拽排序 | 体验需精心优化, 考虑 `movable-area` | 排序归一化 |
| `pressure` | `@longpress` + `requestAnimationFrame` | page.json 设 `disableScroll: true` | 时长归一化 |
| `plot2d` | `@tap` 获取坐标 + Canvas 网格 | `wx.createSelectorQuery` 坐标换算 | x/y 分别映射 |
| `colorpick` | `<canvas type="2d">` 手动绘制扇形 | 小程序 Canvas 不支持 conic-gradient | 色相映射 |

### 10.3 开发建议

1. 动效复杂题型（scratch/fortune/colorpick/plot2d）**先做 H5 Demo，再移植到小程序**。
2. 小程序不保证所有 CSS 效果与浏览器完全一致，必须设计降级方案。
3. 优先开发顺序：`bubble` → `slider` → `star` → `versus` → `swipe` → `scenario` → 其余高级题型。

---

## 11. 测试内容数据模型与版本策略

### 11.1 标准内容模型

测试内容的权威定义存在于 `server/app/config/tests/*.yaml` 中（参见第 6.3 节）。YAML 同步到数据库后，API 查询走数据库。标准 JSON 模型格式：

```json
{
  "testCode": "mbti",
  "name": "MBTI 16型人格",
  "category": "personality",
  "status": "PUBLISHED",
  "version": 1,
  "intro": "探索你的认知功能偏好",
  "durationSec": 600,
  "isMatchEnabled": false,
  "dimensions": [
    { "code": "EI", "name": "外向-内向", "maxScore": 100 }
  ],
  "questions": [
    {
      "questionCode": "mbti_q1",
      "type": "versus",
      "title": "参加社交活动后，你通常感到？",
      "sort": 1,
      "options": [
        {
          "optionCode": "A",
          "label": "精力充沛想继续",
          "scoreRules": [{ "dimensionCode": "EI", "score": 4 }]
        }
      ],
      "ext": { "emoji": ["⚡", "🛋️"] }
    }
  ],
  "personas": [...],
  "reportTemplateCode": "report_personality_v1"
}
```

### 11.2 内容版本状态机

```
DRAFT → REVIEWING → PUBLISHED → OFFLINE
  ↑                     │
  └─────────────────────┘  (可基于已发布版本创建新草稿)
```

**关键原则：** 所有用户答题记录都要绑定 `version_id`，避免题库变化导致历史报告错乱。

### 11.3 YAML 与版本的协同

1. **YAML 修改** → `yaml_sync_service` 创建新 DRAFT 版本 → 运营审核 → 发布
2. **docx/html 导入** → 解析为结构化数据 → 运营审核 → 可选导出为 YAML → 发布
3. **已发布版本**的数据不受 YAML 或后续导入的影响

---

## 12. docx / html 导入方案

### 12.1 导入流程

```
上传文件 → 保存源文件 → 创建导入任务 → 结构解析
     → LLM 语义补全/校验 → 生成预览 JSON → 运营审核
     → 可选: 导出为 YAML 文件 → 发布到正式题库
```

### 12.2 docx 解析

使用 `python-docx` 读取段落、样式、表格。识别规则：

| 文档元素 | 结构化含义 |
|----------|-----------|
| 一级标题 | 测试名 |
| 二级标题 | 模块、维度、结果分段 |
| 正文段落 | 测试说明、题干、报告文案 |
| 编号列表 | 选项 |
| 表格 | 维度说明、规则表、题目配置表 |

格式不规范时，调用大模型做"结构归并"。

### 12.3 html 解析

使用 `BeautifulSoup4` 解析 DOM + 正则提取 `const T`、`ACHIEVEMENTS`、`SOUL_*` 等配置源。

对当前 `index.html` 采用"代码提取优先，LLM 补齐为辅"策略：
1. 优先提取 `T` 数组中的测试定义
2. 提取 `SOUL`、`BADGE`、`MATCH` 等常量作为初始化数据
3. 不直接把 HTML DOM 当最终内容来源
4. 只用 LLM 处理"解释性文案"和"弱结构化块"

### 12.4 导入后生成 YAML

导入解析成功并审核通过后，可选择将结构化数据导出为 YAML 文件，纳入 `config/tests/` 目录进行 Git 版本管理。

### 12.5 审核拦截规则

满足以下任一条件，不允许直接发布：
1. 缺少测试标题
2. 题目数量为 0
3. 选项少于合法最小值
4. 维度引用不存在
5. 题型配置缺失关键参数（根据 `interaction_types.yaml` 校验）
6. AI 输出 JSON 校验失败

---

## 13. 前端架构设计

### 13.1 状态管理

使用 Pinia，按域拆 store：

| Store | 职责 |
|-------|------|
| `useAuthStore` | Token、登录状态 |
| `useUserStore` | 用户资料、设置 |
| `useTestStore` | 当前测试、题目索引、答案、计时 |
| `useReportStore` | 报告数据、AI 状态 |
| `useSoulStore` | 画像、碎片 |
| `useMatchStore` | 匹配状态 |
| `useBadgeStore` | 勋章列表 |
| `useCalendarStore` | 日历数据 |
| `useConfigStore` | 全局配置、音效开关 |

前端本地缓存只保留"会话优化数据"，核心数据以后端为准。

### 13.2 答题页核心实现

```vue
<!-- QuestionRenderer.vue -->
<template>
  <view class="q-stage">
    <view class="q-header">
      <text class="q-num">QUESTION {{ index + 1 }}/{{ total }}</text>
      <text class="q-text">{{ question.title }}</text>
    </view>
    <view class="q-body">
      <component :is="interactionComponent" :q="question" @commit="onCommit" />
    </view>
    <!-- 吉祥物微反馈 (文案来自 YAML 配置或 AI 实时生成) -->
    <xc-mascot v-if="feedback" :text="feedback" :emotion="mascotEmotion" />
  </view>
</template>

<script setup lang="ts">
const componentMap: Record<string, Component> = {
  swipe: SwipeCard, bubble: BubbleSelect, slider: EmojiSlider,
  versus: VersusPick, star: StarRate, scenario: ScenarioPick,
  tarot: TarotCards, hotcold: HotCold, constellation: Constellation,
  fortune: FortuneWheel, scratch: ScratchCard, rank: RankDrag,
  pressure: PressureHold, plot2d: Plot2d, colorpick: ColorPick,
}
const interactionComponent = computed(() => componentMap[props.question.questionType])
</script>
```

### 13.3 小程序与 Web 差异点

| 功能 | 小程序 | H5 |
|------|--------|-----|
| 登录 | `wx.login` (openid) | 手机号+验证码 / 微信 H5 OAuth |
| 分享 | `onShareAppMessage` 原生分享 | Web Share API / 生成海报 |
| 音效 | `wx.createInnerAudioContext` (能力受限, 做弱化) | Web Audio API (完整) |
| Canvas | `<canvas type="2d">` | 标准 `<canvas>` |
| SVG | 不支持内联 SVG | 原生支持 |
| 动效 | 更保守, 避免超重动画 | 可增强 |

### 13.4 设计系统变量

```scss
$purple: #9B7ED8;    $purple-d: #7C5DBF;  $purple-l: #C9B5F0;  $purple-p: #EDE5F9;
$pink: #E8729A;      $pink-l: #F4A5BF;    $pink-p: #FDE6EF;
$peach: #F2A68B;     $mint: #7CC5B2;      $gold: #D4A853;
$bg: #FBF7F4;        $card: rgba(255,255,255,0.72);
$txt: #3A2E42;       $txt2: #7B6E85;      $txt3: #B5A9BF;
$radius: 16px;       $radius-lg: 24px;    $radius-xl: 32px;
$font: 'Noto Sans SC', system-ui, sans-serif;
$serif: 'Noto Serif SC', Georgia, serif;
```

---

## 14. AI 大模型集成方案

### 14.1 AI Gateway 统一封装

```python
from abc import ABC, abstractmethod
from app.schemas.ai import AiChatRequest, AiChatResult, AiStreamResult, AiJsonResult


class AiGateway(ABC):
    """AI 统一网关接口"""

    @abstractmethod
    async def chat(self, request: AiChatRequest) -> AiChatResult:
        """同步聊天"""
        ...

    @abstractmethod
    async def stream(self, request: AiChatRequest):
        """流式输出 (SSE)"""
        ...

    @abstractmethod
    async def json(self, request: AiChatRequest) -> AiJsonResult:
        """JSON 结构化输出"""
        ...
```

### 14.2 供应商路由策略

| 场景 | 默认供应商 | 备用供应商 | 模型档位 | 延迟要求 |
|------|-----------|-----------|---------|---------|
| 测试结果深度分析 | 阿里云百炼 qwen-max | 火山 doubao-pro-32k | PRO | 异步 |
| 匹配报告分析 | 阿里云百炼 qwen-max | 火山 doubao-pro-32k | PRO | 异步 |
| 灵魂画像解读 | 阿里云百炼 qwen-max | 火山 doubao-pro-32k | PRO | 异步 |
| 答题微反馈 | 火山 doubao-lite | 百炼 qwen-plus | LITE | <200ms |
| 时光胶囊引导语 | 火山 doubao-lite | 百炼 qwen-plus | LITE | <500ms |
| 文档结构化解析 | 阿里云百炼 | 火山引擎 | PRO | 异步 |
| QA 结果分析 | 火山引擎 | 阿里云百炼 | PRO | 异步 |

**切换逻辑：**
1. 默认使用主供应商
2. 超时(>30s)或返回错误 → 自动切换备用
3. **两者均失败 → 返回 YAML 配置的预设兜底文案**（微反馈从 `micro_feedback.yaml`、鼓励从 `encouragement.yaml`）
4. 每 5 分钟探测主供应商可用性，自动恢复

### 14.3 典型 Prompt 设计

#### 测试结果分析

```
System:
你是「小测」，心测 App 的灵魂分析师。你温暖、专业、有洞察力。
请基于用户的测试数据生成个性化分析报告，要求：
1. 分为「你的优势」「你的挑战」「小测建议」三部分
2. 每部分 150-250 字
3. 语气温暖但专业，不浮夸，不泛泛
4. 引用具体维度数据佐证分析
5. 建议需具有可操作性
6. 禁止使用"诊断""治疗建议""医学判断"等高风险表述

User:
测试类型: {testName}
人格类型: {personaName} ({personaEmoji})
各维度得分: {scores}
综合评分: {totalScore}/100
答题时长: {duration}秒
历史测试次数: {historyCount}
```

#### 答题微反馈 (低延迟)

```
System:
你是小测吉祥物，需在一句话内给出答题微反馈（10字以内）。
风格: 活泼、温暖、有趣，偶尔俏皮。禁止: 评判对错、过度解读。

User:
交互类型: {type}, 答案值: {value}, 已完成{n}次测试, {pattern}模式
(仅输出一句反馈语, 不超过10个汉字)
```

#### 匹配报告

```
System:
你是心测的关系分析师，请基于两人的测试数据分析关系特质。
分为「灵魂相似点」「互补之处」「相处建议」三部分，每部分 100-150 字。
正面积极的基调，即使差异大也要找到正面角度。

User:
匹配分数: {matchScore}/100
用户A: {personaA}, 得分 {scoresA}
用户B: {personaB}, 得分 {scoresB}
```

### 14.4 Prompt 管理原则

1. 所有 Prompt 模板化、版本化，存储在 `xc_ai_prompt_template` 表。
2. 心理测试相关文本**禁止**使用"诊断""治疗建议""医学判断"等高风险表述。
3. 输出优先 JSON，再由后端拼装展示。
4. 记录每次调用的 Prompt 版本、模型、温度、返回时间、Token 消耗。
5. 同一记录二次打开优先读取缓存，不重复生成。

### 14.5 API 调用代码

百炼与火山引擎均兼容 OpenAI 格式，统一封装：

```python
import httpx

# 调用示例 (两个供应商接口格式一致，兼容 OpenAI 协议)
url = f"{base_url}/chat/completions"
body = {
    "model": model_or_endpoint_id,
    "messages": [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ],
    "temperature": 0.7,
    "max_tokens": 2000,
}
headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

async with httpx.AsyncClient(timeout=30) as client:
    resp = await client.post(url, json=body, headers=headers)
    result = resp.json()

# 流式输出使用 httpx stream + SSE 解析
async with httpx.AsyncClient() as client:
    async with client.stream("POST", url, json={**body, "stream": True}, headers=headers) as resp:
        async for line in resp.aiter_lines():
            if line.startswith("data: "):
                ...  # 解析 SSE chunk
```

- 百炼文档: https://help.aliyun.com/zh/model-studio/getting-started/first-api-call-to-qwen
- 火山方舟文档: https://www.volcengine.com/docs/82379/1330310

---

## 15. 报告与评分引擎

### 15.1 评分流程

提交答案后，后端统一执行：

1. 校验答案完整性（题数=应答数）
2. 根据 `interaction_types.yaml` 的 `scoring_method` 标准化答案值
3. 根据选项规则 + 维度权重计算维度分
4. 计算综合得分
5. 命中人格类型（dim_pattern 匹配，定义在 `tests/*.yaml` 的 personas）
6. **同步生成报告快照**（结构化部分：雷达图数据/排名/画像标签/灵魂天气/隐喻卡片）
7. **异步提交 AI 分析任务**（深度文字分析）
8. 更新灵魂画像、检查勋章、写入日历、收集碎片、更新记忆

### 15.2 报告两层结构

| 层 | 内容 | 生成方式 |
|----|------|---------|
| 固定结构层 | 维度雷达图、排名百分位、画像标签、灵魂天气、结果段位、隐喻卡片(建筑/动物/星球)、DNA条形图 | 同步计算，规则引擎 |
| AI 增强层 | 优势分析、成长建议、关系建议、情绪安抚文案 | 异步生成，AI Gateway |

### 15.3 报告快照原则

每一份正式结果必须保存为快照，原因：
1. 题库会变（版本化）
2. Prompt 会变（模板版本化）
3. AI 输出会变（不可复现）
4. 分享链接必须可复现

---

## 16. AI 在测试与 QA 中的应用

### 16.1 产品内 AI 能力（用户面向）

1. 单次测试结果分析
2. 多次测试画像总结
3. 匹配报告解读
4. 小测陪伴式微反馈（AI 超时时从 `micro_feedback.yaml` 降级）
5. 时光胶囊引导语
6. 每日灵魂一问洞察增强

### 16.2 研发内 QA AI 分析（开发面向）

1. 自动化回归报告总结
2. 接口失败日志归因
3. 页面视觉回归差异说明
4. 测试截图/Trace 生成缺陷草稿

### 16.3 QA AI 工作流

```
CI 执行自动化测试 → 收集结果/截图/Trace/日志
  → 写入 xc_qa_run + xc_qa_case_result
  → 调用 AI 任务分析
  → 输出:
     - 高风险缺陷 + 根因猜测
     - 可忽略噪音
     - 疑似环境问题
     - 建议责任模块
     - 是否疑似回归
```

AI 输出结构：

```json
{
  "summary": "本次回归共发现 3 个高风险问题",
  "findings": [
    {
      "title": "答题页 scratch 题型在微信端无法提交",
      "severity": "high",
      "suspectedModules": ["interaction/ScratchCard", "canvas-adapter"],
      "evidence": ["screenshot_01.png", "console.log"],
      "fixSuggestion": "检查 touchend 提交阈值与透明度计算"
    }
  ]
}
```

---

## 17. 管理后台设计

### 17.1 核心页面

1. 测试内容管理（列表/编辑/版本/发布）
2. 文档导入中心（上传/解析/预览/审核）
3. 题型配置页
4. 报告模板管理
5. AI Prompt 模板管理
6. AI 任务监控（成功率/时延/成本）
7. 用户记录查看
8. 勋章/画像规则配置
9. Banner/推荐运营位配置
10. QA 结果分析面板
11. **YAML 配置管理**（查看/重新加载/同步到数据库/校验状态）

### 17.2 权限角色

基于 FastAPI 自定义 RBAC 权限体系（依赖注入 + 角色装饰器）：超级管理员、内容运营、测试编辑、审核员、数据分析员、QA 管理员。后端数据管理可通过 SQLAdmin 快速搭建，复杂业务页面使用独立 Vue 3 + Element Plus 管理前端。

---

## 18. 安全、隐私与合规

### 18.1 心理测试合规

1. 所有结果说明为"人格/心理倾向参考"，**不是医疗诊断**。
2. **禁止** AI 给出疾病诊断、处方建议、医疗承诺。
3. 用户协议与隐私协议必须明确：数据用途、AI 生成说明、分享与匹配授权。

### 18.2 数据安全

| 措施 | 实现 |
|------|------|
| 敏感字段加密 | 手机号 AES 加密存储，openid 不可逆哈希 |
| AI 数据脱敏 | AI 请求不传递真实身份信息，仅传匿名化数据 |
| 匹配码安全 | 6 位随机码 + 24h 过期 + 使用后删除 |
| 分享链接 | 短期签名或一次性 code |
| 审计 | AI 文本和 Prompt 留审计记录 |

### 18.3 内容安全

1. 用户昵称、简介、胶囊内容走内容审核（微信内容安全 API）。
2. AI 输出结果增加敏感词过滤。
3. 匹配邀请链路防刷、防滥发。

### 18.4 接口安全

JWT 鉴权 + Redis 限流（slowapi `@limiter.limit("20/minute")`）+ Pydantic 参数校验 + 全站 HTTPS。

---

## 19. 性能与可观测性

### 19.1 性能目标

| 端 | 指标 |
|----|------|
| 小程序首屏 | 接口 <=3 个，2 秒内可交互 |
| 答题组件切换 | 无明显白屏 |
| Canvas 题型 | 帧率可接受 |
| 提交答案接口 | <500ms 同步返回 |
| AI 报告 | 异步，不阻塞主流程 |

### 19.2 可观测性

必须接入：接口日志（loguru / structlog）、慢查询监控、AI 调用成功率/时延/成本统计、Celery 任务失败告警、小程序端错误上报。

---

## 20. 部署架构

```
                   ┌─────────────┐
                   │ 微信小程序    │
                   │ (微信CDN)    │
                   └──────┬──────┘
                          │
                   ┌──────▼──────┐
        ┌──────────┤   Nginx     ├──────────┐
        │          │ (SSL+限流)  │          │
        │          └──────┬──────┘          │
        │                 │                 │
 ┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐
 │  H5 静态资源  │  │ API Server  │  │ Admin 后台   │
 │  (OSS+CDN)  │  │ (FastAPI)   │  │ (Vue+SQLAdmin)│
 └─────────────┘  │ ×2 (负载均衡) │  └─────────────┘
                  └──────┬──────┘
          ┌──────────────┼──────────────┐
   ┌──────▼──────┐ ┌────▼────┐ ┌──────▼──────┐
   │  MySQL 8.0   │ │ Redis 7 │ │  OSS        │
   │  或 PG 16    │ │ (哨兵)  │ │  (文件存储)  │
   └─────────────┘ └─────────┘ └─────────────┘
```

| 服务 | 配置 | 数量 |
|------|------|------|
| API 服务器 (uvicorn) | 2C4G | 2 台 (负载均衡) |
| PostgreSQL / MySQL | 4C8G | 1 主 1 从 |
| Redis | 2C4G | 1 台 (哨兵可选) |
| Nginx | 2C2G | 1 台 |

---

## 21. 自动化测试策略

### 21.1 测试分层

| 层 | 覆盖内容 | 工具 |
|----|---------|------|
| 单元测试 | 评分规则、题型数据标准化、Prompt 拼装、YAML 加载与校验 | pytest |
| 集成测试 | 登录、提交答题、报告生成、导入发布、YAML 同步 | pytest + httpx (FastAPI TestClient) |
| E2E | H5: Playwright; 小程序: miniprogram-automator | Playwright |
| 压测 | 提交接口、报告查询、AI 任务吞吐 | Locust / JMeter |
| AI 回归 | Prompt 样本集、输出稳定性、风险词审查 | 自定义 + AI |

### 21.2 关键自动化场景

至少覆盖：新用户登录引导、完成标准测试、完成匹配测试、生成并轮询 AI 报告、解锁勋章、日历写入、导入 docx、导入 html、YAML 配置加载与同步。

---

## 22. 开发实施路线图

### 阶段 1：脚手架与基础设施

**目标：** 建立多端仓库结构，跑通本地开发环境。

**交付物：** uni-app 主项目 + FastAPI 后端 + 管理端 + PostgreSQL/Redis/OSS 配置 + 环境变量模板 + YAML 配置目录结构 + yaml_loader 基础实现。

**完成标准：** 小程序与 H5 均可启动空壳页面，后端健康检查通过，YAML 配置加载成功，后台可登录。

### 阶段 2：内容模型与导入系统

**目标：** 定义内容 JSON Schema，编写 8 套测试的 YAML 配置文件，实现 YAML → DB 同步，实现 docx/html 导入。

**交付物：** 内容相关数据表 + 8 套测试 YAML + yaml_sync_service + 导入接口 + 导入预览后台页。

**完成标准：** `python -m app.services.yaml_sync_service` 可将 YAML 配置同步到数据库。能把 1 个 docx 解析成测试草稿。

### 阶段 3：用户端基础链路

**目标：** 小程序登录 + 核心页面基础框架。

**交付物：** 登录态 + 用户资料 + 测试列表 + 页面基础布局。

**完成标准：** 可以查看测试列表与详情，可以进入答题页。

### 阶段 4：答题引擎与评分

**目标：** 统一答题引擎 + 高频题型交付。题型组件读取 `interaction_types.yaml` 配置。

**优先级：** bubble → slider → star → versus → swipe → scenario → 其余。

**交付物：** 题型组件库 + 提交与评分接口 + 微反馈 YAML 兜底。

**完成标准：** >=5 种题型在小程序与 H5 可用，提交后能得到结构化结果，答题时有微反馈。

### 阶段 5：报告系统与 AI 网关

**目标：** 报告页 + AI 分析上线。

**交付物：** 报告快照 + 雷达图/条形图 + AI Gateway + 百炼与火山两个供应商接入。

**完成标准：** 提交后可看基础报告，AI 文本异步完成后可展示。

### 阶段 6：画像、勋章、日历

**目标：** 成长体系上线。勋章定义来自 `badges.yaml`，碎片来自 `soul_fragments.yaml`。

**交付物：** 画像聚合 + 勋章规则引擎 + 日历热力图。

**完成标准：** 完成多次测试后画像变化可见，勋章可自动解锁，日历可记录。

### 阶段 7：匹配与分享

**目标：** 邀请、双人答题、匹配报告、分享海报。

**完成标准：** 两个用户可完成匹配并查看报告。

### 阶段 8：高级差异化

**目标：** 小测记忆 + 时光胶囊 + 灵魂碎片 + 每日灵魂一问。每日一问题库来自 `daily_questions.yaml`。

**完成标准：** 用户成长链路完整闭环。

### 阶段 9：QA、压测、发布

**目标：** 上线前质量与运维准备。

**交付物：** 自动化测试集 + AI QA 总结 + 压测报告 + 上线清单 + 回滚预案。

**完成标准：** 小程序提审版本可交付，H5 正式域名可访问。

---

## 23. 大模型执行指导

为了让大模型代理能稳定推进，建议遵循以下规则：

### 23.1 每次任务只做一个明确子域

例如：
- "实现 docx 导入解析模块"
- "实现 bubble/slider/star 三种题型组件"
- "实现测试提交与评分接口"
- "编写 mbti.yaml 和 bigfive.yaml 配置文件"

### 23.2 每次任务给出输入与完成标准

```
任务目标：
边界：
依赖：
输入：
输出：
完成标准：
不可改动项：
```

### 23.3 开发优先顺序

1. 先建 YAML 配置文件
2. 再建数据结构与 YAML 同步
3. 再建接口
4. 再建页面
5. 最后接 AI

不要一开始就做复杂动画与 AI 文案。

---

## 24. 风险与应对

| 风险 | 应对 |
|------|------|
| 原型动效多，小程序还原成本高 | 先还原结构与功能，不强求 100% CSS 细节；复杂题型建立降级版 |
| docx/html 导入格式不稳定 | 先定义导入规范 → AI 补齐 → 审核后发布；成功的导入可导出为 YAML 固化 |
| AI 输出不稳定 | Prompt 模板化 + 输出 JSON + 审计与缓存 + 供应商回退 + YAML 兜底文案 |
| 报告生成耗时影响体验 | 基础结果同步返回，AI 解释异步返回 |
| 项目范围过大 | 严格按 P0/P1/P2 分期，先做闭环 |
| YAML 配置过多难维护 | yaml_validate.py 校验工具 + CI 集成校验 + 管理后台可视化 |

---

## 25. 附录

### 25.1 15 种交互类型 config JSON 结构

> 这些配置的默认值已在 `interaction_types.yaml` 中定义，以下为参考。

```json
// swipe
{"leftLabel": "不认同", "rightLabel": "认同", "threshold": 60}

// bubble (选项在 xc_option 表)
{"columns": 2}

// slider
{"min": 1, "max": 5, "labels": ["完全不符", "非常符合"],
 "emojis": ["😔", "😐", "🙂", "😊", "😄"]}

// versus
{"topColor": "purple-p", "bottomColor": "pink-p"}

// star
{"maxStars": 5, "labels": ["完全不符合","不太符合","一般","比较符合","非常符合"]}

// scenario
{"sceneEmoji": "☕", "sceneText": "你在咖啡店...", "tipText": "选择你最自然的反应"}

// tarot
{"cardCount": 3}

// hotcold
{"minLabel": "冰冷", "maxLabel": "火热", "emojis": ["❄️","🧊","😐","🔥","☀️"]}

// constellation
{"positions": [{"x":"20%","y":"30%"}, ...]}

// fortune
{"sectorColors": ["#9B7ED8","#E8729A","#F2A68B","#7CC5B2"]}

// scratch
{"canvasWidth": 260, "canvasHeight": 180, "revealThreshold": 0.35}

// rank
{}

// pressure
{"maxDuration": 3000, "levels": 5}

// plot2d
{"xMin":"内向","xMax":"外向","yMin":"感性","yMax":"理性","gridSize":240}

// colorpick
{"hueMap":{"0":"热情","60":"乐观","120":"平和","180":"沉稳","240":"忧郁","300":"神秘"}}
```

### 25.2 勋章解锁规则配置示例

> 勋章定义已迁移至 `badges.yaml`，以下为数据库 `unlock_rule` JSONB 字段的参考格式。

```json
// 个人勋章
{"type": "test_count", "value": 1}              // 初次觉醒
{"type": "category_all"}                         // 知识小达人
{"type": "streak", "value": 3}                   // 连续打卡
{"type": "duration_under", "value": 180}         // 闪电手速 <3分钟
{"type": "time_range", "start": 23, "end": 5}   // 深夜思考者

// 双人勋章
{"type": "match_score_above", "value": 95}       // 天作之合
{"type": "same_partner_count", "value": 3}       // 彩虹桥
{"type": "match_score_exact", "value": 88}       // 命运之约
```

### 25.3 第三方服务申请清单

| 服务 | 用途 | 申请地址 |
|------|------|----------|
| 微信小程序 AppID | 登录/分享 | mp.weixin.qq.com |
| 阿里云百炼 API Key | AI 大模型 | bailian.console.aliyun.com |
| 火山引擎豆包 API Key | AI 降级 | console.volcengine.com/ark |
| 阿里云 OSS | 文件存储 | oss.console.aliyun.com |
| 短信服务 | H5 验证码 | 阿里云/腾讯云 SMS |

### 25.4 开发环境搭建

```bash
# 1. 后端
cd server/
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt   # 或: poetry install
cp .env.example .env              # 配置环境变量
uvicorn app.main:app --reload --port 8080

# 2. 数据库 (PostgreSQL)
psql -U postgres -c "CREATE DATABASE xince;"
alembic upgrade head              # 执行迁移
python scripts/seed_data.py       # 初始化数据

# 3. YAML 配置同步
python -m app.services.yaml_sync_service   # 将 YAML 配置同步到数据库

# 4. YAML 配置校验
python scripts/yaml_validate.py            # 校验所有 YAML 文件

# 5. Celery 异步任务
celery -A app.tasks.celery_app worker --loglevel=info

# 6. 小程序 + H5 (uni-app)
cd apps/xince-app
npm install
npm run dev:mp-weixin    # 小程序
npm run dev:h5           # H5

# 7. 管理后台
cd apps/xince-admin
npm install && npm run dev
```

### 25.5 参考文档

- 阿里云百炼: https://help.aliyun.com/zh/model-studio/getting-started/first-api-call-to-qwen
- 阿里云百炼批量接口: https://help.aliyun.com/zh/model-studio/batch-interfaces-compatible-with-openai
- 火山方舟 SDK: https://www.volcengine.com/docs/82379/1399008
- 火山方舟 API: https://www.volcengine.com/docs/82379/1330310

---

*本文档以 FastAPI + YAML 配置驱动为技术基础，将题型定义、试题内容、交互提示全部配置化，实现产品迭代与代码开发解耦。开发团队或大模型代理可依据各阶段逐步推进实施。*
