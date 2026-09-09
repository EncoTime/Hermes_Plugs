# Hermes_Plugs

Hermes_Plugs：Hermes Agent 插件仓库 —— CoffeeOwl 的自有插件集合。

## 项目地图

| 插件 | 概况 |
|------|------|
| [hermes_tg_zh_menu](hermes_tg_zh_menu/) | 把 Telegram 命令菜单（输入 `/` 弹出的列表）描述替换为中文；词表外命令回退官方英文，官方原生支持描述覆盖时自动让位。详见其 [README](hermes_tg_zh_menu/README.md) |

## 安装到 Hermes

```bash
hermes plugins install EncoTime/Hermes_Plugs/hermes_tg_zh_menu --enable
```

安装后重启 gateway 生效；`hermes plugins disable <name>` + 重启即可停用。

## 相关

- 上游：[NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) 插件规范
