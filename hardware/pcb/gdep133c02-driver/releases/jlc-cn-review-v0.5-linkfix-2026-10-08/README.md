# v0.5-linkfix 嘉立创制造审阅包

2026-10-08，KiCad 10.0.6。对应当前 v0.5-GDRC-DEBUG 原生原理图/PCB：P4新增R49（0Ω/0805）、TP25/TP26，R13在栅极侧。详见[调试说明](../../docs/gdrc-debug-v0.5.md)和[下单必读](../../../../../docs/raw/嘉立创下单必读.md)。

- `gdep133c02-driver-gerber-rs274x.zip`：四层制板Gerber和PTH/NPTH钻孔，11个文件。
- `gdep133c02-driver-bom-all.csv`：38组、103个完整装配件，自行采购使用。
- `gdep133c02-driver-bom-smt.csv`：36组、101个顶面贴片件。
- `gdep133c02-driver-cpl-smt.csv`：101个顶面贴片坐标，数值毫米。
- `gdep133c02-driver-bom-manual.csv`：J1/J2两个直插排针。
- `positions-kicad.csv`：KiCad原始坐标，供核对。
- `stencil-optional/`：可选顶面钢网层，单独保存。

TP1–TP26是铜测试点，全部DNP，不进入采购BOM或CPL。正常工作必须装R49；不能将此调试断点空焊。不要混用v0.4与v0.5制造文件。

ERC 0；完整DRC 0、未连接0、原理图一致性问题0；317个连接引脚与设计记录和PCB一致；原生重新铺铜与KiCad GUI实际打开通过。源文件和产物SHA256见[verification.json](verification.json)。没有上传、付款或下单。

本包仍供工程样板审阅。嘉立创库存/料号匹配、装配方向与实物配接、功率/容量及上电显示/安全掉电尚未验收；新增断点不代表Q7驱动匹配已经实测确认。

本包由正式关联修复后的CAD重新导出。默认KiCad更新预览不重复添加元件，检查脚本新增129个关联校验。制板几何及BOM/CPL与原v0.5相同，仅关联和检查来源更新，详见[关联修复记录](../../docs/pcb-link-fix-2026-10-08.md)。
