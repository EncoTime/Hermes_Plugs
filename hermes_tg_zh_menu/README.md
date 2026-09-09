# tg_zh_menu

Hermes Agent 插件：把 Telegram 命令菜单（输入 `/` 弹出的列表）描述替换为中文。

## 功能

- 60 条官方命令描述汉化（help / new / status / model 等）
- 词表没有的命令自动回退官方英文，新命令不会显示空白
- 官方未来原生支持描述覆盖时（`description_overrides` 配置），插件自动让位并在日志提示
- 附带检查脚本：官方更新后运行，报告需要补翻译/清理的命令

## 安装

```bash
hermes plugins install EncoTime/Hermes_Plugs/hermes_tg_zh_menu --enable
```

安装后重启 gateway（或重启 Hermes）生效。

## 维护

Hermes 更新后运行检查：

```bash
python3 check_zh_menu.py
```

- 【官方新增】→ 在 `zh_overrides.json` 补翻译，`hermes plugins update tg_zh_menu` 后重启
- 【官方已删除】→ 清理词表对应条目
- 【官方原生支持】→ 停用本插件：`hermes plugins disable tg_zh_menu`

## 自定义词表

环境变量 `TG_ZH_MENU_OVERRIDES` 可指向自定义 JSON 词表路径（默认用插件目录内的）。

## 卸载

```bash
hermes plugins remove tg_zh_menu
```

## License

MIT
