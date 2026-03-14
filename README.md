# XinCe / 心测

这个仓库目前的输入材料有 3 份：

- `xince-technical-design-final_121644ff.md`：正式技术落地方案
- `xince-design-doc.docx`：产品与交互设计文档
- `index.html`：高保真单文件 demo

我已经先把项目启动阶段需要的基础底座搭出来，目标不是继续堆单文件原型，而是按技术方案里的路线，把项目迁移为配置驱动的正式工程。

## 当前已落地

- `server/`：FastAPI 后端骨架
- `server/app/config/`：YAML 配置目录和首批配置文件
- `scripts/yaml_validate.py`：YAML 校验脚本
- `scripts/extract_demo_inventory.py`：从 `index.html` 抽取业务清单的脚本
- `docs/project-start.md`：根据三份源材料整理的开工说明
- `docs/master-development-plan.md`：后续多轮协作使用的总体开发计划
- `docs/project-status.md`：持续维护的项目进度与缺口状态板

## 推荐启动顺序

1. 先稳定内容模型和 YAML 配置源
2. 再做 YAML -> DB 同步
3. 再做用户端基础链路
4. 最后接评分引擎、报告和 AI

这个顺序来自技术方案第 22 节，和当前仓库的真实状态最匹配。

## 后端启动

```bash
cd /Users/zhaoyue/pythonProject/mule/server
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
uvicorn app.main:app --reload --port 8080
```

后端测试建议统一走：

```bash
cd /Users/zhaoyue/pythonProject/mule/server
bash scripts/run_pytest.sh
```

这样可以避免不同 shell / Python PATH 差异导致的 `pytest` 不可用问题。

如果你平时用 Conda，也可以直接使用当前的 `hjll_zy` 环境：

```bash
conda activate hjll_zy
cd /Users/zhaoyue/pythonProject/mule/server
python -m pip install -e ".[dev]"
bash scripts/run_pytest.sh
```

启动后可访问：

- `http://127.0.0.1:8080/health`
- `http://127.0.0.1:8080/docs`
- `http://127.0.0.1:8080/api/app/bootstrap`

## 配置校验

```bash
cd /Users/zhaoyue/pythonProject/mule
python3 scripts/yaml_validate.py
```

## Demo 业务清单抽取

```bash
cd /Users/zhaoyue/pythonProject/mule
python3 scripts/extract_demo_inventory.py \
  --html index.html \
  --output docs/demo_inventory.json
```

## 当前进度入口

- 项目总计划：[docs/master-development-plan.md](/Users/zhaoyue/pythonProject/mule/docs/master-development-plan.md)
- 动态状态板：[docs/project-status.md](/Users/zhaoyue/pythonProject/mule/docs/project-status.md)
- 开工背景说明：[docs/project-start.md](/Users/zhaoyue/pythonProject/mule/docs/project-start.md)
- 发布清单：[docs/release-checklist.md](/Users/zhaoyue/pythonProject/mule/docs/release-checklist.md)

## 接下来最值得继续做的 4 件事

1. 把导入生成的草稿版本补成可读取、可编辑的内容结构
2. 明确用户端只读取 `PUBLISHED` 版本
3. 初始化 `apps/xince-app`
4. 建立答题引擎与统一题型协议
