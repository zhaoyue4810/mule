# 心测发布清单

这份清单用于本地联调、预发布和正式发布前的统一检查，目标是把“感觉差不多能上”变成“有明确基线、可重复执行”的流程。

## 1. 环境基线

### 后端

- Python 版本：`>= 3.11`
- 推荐 Conda 环境：`xince`
- 数据库：PostgreSQL
- Redis：可选但建议开启

### 前端

- Node：当前仓库可通过 `npm run type-check` 和 `npm run build:h5`
- 构建目标：H5 / 微信小程序

## 2. 必填配置

发布前至少确认以下配置不再是占位值：

- `APP_ENV`
- `APP_DEBUG`
- `DATABASE_URL`
- `JWT_SECRET_KEY`

按接入范围选择性确认：

- `WX_APPID`
- `WX_SECRET`
- `DASHSCOPE_API_KEY`
- `VOLC_API_KEY`
- `VOLC_ENDPOINT_ID`（如有）

## 3. 后端发布前检查

在 [/Users/zhaoyue/pythonProject/mule/server](/Users/zhaoyue/pythonProject/mule/server) 执行：

```bash
conda activate xince
python scripts/check_runtime.py
bash scripts/run_pytest.sh -q
python ../scripts/yaml_validate.py
```

通过标准：

- `check_runtime.py` 返回 `ready`
- 后端测试全绿
- YAML 校验通过

## 4. 前端发布前检查

在 [/Users/zhaoyue/pythonProject/mule/apps/xince-app](/Users/zhaoyue/pythonProject/mule/apps/xince-app) 执行：

```bash
npm run type-check
npm run build:h5
```

通过标准：

- 类型检查通过
- H5 构建通过
- 仅允许已有 `uni-app` / Sass 弃用警告，不允许新增构建错误

## 5. 关键功能冒烟

至少验证以下链路：

1. 访客进入应用后能建立会话
2. 未完成 onboarding 的用户会进入 onboarding 页面
3. 已发布测试可正常展示列表与详情
4. 完成一次答题后可生成报告
5. 个人中心可看到历史记录与成长反馈
6. 分享海报可预览并保存
7. 后台可读取 AI 任务列表、概览和 metrics
8. `/health` 正常返回
9. `/health/ready` 在环境完整时返回 `200`

## 6. 小程序专项

发布前额外确认：

- 真机 `wx.login()` 可获取 `js_code`
- `/api/app/auth/wechat/mini-program` 可返回正式会话
- 同一用户重复登录不会创建重复账号
- 访客升级到微信身份时，历史测试记录不会丢失

## 7. 回滚准备

至少准备：

- 当前后端镜像 / 版本号
- 当前前端构建包
- 当前数据库迁移版本
- 最近一次可回滚的发布版本
- 发布失败时的回滚联系人与步骤

## 8. 当前已知未完成项

这份清单当前仍有 3 类事项需要后续补齐：

- 压测基线
- 告警与日志聚合
- 正式回滚演练
