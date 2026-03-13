# xince-app

`xince-app` 是心测项目的用户端主应用，技术栈按项目基线使用：

- `uni-app`
- `Vue 3`
- `TypeScript`
- `Pinia`

当前已完成第一版工程初始化，包含：

- `uni-app + vite` 基础脚手架
- 4 个 tab 页面骨架
- 已发布测试列表页
- 已发布测试详情页
- 基于后端 `/api/app/tests` 的数据接入

## 启动

```bash
cd /Users/zhaoyue/pythonProject/mule/apps/xince-app
cp .env.example .env
npm install
npm run dev:h5
```

当前依赖已对齐到官方最新 `vite-ts` 模板版本。如果本机仍出现 `uni` CLI 或 TypeScript 构建异常，需要继续看 `@dcloudio` 当前工具链与本机 Node 版本的实际兼容情况。

## 当前范围

当前先完成 P0 用户链路的前两步：

1. 测试列表
2. 测试详情

下一步会继续做答题容器和题型渲染协议。
