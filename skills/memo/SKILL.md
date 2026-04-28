---
name: memo
description: >
  轻量 memo 工具，供 AI agent 使用。用于记录、检索、回顾和生成分享图。
---

# memo

用于快速记录想法、摘录、日常碎片和待回顾内容。优先使用现有命令完成操作，避免改动脚本。

## 操作权限

查询类操作可以直接执行：`list`、`search`、`tags`、`review`、`links`、`image`、`init`、`rebuild-fts`、`flomo-import --dry-run`。

写入类操作必须由用户显式指定后才能执行：`add`、`update`、`delete`、`tag`、`link`、`unlink`、`review --push`、正式导入 flomo。

涉及数据破坏的操作必须由用户显式指定：`reset --force`。

不要根据对话内容自动创建、删除或修改 memo。用户只是在表达想法、摘录内容或讨论文本时，只能回答或建议命令，不能代为写入。

## 初始化

首次使用或数据库异常时，直接运行 `memo init`（表会自动创建）。
需要清空所有数据时，使用 `memo reset --force`。

## 常用操作

### 添加

```bash
memo add “内容文字” #tag1 #tag2
```

内容里的 `#tag` 会作为标签保存；正文展示时保持干净。

### 列表

```bash
memo list
memo list #tag
memo list --limit 20
```

### 搜索

```bash
memo search “关键词”
```

### 回顾

```bash
memo review
memo review --count 10
memo review --count 1 --push
```

定时任务默认使用 `memo review --count 1 --push`。

`review` 输出 JSON 数组，代码层面不做展示格式化。拿到 JSON 后按以下模板呈现给用户，注意换行和排版：

```markdown
### 📝 Memo 回顾 · #ID

#tag1 #tag2

content xxx

📋 YYYY/MM/DD HH:mm(created_at) · 回顾 N 次

相关 memo：
- #ID relation_type：#tag content
```

`links` 为空时省略”相关 memo”区块。

每次 `memo review --push` 有结果时，会追加写入 `~/.memo/history/yyyy-mm-dd.md`：

```markdown
HH:mm
#tag memo
---
```

需要生成分享图时，使用 JSON 里的 `id`。

### 分享图

```bash
memo image <编号> --format png
memo image <编号> --format svg
```

优先生成 PNG。默认保存到 `~/.memo/images/`。

### 删除

```bash
memo delete <编号>
```

### 更新

```bash
memo update <编号> “新的内容”
memo update <编号> “新的内容 #tag”
```

更新内容里带标签时会同步更新标签；没有标签时保留原标签。

### 标签

```bash
memo tags
memo tag <编号> #newtag
```

### 标签策略

当用户想给一条 memo 精心挑选标签时，按以下步骤操作：

1. **先看全局标签**：`memo list --limit 500` 列出所有 memo，从中提取用户已有的标签体系
2. **建议符合层级的标签**：优先推荐与现有层级一致的嵌套标签（如 `#area/心理认知/当下`），避免凭空创建新的顶层标签
3. **加完检查关联 memo**：如果该 memo 有 `link` 关联的其他 memo，主动询问是否要给关联 memo 也加上同样的标签，保持语义一致性

`tag` 命令每次会**替换**全部标签，不是追加。如果要保留旧标签，必须一并传入。

关联为逻辑双向关系。底层只保存一条关系，查看任意一端都会显示另一端。

```bash
memo link <编号1> <编号2>
memo link <编号1> <编号2> --type supports --note “提供案例”
memo links <编号>
memo unlink <编号1> <编号2>
```

关联类型：

- `related`：普通相关，默认值
- `supports`：一条 memo 支撑另一条 memo
- `contrasts`：两条 memo 形成对照

当用户在飞书中说”把这条和 #23 关联””#12 支撑 #45””删除 #12 和 #45 的关联”时，先确认当前 memo 编号可用，再执行对应命令。

### 导入 flomo

```bash
memo flomo-import <flomo.html>
memo flomo-import <flomo.html> --dry-run
```

导入前可用 `--dry-run` 预览结果；确认后再正式导入。

## 排错

### 搜索结果异常

先重建搜索索引：

```bash
memo rebuild-fts
```

### 分享图生成失败

优先使用 PNG。PNG 失败时再生成 SVG 作为替代：

```bash
memo image <编号> --format png
memo image <编号> --format svg
```

PNG 需要本机可用的 Chrome 和 `uv`。缺少环境时，向用户说明 PNG 生成依赖未就绪，并提供 SVG 文件。

### 导入结果不符合预期

先用 dry-run 预览：

```bash
memo flomo-import <flomo.html> --dry-run
```

确认解析数量和内容后再正式导入。

### 找不到 memo

先用列表或搜索确认编号：

```bash
memo list --limit 20
memo search “关键词”
```
