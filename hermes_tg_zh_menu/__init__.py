"""Hermes 插件：Telegram 命令菜单汉化。

在插件注册时对 hermes_cli.commands_platforms.telegram_bot_commands 做 monkey-patch，
把描述替换为词表中的中文。词表不存在的命令回退官方英文描述。

若官方源码原生支持 description_overrides / command_descriptions 配置，本插件自动让位
（不再打补丁）并在日志提示改用官方功能。
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

# 词表优先取插件目录内的 zh_overrides.json（自包含，随仓库分发），
# 可用环境变量 TG_ZH_MENU_OVERRIDES 指向自定义词表。
OVERRIDES_PATH = Path(
    os.environ.get(
        "TG_ZH_MENU_OVERRIDES",
        str(Path(__file__).resolve().parent / "zh_overrides.json")))

_ORIGINAL = None  # 保存原函数，便于卸载/重载


def _load_overrides() -> dict:
    """读取中文词表；读不到返回空 dict（全部回退英文，不影响运行）。"""
    try:
        return json.loads(Path(OVERRIDES_PATH).read_text(encoding="utf-8"))
    except FileNotFoundError:
        logger.warning("[tg_zh_menu] 词表不存在：%s，菜单将保持英文", OVERRIDES_PATH)
    except json.JSONDecodeError as e:
        logger.warning("[tg_zh_menu] 词表 JSON 损坏：%s", e)
    return {}


def _official_native_support() -> bool:
    """检测官方 commands_platforms.py 是否已原生支持描述覆盖。"""
    try:
        import hermes_cli.commands_platforms as m
        return "description_overrides" in Path(m.__file__).read_text(encoding="utf-8")
    except Exception:
        return False


def register(ctx) -> None:
    """插件入口：monkey-patch telegram_bot_commands。"""
    global _ORIGINAL
    import hermes_cli.commands_platforms as m

    if getattr(m.telegram_bot_commands, "_tg_zh_menu", False):
        logger.info("[tg_zh_menu] 已打过补丁，跳过（插件重载场景）")
        return

    if _official_native_support():
        logger.warning(
            "[tg_zh_menu] 检测到官方已原生支持 description_overrides，"
            "本插件不再打补丁；请在 config.yaml 配置官方选项并停用本插件")
        return

    overrides = _load_overrides()
    if not overrides:
        logger.warning("[tg_zh_menu] 词表为空，跳过补丁")
        return

    _ORIGINAL = m.telegram_bot_commands

    def telegram_bot_commands_zh(*, include_plugins: bool = True):
        """中文版菜单命令列表：同名命令用词表覆盖描述，其余回退英文。"""
        pairs = [(cmd.name, overrides.get(cmd.name, cmd.description))
                 for cmd in m._gateway_available_commands()]
        if include_plugins:
            pairs += [(n, overrides.get(n, d))
                      for n, d, hint in m._iter_plugin_command_entries()
                      if not m._requires_argument(hint)]
        return [(tg, desc) for name, desc in pairs
                if (tg := m._sanitize_telegram_name(name))]

    telegram_bot_commands_zh._tg_zh_menu = True
    m.telegram_bot_commands = telegram_bot_commands_zh
    logger.info("[tg_zh_menu] 已挂载：%d 条中文描述生效", len(overrides))
