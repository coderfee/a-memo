# Release 流程

## 版本号规范

遵循语义化版本 (semver)：

| 类型 | 场景 | 示例 |
|------|------|------|
| `patch` | Bug 修复 | `1.1.1` → `1.1.2` |
| `minor` | 新功能（向后兼容） | `1.1.1` → `1.2.0` |
| `major` | 破坏性变更 | `1.1.1` → `2.0.0` |

## 发布前检查

1. **本地验证**
   ```bash
   uv run memo --help
   uv run memo list --limit 3
   ```

2. **确认改动已提交**
   ```bash
   git status   # 确保没有未提交的修改
   git log --oneline -3
   ```

## 发布步骤

1. **更新版本号**
   ```bash
   # 编辑 pyproject.toml
   version = "1.2.3"
   ```

2. **提交版本变更**
   ```bash
   git add pyproject.toml
   git commit -m "chore: bump version to 1.2.3"
   git push
   ```

3. **打标签并推送**
   ```bash
   git tag -a v1.2.3 -m "Release 1.2.3"
   git push origin v1.2.3
   ```

   CI 检测到 `v*` 标签后自动构建并发布到 PyPI。

4. **确认发布成功**
   前往 [PyPI Releases](https://pypi.org/manage/releases/a-memo/) 验证，或：
   ```bash
   pip install a-memo==1.2.3 --dry-run  # 检查版本是否可下载
   ```

## 常见问题

**Q: 忘记先提交版本号就打了 tag？**
> 重新打一个 `v1.2.3-hotfix` 或用 `git tag -f` 强制更新（仅限未发布时使用）。

**Q: tag 和 pyproject.toml 版本不一致？**
> PyPI 会按 pyproject.toml 的版本发布。tag 版本号仅用于触发 CI，必须保持一致。

**Q: 需要回滚？**
> PyPI 不支持删除版本。发布破坏性变更前确保测试充分。
