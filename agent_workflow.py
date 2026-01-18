#!/usr/bin/env python3
"""
Claude Agent SDK 驱动的小红书笔记生成工作流

使用方法:
    python agent_workflow.py

环境变量:
    ANTHROPIC_API_KEY - Claude API 密钥
    FEISHU_APP_ID, FEISHU_APP_SECRET, FEISHU_APP_TOKEN, FEISHU_TABLE_ID - 飞书配置
    REPLICATE_API_TOKEN - Replicate API Token
"""
import asyncio
import json
import os
import sys
from pathlib import Path

# 添加 scripts 目录到路径
SCRIPT_DIR = Path(__file__).parent / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

try:
    from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, TextBlock
except ImportError:
    print("错误: 请安装 claude-agent-sdk: pip install claude-agent-sdk")
    sys.exit(1)


def get_system_prompt() -> str:
    """读取 CLAUDE.md 作为系统提示"""
    claude_md = Path(__file__).parent / "CLAUDE.md"
    if claude_md.exists():
        return claude_md.read_text(encoding="utf-8")
    return """你是一个小红书笔记自动化助手。你的任务是：
1. 选择下一篇未使用的笔记
2. 生成图片提示词
3. 调用 Replicate 生成图片
4. 上传内容到飞书多维表格
5. 更新使用日志"""


def validate_environment() -> bool:
    """验证必要的环境变量"""
    required = [
        "ANTHROPIC_API_KEY",
        "FEISHU_APP_ID",
        "FEISHU_APP_SECRET",
        "FEISHU_APP_TOKEN",
        "FEISHU_TABLE_ID",
        "REPLICATE_API_TOKEN",
    ]
    missing = [var for var in required if not os.environ.get(var)]
    if missing:
        print(f"错误: 缺少环境变量: {', '.join(missing)}")
        return False
    return True


async def run_workflow():
    """运行完整的笔记生成工作流"""
    
    # 1. 选择下一篇笔记
    print("📋 步骤 1: 选择下一篇笔记...")
    from select_next_note import select_next_note
    note_id = select_next_note()
    if not note_id:
        print("❌ 没有可用的笔记")
        return False
    print(f"   ✓ 选中笔记: {note_id}")
    
    # 2. 生成提示词
    print(f"📝 步骤 2: 生成图片提示词...")
    from generate_prompts import generate_prompts
    import subprocess
    result = subprocess.run(
        [sys.executable, str(SCRIPT_DIR / "generate_prompts.py"), "--note_id", note_id],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        print(f"❌ 生成提示词失败: {result.stderr}")
        return False
    print(f"   ✓ {result.stdout.strip()}")
    
    # 3. 生成图片
    print(f"🎨 步骤 3: 使用 Replicate 生成图片...")
    result = subprocess.run(
        [sys.executable, str(SCRIPT_DIR / "generate_images.py"), "--note_id", note_id],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        print(f"❌ 生成图片失败: {result.stderr}")
        return False
    print(f"   ✓ 图片生成完成")
    
    # 4. 上传到飞书
    print(f"☁️ 步骤 4: 上传到飞书...")
    result = subprocess.run(
        [sys.executable, str(SCRIPT_DIR / "upload_to_feishu.py"), "--note_id", note_id],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        print(f"❌ 上传失败: {result.stderr}")
        return False
    print(f"   ✓ 上传完成")
    
    # 5. 更新日志
    print(f"📊 步骤 5: 更新使用日志...")
    result = subprocess.run(
        [sys.executable, str(SCRIPT_DIR / "update_log.py"), "--note_id", note_id],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        print(f"❌ 更新日志失败: {result.stderr}")
        return False
    print(f"   ✓ 日志已更新")
    
    print(f"\n✅ 笔记 {note_id} 生成完成!")
    return True


async def run_with_claude():
    """使用 Claude Agent SDK 运行工作流（智能模式）"""
    print("🤖 启动 Claude Agent 模式...")
    
    options = ClaudeAgentOptions(
        system_prompt=get_system_prompt(),
        max_turns=10,
    )
    
    prompt = """请执行小红书笔记生成工作流：
1. 运行 `python scripts/select_next_note.py` 选择下一篇笔记
2. 运行 `python scripts/generate_prompts.py --note_id <ID>` 生成提示词
3. 运行 `python scripts/generate_images.py --note_id <ID>` 生成图片
4. 运行 `python scripts/upload_to_feishu.py --note_id <ID>` 上传到飞书
5. 运行 `python scripts/update_log.py --note_id <ID>` 更新日志

请依次执行这些步骤，并报告结果。"""

    try:
        async for message in query(prompt=prompt, options=options):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(block.text)
    except Exception as e:
        print(f"Claude Agent 执行出错: {e}")
        print("回退到直接执行模式...")
        return await run_workflow()
    
    return True


async def main():
    """主入口"""
    if not validate_environment():
        sys.exit(1)
    
    # 检查是否在 GitHub Actions 环境
    is_github_actions = os.environ.get("GITHUB_ACTIONS") == "true"
    
    # 在 GitHub Actions 中使用简单模式，本地可以使用 Claude 模式
    use_claude = os.environ.get("USE_CLAUDE_AGENT", "false").lower() == "true"
    
    if use_claude and not is_github_actions:
        success = await run_with_claude()
    else:
        # 直接执行模式（更可靠）
        success = await run_workflow()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
