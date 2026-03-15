# 心测项目总览

这是项目唯一总入口文档。状态以 `STATUS.md` 为准，后续开发顺序以 `PLAN.md` 为准。

## 1. 项目是什么

心测是一个围绕心理测试、人格画像、成长反馈和双人匹配构建的多端项目。

当前仓库包含：

- 用户端：`apps/xince-app/`
- 管理后台：`apps/xince-admin/`
- 后端：`server/`
- 配置源：`server/app/config/`
- 高保真 demo：`index.html`
- 产品蓝图源：`xince-design-doc.docx`
- 技术方案源：`xince-technical-design-final_121644ff.md`

## 2. 双轨基线

### 目标产品蓝图

来源：

- `xince-design-doc.docx`

用途：

- 定义最终产品范围、页面结构、体验目标和内容运营形态

### 当前实现基线

来源：

- `index.html`
- `xince-technical-design-final_121644ff.md`
- 仓库现有代码

用途：

- 判断今天真实完成度、可运行能力和最近一轮开发优先级

## 3. 当前工程结论

- 这已经不是“只有原型”的仓库，前后端和后台都已成型
- 用户端主链路、后台基础能力、后端主要业务域都已具备
- 发现页、通知页、星座内容等仍是部分完成模块
- 当前项目管理方式不再依赖多个 README 和 `docs/*.md`，只维护根目录 3 个活文档

## 4. 推荐启动方式

### 一键开发栈

```bash
cd /Users/zhaoyue/pythonProject/mule
bash scripts/dev_stack.sh up
```

默认地址：

- 后端：`http://127.0.0.1:8080`
- 用户端 H5：`http://127.0.0.1:5173`
- 管理后台：`http://127.0.0.1:5174`

停止：

```bash
cd /Users/zhaoyue/pythonProject/mule
bash scripts/dev_stack.sh down
```

### 分别启动

后端：

```bash
cd /Users/zhaoyue/pythonProject/mule/server
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload --port 8080
```

用户端：

```bash
cd /Users/zhaoyue/pythonProject/mule/apps/xince-app
cp .env.example .env
npm install
npm run dev:h5
```

管理后台：

```bash
cd /Users/zhaoyue/pythonProject/mule/apps/xince-admin
npm install
npm run dev -- --host 127.0.0.1 --port 5174
```

## 5. 常用验证命令

后端：

```bash
cd /Users/zhaoyue/pythonProject/mule/server
bash scripts/run_pytest.sh -q
python scripts/check_runtime.py
python ../scripts/yaml_validate.py
```

用户端：

```bash
cd /Users/zhaoyue/pythonProject/mule/apps/xince-app
npm run type-check
npm run build:h5
```

管理后台：

```bash
cd /Users/zhaoyue/pythonProject/mule/apps/xince-admin
npm run type-check
npm run build
```

## 6. 文档职责

- `PROJECT.md`
  - 项目总览、基线说明、启动方式、验证命令
- `STATUS.md`
  - 唯一事实状态板、最新验证结果、当前风险
- `PLAN.md`
  - 最终蓝图差距、阶段目标、开发优先级

## 7. 当前输入材料

以下文件保留，但不作为“活状态板”：

- `xince-design-doc.docx`
- `xince-technical-design-final_121644ff.md`
- `index.html`
- `docs/demo_inventory.json`
