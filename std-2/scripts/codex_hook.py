#!/usr/bin/env python3
"""
Codex pre-commit hook wrapper
使用 Codex 进行代码审查
"""
import subprocess
import sys
import os


def run_codex_check(filenames):
    """运行 Codex 检查指定文件"""
    if not filenames:
        print("No files to review")
        return 0

    print(f"Running Codex on {len(filenames)} file(s)...")

    # 构建 Codex 命令
    cmd = ["npx", "@anthropic-ai/codex", "check"] + filenames

    try:
        result = subprocess.run(
            cmd,
            capture_output=False,
            text=True,
            env={**os.environ, "CLAUDE_API_KEY": os.environ.get("ANTHROPIC_API_KEY", "")}
        )
        return result.returncode
    except FileNotFoundError:
        print("Error: npx not found. Please install Node.js and npm.")
        return 1
    except Exception as e:
        print(f"Error running Codex: {e}")
        return 1


if __name__ == "__main__":
    # 从命令行参数获取要检查的文件
    # pre-commit 会传递修改的文件列表
    filenames = sys.argv[1:]
    sys.exit(run_codex_check(filenames))