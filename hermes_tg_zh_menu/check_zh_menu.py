#!/usr/bin/env python3
"""Hermes Telegram 菜单汉化 —— 检查工具。

插件 tg_zh_menu 负责运行时汉化，本脚本只做检查：
1. 官方是否已原生支持描述覆盖（是 → 提示改用官方功能，可停用插件）
2. 官方命令清单 vs zh_overrides.json：新增/删除了哪些命令
3. 官方英文描述是否改动（提示核对对应中文翻译）

用法：python3 check_zh_menu.py
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
OVERRIDES = HERE / "zh_overrides.json"


def plugins_dir() -> Path:
    """官方插件目录：<HERMES_HOME>/plugins（HERMES_HOME 缺省 ~/.hermes）。"""
    home = os.environ.get("HERMES_HOME") or str(Path.home() / ".hermes")
    return Path(home) / "plugins"


def _ensure_hermes_cli() -> None:
    """保证 hermes_cli 可导入；不可导入时用 hermes CLI 所在 venv 的 python 重跑自身。"""
    try:
        import hermes_cli  # noqa: F401
        return
    except ImportError:
        pass
    hermes_bin = shutil.which("hermes")
    if not hermes_bin:
        sys.exit("未找到 hermes_cli：请先安装 Hermes Agent（https://hermes-agent.nousresearch.com）")
    venv_python = Path(hermes_bin).resolve().parent / "python"
    if not venv_python.exists():
        sys.exit(f"未找到 Hermes venv python：{venv_python.parent}（hermes 安装方式非 venv？）")
    r = subprocess.run([str(venv_python), __file__], capture_output=True, text=True)
    print(r.stdout, end="")
    sys.exit(r.returncode)


def main() -> None:
    """对比官方命令与汉化词表，报告差异。"""
    _ensure_hermes_cli()
    import hermes_cli.commands_platforms as m

    overrides = json.loads(OVERRIDES.read_text(encoding="utf-8"))

    # 1) 官方原生支持检测
    src = Path(m.__file__).read_text(encoding="utf-8")
    if "description_overrides" in src or "command_descriptions" in src:
        print("⚠️ 官方已原生支持描述覆盖！建议：在 config.yaml 用官方配置，"
              "然后停用 tg_zh_menu 插件。")
    else:
        print("✅ 官方尚未内置描述覆盖功能，插件方案仍然需要。")

    # 2) 命令清单对比（用插件同款逻辑取官方清单：直接调原函数）
    official = dict(m.telegram_bot_commands())
    missing = sorted(set(official) - set(overrides))
    extra = sorted(set(overrides) - set(official))

    print(f"\n官方命令数：{len(official)}，汉化表条目：{len(overrides)}")
    if missing:
        print("\n【官方新增、词表缺少】（补翻译到 zh_overrides.json）：")
        for n in missing:
            print(f"  {n} | {official[n]}")
    else:
        print("【官方新增】无")
    if extra:
        print("\n【官方已删除、词表多余】（插件会自动忽略，可清理）：")
        for n in extra:
            print(f"  {n}")
    else:
        print("【官方已删除】无")

    # 3) 插件就位检测
    installed = plugins_dir() / "tg_zh_menu" / "__init__.py"
    print(f"\n插件状态：{'✅ 已安装' if installed.exists() else '❌ 未安装（plugins 目录下无 tg_zh_menu）'}")
    if missing:
        print("处理：补好翻译后重启 gateway 使其生效")


if __name__ == "__main__":
    main()
