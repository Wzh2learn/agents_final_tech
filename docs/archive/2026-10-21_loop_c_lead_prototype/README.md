# 历史 Loop C lead 原型

> 状态: 归档 | 更新: 2026-10-21 | 取代/被取代: 从 GB10 loop_c 历史分支保全；不是当前可运行控制面

来源 HEAD：`815dda50efcbc9bff48348e14634c54002a96c70`。设计与两个原型文件保持 Git 原字节；脚本以 `.txt` 保留供审阅，不进入 `scripts/` 执行面。

- [原架构设计](loop_c_lead_architecture.md)
- [Python 原型](loop_c_lead.py.txt)
- [Shell 原型](loop_c_lead.sh.txt)

只读复核发现 Python 原型的 `ACTIVE` 状态赋值落在错误缩进/不可达路径，mode guard 也没有实现所声称的校验；Python 3.11 另有嵌套 f-string 兼容问题。此次只做历史保全，不修复或激活旧方案，不恢复原 INDEX 的“活跃”脚本条目。

治理报告、接受 REJECT 后的纠正及 packet-only 模型复审见[历史审查身份说明](../../../reports/LC-GOV-002_CONTEXT.md)。当前系统边界见[代码资产地图](../../architecture/codebase_map.md)。
