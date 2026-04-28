# Release 流程

## 发布步骤

1. **更新版本号**

   编辑 `pyproject.toml`，将 `version` 改为目标版本：

   ```toml
   version = "1.2.3"
   ```

2. **提交并推送到远程**

   ```bash
   git add pyproject.toml
   git commit -m "chore: bump version to 1.2.3"
   git push
   ```

3. **打标签并推送**

   ```bash
   git tag v1.2.3
   git push origin v1.2.3
   ```

   GitHub Actions 检测到 `v*` 标签后自动构建并发布到 PyPI。

## 注意事项

- 版本号必须与 pyproject.toml 一致，CI 不会自动同步
- 推送 tag 后前往 [PyPI Releases](https://pypi.org/manage/releases/a-memo/) 确认发布成功
