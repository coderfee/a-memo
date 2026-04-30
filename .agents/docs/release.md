# Release 流程

本文档用于执行 `a-memo` 正式发布。发布由 GitHub tag 触发，产物包括 PyPI 包、GitHub Release assets、Homebrew tap Formula。

## 发布产物

- PyPI 包：`a-memo`
- GitHub Release：源码包、wheel、macOS/Linux/Windows 独立二进制
- Homebrew tap：`coderfee/homebrew-tap`
- 用户安装命令：`brew install coderfee/tap/a-memo`

## 版本号

使用语义化版本：

| 类型 | 场景 | 示例 |
|------|------|------|
| `patch` | Bug 修复 | `1.5.0` -> `1.5.1` |
| `minor` | 向后兼容的新功能 | `1.5.0` -> `1.6.0` |
| `major` | 破坏性变更 | `1.5.0` -> `2.0.0` |

tag 使用 `v` 前缀，`pyproject.toml` 版本号使用纯版本号：

```toml
version = "1.5.1"
```

```bash
git tag -a v1.5.1 -m "Release 1.5.1"
```

## 发布前检查

确认工作区状态：

```bash
git status --short
```

运行本地检查：

```bash
uv tool run ruff check .
uv tool run ruff format --check .
uv tool run ty check
uv run --extra dev pytest
uv build
```

确认 CLI 可运行：

```bash
uv run memo --version
uv run memo --help
```

## 准备 GitHub Secrets

发布 workflow 使用这些 secrets：

- `PYPI_TOKEN`：发布到 PyPI
- `HOMEBREW_TAP_TOKEN`：写入 `coderfee/homebrew-tap`

`HOMEBREW_TAP_TOKEN` 推荐使用 fine-grained personal access token：

- Repository access：只选 `coderfee/homebrew-tap`
- Contents：Read and write
- Metadata：Read-only

配置位置：

```text
coderfee/a-memo -> Settings -> Secrets and variables -> Actions
```

## 发布步骤

1. 更新版本号：

   ```bash
   # 编辑 pyproject.toml
   version = "1.5.1"
   ```

2. 提交版本变更：

   ```bash
   git add pyproject.toml
   git commit -m "chore: bump version to 1.5.1"
   git push
   ```

3. 创建并推送 tag：

   ```bash
   git tag -a v1.5.1 -m "Release 1.5.1"
   git push origin v1.5.1
   ```

4. 观察 GitHub Actions：

   ```bash
   gh run list --workflow Release --limit 5
   gh run watch
   ```

## 发布后验证

验证 GitHub Release：

```bash
gh release view v1.5.1 --json tagName,url,assets
```

Release assets 应包含：

- `a_memo-1.5.1-py3-none-any.whl`
- `a_memo-1.5.1.tar.gz`
- `memo-macos-arm64.tar.gz`
- `memo-macos-x86_64.tar.gz`
- `memo-linux-x86_64.tar.gz`
- `memo-windows-x86_64.zip`

验证 PyPI：

```bash
pip install a-memo==1.5.1 --dry-run
```

验证 Homebrew tap：

```bash
gh repo view coderfee/homebrew-tap --json url,defaultBranchRef
gh api repos/coderfee/homebrew-tap/contents/Formula/a-memo.rb --jq .html_url
brew update
brew install coderfee/tap/a-memo
memo --version
```

验证 Formula 内容：

```bash
gh api repos/coderfee/homebrew-tap/contents/Formula/a-memo.rb --jq .content | base64 --decode
```

## Homebrew Formula 本地生成

发布 workflow 会自动下载 macOS release assets 并生成 Formula。本地调试命令：

```bash
python3 scripts/homebrew_formula.py \
  --version 1.5.1 \
  --arm64 memo-macos-arm64.tar.gz \
  --x86-64 memo-macos-x86_64.tar.gz
```

输出路径：

```text
packaging/homebrew/a-memo.rb
```

## 常见处理

### tag 已推送，workflow 失败

修复 workflow 或代码后，删除远端 tag，再重新创建同名 tag：

```bash
git tag -d v1.5.1
git push origin :refs/tags/v1.5.1
git tag -a v1.5.1 -m "Release 1.5.1"
git push origin v1.5.1
```

### PyPI 已发布，后续步骤失败

保留已发布版本，修复问题后发布下一个 patch 版本，例如 `1.5.2`。

### Homebrew tap 更新失败

检查 secret 权限：

```bash
gh repo view coderfee/homebrew-tap --json nameWithOwner,visibility,defaultBranchRef
```

确认 `HOMEBREW_TAP_TOKEN` 对 `coderfee/homebrew-tap` 具备 Contents read/write 权限，然后重新运行失败的 GitHub Actions job。

### Formula checksum 需要手动更新

下载 release assets 并生成 Formula：

```bash
gh release download v1.5.1 \
  --pattern "memo-macos-arm64.tar.gz" \
  --pattern "memo-macos-x86_64.tar.gz"

python3 scripts/homebrew_formula.py \
  --version 1.5.1 \
  --arm64 memo-macos-arm64.tar.gz \
  --x86-64 memo-macos-x86_64.tar.gz
```

复制生成文件到 tap 仓库：

```bash
cp packaging/homebrew/a-memo.rb ../homebrew-tap/Formula/a-memo.rb
```
