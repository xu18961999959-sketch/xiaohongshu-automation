# 小红书自动化笔记生成系统

## 项目说明

使用 GitHub Actions + Claude Agent SDK 自动化生成小红书笔记内容，并同步到飞书多维表格。

## 功能特性

- ✅ 自动选择下一篇待发布笔记
- ✅ AI 生成 9 张配图提示词
- ✅ 调用图片生成 API 创建配图
- ✅ 自动上传到飞书多维表格
- ✅ 支持定时执行和手动触发

## 快速开始

### 1. 配置 GitHub Secrets

在仓库 Settings → Secrets and variables → Actions 中添加：

| Secret 名称 | 说明 |
|-------------|------|
| `ANTHROPIC_API_KEY` | Anthropic API 密钥 |
| `FEISHU_APP_ID` | 飞书应用 ID |
| `FEISHU_APP_SECRET` | 飞书应用密钥 |
| `FEISHU_APP_TOKEN` | 飞书多维表格 Token |
| `FEISHU_TABLE_ID` | 飞书表格 ID |
| `REPLICATE_API_TOKEN` | Replicate API Token |

### 2. 手动触发

1. 进入 Actions 标签页
2. 选择 "Xiaohongshu Note Generator"
3. 点击 "Run workflow"

### 3. 定时执行

默认配置为每天北京时间 20:00 自动执行。

## 目录结构

```
├── .github/workflows/     # GitHub Actions 配置
├── scripts/               # Python 脚本
├── data/
│   ├── notes/            # 笔记内容文件
│   └── usage_log.json    # 执行日志
└── CLAUDE.md             # Claude Agent 上下文
```

## 许可证

MIT License
