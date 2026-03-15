# 心测项目本地部署与效果预览指南

这份文档的目标是帮你把当前仓库完整跑起来，并实际查看：

- 后端 API
- 用户端 H5
- 用户端微信小程序构建结果
- 管理后台 H5

文档也会明确写出：现在还需要你配合准备什么外部环境。

## 1. 你需要先准备什么

在开始之前，请先确认下面这些条件。

### 1.1 基础运行环境

- Python `3.11+`
- Node.js `18+`，建议使用较新的 LTS 版本
- npm
- PostgreSQL
- Redis
- 微信开发者工具

### 1.2 你需要配合准备的内容

这些是仓库代码之外，你需要自己准备或确认的：

1. 本机可用的 PostgreSQL 服务
2. 本机可用的 Redis 服务
3. 一个本地数据库 `xince`
4. 微信开发者工具
5. 如果你要在真机上调小程序，而不是只在开发者工具里看效果：
   需要把前端 API 地址改成你电脑的局域网 IP，而不是 `127.0.0.1`

### 1.3 当前可选，不是阻塞项

以下配置现在不是必须项，不影响你本地看主要成果：

- 微信正式 `WX_APPID / WX_SECRET`
- 阿里云短信配置
- OSS 配置
- AI 平台 API Key

原因：

- 短信服务默认是 `mock`
- 小程序登录在未配置微信正式能力时，当前链路会尽量降级
- 大部分前端演示和主流程可在本地依赖 mock / 默认配置运行

## 2. 推荐启动顺序

建议按这个顺序启动：

1. 启动 PostgreSQL 和 Redis
2. 初始化并启动后端
3. 启动管理后台 H5
4. 启动用户端 H5
5. 构建并导入微信小程序

## 3. 后端部署与运行

后端目录：[/Users/zhaoyue/pythonProject/mule/server](/Users/zhaoyue/pythonProject/mule/server)

### 3.1 创建数据库

如果你本机还没有 `xince` 数据库，可以先执行：

```sql
CREATE USER xince WITH PASSWORD 'xince';
CREATE DATABASE xince OWNER xince;
```

如果用户或数据库已经存在，可以跳过。

### 3.2 启动 PostgreSQL / Redis

你可以按自己的方式启动，只要最终满足：

- PostgreSQL 监听 `localhost:5432`
- Redis 监听 `localhost:6379`

如果你用 Homebrew，常见方式是：

```bash
brew services start postgresql
brew services start redis
```

### 3.3 配置后端环境变量

```bash
cd /Users/zhaoyue/pythonProject/mule/server
cp .env.example .env
```

默认 `.env.example` 已经包含本地开发所需关键值，尤其是：

- `DATABASE_URL=postgresql+asyncpg://xince:xince@localhost:5432/xince`
- `REDIS_URL=redis://localhost:6379/0`
- `SMS_PROVIDER=mock`

如果你的本地 PostgreSQL 用户名、密码或端口不同，请修改 `.env`。

### 3.4 安装依赖

推荐使用项目内虚拟环境：

```bash
cd /Users/zhaoyue/pythonProject/mule/server
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### 3.5 执行数据库迁移

```bash
cd /Users/zhaoyue/pythonProject/mule/server
source .venv/bin/activate
alembic upgrade head
```

### 3.6 启动后端

```bash
cd /Users/zhaoyue/pythonProject/mule/server
source .venv/bin/activate
uvicorn app.main:app --reload --host 127.0.0.1 --port 8080
```

如果你后面要让手机访问你电脑上的后端，请改成：

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

### 3.7 后端启动后如何检查

浏览器打开：

- [http://127.0.0.1:8080/health](http://127.0.0.1:8080/health)
- [http://127.0.0.1:8080/docs](http://127.0.0.1:8080/docs)

也可以执行运行时检查：

```bash
cd /Users/zhaoyue/pythonProject/mule/server
source .venv/bin/activate
python scripts/check_runtime.py
```

如果输出 JSON 里 `status` 是 `ready`，说明后端运行条件基本满足。

### 3.8 后端我已替你验证过的项目

我已经实际跑过：

```bash
cd /Users/zhaoyue/pythonProject/mule/server
python -m py_compile app/main.py
python -m py_compile app/services/sms_service.py
python -m py_compile app/services/content_filter.py
./.venv/bin/python -m pytest tests/ -v --tb=short
```

结果：`83 passed`

## 4. 用户端 H5 运行方式

用户端目录：[/Users/zhaoyue/pythonProject/mule/apps/xince-app](/Users/zhaoyue/pythonProject/mule/apps/xince-app)

### 4.1 配置前端环境变量

```bash
cd /Users/zhaoyue/pythonProject/mule/apps/xince-app
cp .env.example .env
```

当前默认值是：

```env
VITE_API_BASE_URL=http://127.0.0.1:8080/api/app
```

如果你只是本机浏览器访问 H5，这个默认值通常就够了。

如果你要用手机或小程序真机访问，请改成你电脑的局域网地址，例如：

```env
VITE_API_BASE_URL=http://192.168.1.23:8080/api/app
```

### 4.2 安装依赖

```bash
cd /Users/zhaoyue/pythonProject/mule/apps/xince-app
npm install
```

### 4.3 启动 H5 开发环境

```bash
cd /Users/zhaoyue/pythonProject/mule/apps/xince-app
npm run dev:h5
```

命令启动后，终端通常会输出本地访问地址。  
你可以直接在浏览器中打开它，查看当前用户端效果。

### 4.4 我已替你验证过的前端构建

我已经实际跑过：

```bash
cd /Users/zhaoyue/pythonProject/mule/apps/xince-app
npx vue-tsc --noEmit
npm run build:h5
npm run build:mp-weixin
```

全部通过。

## 5. 微信小程序查看方式

### 5.1 构建小程序

```bash
cd /Users/zhaoyue/pythonProject/mule/apps/xince-app
npm run build:mp-weixin
```

构建产物目录是：

- [/Users/zhaoyue/pythonProject/mule/apps/xince-app/dist/build/mp-weixin](/Users/zhaoyue/pythonProject/mule/apps/xince-app/dist/build/mp-weixin)

### 5.2 导入微信开发者工具

打开微信开发者工具，选择“导入项目”，目录指向：

- `/Users/zhaoyue/pythonProject/mule/apps/xince-app/dist/build/mp-weixin`

### 5.3 小程序联调时你需要配合的设置

如果你只是本地联调，通常还需要在微信开发者工具里：

1. 打开“详情”
2. 勾选或启用开发环境下的“不校验合法域名 / TLS / HTTPS 证书”相关选项

否则小程序请求本地后端时，可能因为域名白名单限制而失败。

### 5.4 真机预览时的额外要求

如果你要在手机上而不是开发者工具模拟器里看效果，请同时满足：

1. 后端使用 `0.0.0.0` 启动
2. `apps/xince-app/.env` 中的 `VITE_API_BASE_URL` 改成你电脑的局域网 IP
3. 手机和电脑处于同一个局域网

## 6. 管理后台运行方式

管理后台目录：[/Users/zhaoyue/pythonProject/mule/apps/xince-admin](/Users/zhaoyue/pythonProject/mule/apps/xince-admin)

### 6.1 API 基地址

管理后台默认请求：

```text
http://127.0.0.1:8080/api
```

也就是直接打后端的 `/api/admin/*` 路径。

如果你要改地址，可以自己新增环境变量：

```env
VITE_ADMIN_API_BASE_URL=http://127.0.0.1:8080/api
```

### 6.2 安装依赖

```bash
cd /Users/zhaoyue/pythonProject/mule/apps/xince-admin
npm install
```

### 6.3 启动管理后台

```bash
cd /Users/zhaoyue/pythonProject/mule/apps/xince-admin
npm run dev
```

默认 Vite 端口是 `5174`。

### 6.4 管理后台登录信息

当前可以使用：

- 用户名：`admin`
- 密码：`xince-admin-2026`

### 6.5 我已替你验证过的 admin 构建

我已经实际跑过：

```bash
cd /Users/zhaoyue/pythonProject/mule/apps/xince-admin
npx vue-tsc --noEmit
npm run build
```

全部通过。

## 7. 建议你实际查看的成果路径

如果你要最快看到成果，建议按下面这个顺序看。

### 7.1 先看后端是否正常

打开：

- [http://127.0.0.1:8080/docs](http://127.0.0.1:8080/docs)

重点确认：

- `/api/app/tests`
- `/api/app/profile/me/overview`
- `/api/admin/auth/login`

### 7.2 再看用户端 H5

重点建议你验证这些路径：

1. 首页
2. 发现页
3. 我的页
4. 测试详情页
5. 答题页
6. 报告揭晓与结果页
7. 新增的二级页面：
   - 编辑资料
   - 关于心测
   - 消息通知
   - 搜索
   - 星座详情

### 7.3 然后看小程序效果

重点建议验证：

1. 页面是否能正常打开
2. 是否能请求到本地后端
3. `Confetti`、`ReportReveal`、`CelebrationOverlay` 是否正常展示
4. 新增二级页面是否都能从入口跳转到达

### 7.4 最后看 admin

重点建议验证：

1. 登录
2. Dashboard
3. YAML / 内容管理页面
4. 用户与徽章页面

## 8. 常见问题排查

### 8.1 H5 打不开数据

优先检查：

1. 后端是否真的已启动在 `8080`
2. `apps/xince-app/.env` 的 `VITE_API_BASE_URL` 是否正确
3. 改完 `.env` 后是否重新启动了前端 dev server

### 8.2 小程序能打开但请求失败

优先检查：

1. 微信开发者工具是否关闭了域名校验
2. 是否还在使用 `127.0.0.1`
3. 如果是真机，是否已经改成电脑局域网 IP
4. 后端是否使用了 `--host 0.0.0.0`

### 8.3 后端启动失败

优先检查：

1. PostgreSQL 是否已启动
2. Redis 是否已启动
3. `.env` 中的 `DATABASE_URL` / `REDIS_URL` 是否正确
4. 是否已执行 `alembic upgrade head`

### 8.4 admin 登录失败

优先检查：

1. 后端是否已启动
2. 你访问的是 `http://127.0.0.1:8080/api/admin/auth/login`
3. 使用的账号是否为 `admin / xince-admin-2026`

## 9. 你现在最少要做的配合动作

如果你只想尽快本地看成果，最少只需要完成这些：

1. 启动 PostgreSQL
2. 启动 Redis
3. 创建本地数据库 `xince`
4. 按文档跑起后端
5. 跑起 `apps/xince-app` 的 H5
6. 用微信开发者工具导入 `dist/build/mp-weixin`

## 10. 一套最短可执行命令清单

### 后端

```bash
cd /Users/zhaoyue/pythonProject/mule/server
cp .env.example .env
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload --host 127.0.0.1 --port 8080
```

### 用户端 H5

```bash
cd /Users/zhaoyue/pythonProject/mule/apps/xince-app
cp .env.example .env
npm install
npm run dev:h5
```

### 用户端小程序构建

```bash
cd /Users/zhaoyue/pythonProject/mule/apps/xince-app
npm run build:mp-weixin
```

### 管理后台

```bash
cd /Users/zhaoyue/pythonProject/mule/apps/xince-admin
npm install
npm run dev
```

---

如果你希望，我下一步可以继续帮你做两件事中的任意一个：

1. 再写一份“面向生产环境”的部署文档
2. 再写一份“按页面逐项验收”的测试 checklist
