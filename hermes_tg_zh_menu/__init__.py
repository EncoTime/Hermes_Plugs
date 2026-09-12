"""Hermes 插件：Telegram 命令菜单汉化 + 提示文本汉化。

两部分（插件注册时 monkey-patch，不改官方源码）：
1. telegram_bot_commands：命令描述替换为词表中文，词表外回退英文。
   若官方源码原生支持 description_overrides，本部分自动让位并提示改用官方功能。
2. 提示文本（tips + 会话信息块）：
   - hermes_cli.tips.TIPS 原地替换为 tips_zh.json 中文词表；
   - GatewayTurnMixin._format_session_info 的 ◆ Model/Provider/Context 行换中文标签。
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

TIPS_ZH_PATH = Path(
    os.environ.get(
        "TG_ZH_MENU_TIPS",
        str(Path(__file__).resolve().parent / "tips_zh.json")))

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


def _patch_tips() -> int:
    """把 hermes_cli.tips.TIPS 原地替换为中文词表；返回生效条数。"""
    try:
        import hermes_cli.tips as tips_mod
    except Exception as e:
        logger.warning("[tg_zh_menu] 无法导入 hermes_cli.tips：%s", e)
        return 0
    try:
        zh = json.loads(TIPS_ZH_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError:
        logger.warning("[tg_zh_menu] tips 词表不存在：%s", TIPS_ZH_PATH)
        return 0
    except json.JSONDecodeError as e:
        logger.warning("[tg_zh_menu] tips 词表 JSON 损坏：%s", e)
        return 0
    if not isinstance(zh, list) or not zh:
        logger.warning("[tg_zh_menu] tips 词表为空，跳过")
        return 0
    if tips_mod.TIPS and isinstance(tips_mod.TIPS[0], str) and \
       any("\u4e00" <= ch <= "\u9fff" for ch in tips_mod.TIPS[0]):
        return len(tips_mod.TIPS)  # 已是中文（插件重载场景）
    tips_mod.TIPS[:] = zh  # 原地替换，引用方无需重载
    logger.info("[tg_zh_menu] tips 已中文化：%d 条", len(zh))
    return len(zh)


def _patch_session_info() -> bool:
    """把 _format_session_info 的 ◆ 标签换成中文（仅替换函数体引用，整函数复制打补丁）。"""
    try:
        from gateway import run_turn
    except Exception as e:
        logger.warning("[tg_zh_menu] 无法导入 gateway.run_turn：%s", e)
        return False
    cls = getattr(run_turn, "GatewayTurnMixin", None)
    fn = getattr(cls, "_format_session_info", None) if cls else None
    if fn is None:
        logger.warning("[tg_zh_menu] 未找到 GatewayTurnMixin._format_session_info，跳过")
        return False
    if getattr(fn, "_tg_zh_menu", False):
        return True
    if "ctx_source" not in getattr(fn.__code__, "co_names", ()) and \
       "ctx_source" not in fn.__code__.co_varnames:
        logger.warning("[tg_zh_menu] _format_session_info 结构已变，跳过汉化（官方升级后需核对）")
        return False

    def _format_session_info_zh(self) -> str:
        """◆ 模型 / 提供商 / 上下文 中文版（逻辑镜像官方 _format_session_info）。"""
        from gateway.run import _resolve_gateway_model_context
        from utils import base_url_hostname
        resolved = _resolve_gateway_model_context()
        context_length = resolved.context_length
        ctx_source = {
            "config": "配置",
            "default": "默认 — 在 config 设 model.context_length 可覆盖",
        }.get(resolved.context_source, "已检测")
        ctx_display = (
            f"{context_length / 1_000_000:.1f}M" if context_length >= 1_000_000
            else f"{context_length // 1_000}K" if context_length >= 1_000 else str(context_length)
        )
        lines = [
            f"◆ 模型：`{resolved.model}`",
            f"◆ 提供商：{resolved.provider or 'openrouter'}",
            f"◆ 上下文：{ctx_display} tokens（{ctx_source}）",
        ]
        base_url = resolved.base_url
        if base_url and base_url_hostname(base_url) in ("localhost", "127.0.0.1", "0.0.0.0"):
            lines.append(f"◆ 端点：{base_url}")
        return "\n".join(lines)

    _format_session_info_zh._tg_zh_menu = True
    cls._format_session_info = _format_session_info_zh
    logger.info("[tg_zh_menu] 会话信息块已中文化")
    return True


def register(ctx) -> None:
    """插件入口：monkey-patch 菜单描述 + tips + 会话信息块。"""
    global _ORIGINAL
    import hermes_cli.commands_platforms as m

    if getattr(m.telegram_bot_commands, "_tg_zh_menu", False):
        logger.info("[tg_zh_menu] 已打过补丁，跳过（插件重载场景）")
        return

    tips_n = _patch_tips()
    info_ok = _patch_session_info()

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

    _PLUGIN_EXTRA = [
        (n, overrides.get(m._sanitize_telegram_name(n), overrides.get(n, d)))
        for n, d, hint in m._iter_plugin_command_entries()
        if not m._requires_argument(hint)]

    def telegram_bot_commands_zh(*, include_plugins: bool = True):
        """中文版菜单命令列表：同名命令用词表覆盖描述，其余回退英文。

        词表 key 用 Telegram 口径（下划线），官方注册名可能带连字符
        （codex-runtime / reload-mcp），先 sanitize 再查表。
        """
        def _zh(official_name: str, fallback: str) -> str:
            tg = m._sanitize_telegram_name(official_name)
            return overrides.get(tg, overrides.get(official_name, fallback))
        pairs = [(cmd.name, _zh(cmd.name, cmd.description))
                 for cmd in m._gateway_available_commands()]
        if include_plugins:
            pairs += _PLUGIN_EXTRA[:]
        return [(tg, desc) for name, desc in pairs
                if (tg := m._sanitize_telegram_name(name))]

    telegram_bot_commands_zh._tg_zh_menu = True
    m.telegram_bot_commands = telegram_bot_commands_zh
    logger.info("[tg_zh_menu] 已挂载：%d 条中文描述，tips %d 条，会话信息块%s",
                len(overrides), tips_n, "已汉化" if info_ok else "未动")
