# GDEP133C02 驱动板 v0.11

当前工程采用用户指定的17组基础库原型方案：147件、145个顶面SMD，其中138个机器贴片、9个手工装配，36组采购型号；100×80mm四层及接口位置保持。3组参数审核通过，14组电气等效未验证。

[改版及验证边界](docs/基础库17组改版-v0.11.md)、[采购清单](docs/采购清单-v0.11.csv)、[逐位号对照](docs/逐位号替换对照-v0.11.csv)、[剩余例外](docs/17组决定及剩余例外-v0.11.csv)。基础库组合补充页 basic-composites.kicad_sch 通过原工程入口加载；原有符号UUID保留。

当前制造审阅包：[v0.11](releases/jlc-cn-review-v0.11-basic17-2026-10-11/README.md)，ERC、DRC、未连接、一致性均为0；KiCad实际更新/保存后无重复新增或待执行变更。实板显示、瞬态、温升、FPC配接及安全掉电尚未验收，C15008 SMT库存仍未知。KiCad10.0.6。

学习资料：[学习指南](docs/learning-guide.md)、[电源](docs/power-circuit-explained.md)、[接口](docs/interface-circuit-explained.md)、[屏幕](docs/panel-circuit-explained.md)。旧v0.9/v0.10文档为历史快照。

2026-10-11装配调整：用户淘宝采购U4/U5/Q3/D3/D5/D6/FPC1并手焊；仅改变机器BOM/CPL分配，电路、PCB和Gerber保持。以assembly-plan.json为当前导出装配规则，CAD中的SMT属性描述此前装配方式。
