# Mock Assets

本目录提供本地联调用的模拟文件：

- `imports/xince-full-mock-import.html`
  - 后台“内容导入”页面可直接上传
  - 会导入完整测试、维度、题目、人格到 `IMPORTED_DRAFT`
- `env/server.mock.env`
  - 本地服务端测试环境示例
  - 如需覆盖当前 `server/.env`，可手动复制内容

如需重新生成导入包：

```bash
cd /Users/zhaoyue/pythonProject/mule
python3 scripts/generate_mock_import_html.py
```
