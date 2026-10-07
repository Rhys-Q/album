# GDEP133C02驱动板：v0.5 GDRC调试版

2026-10-07，KiCad **10.0.6**。已移除L4/L5，以EPD_3V3统一开关后供电；已更新原生原理图与PCB，更新P1供电铜线和铺铜，完整ERC/DRC均为零。**103个装配件＝101个顶面贴片＋J1/J2两个直插排针**；26个测试点是铜焊盘，全部DNP。

这版按用户接受的软件上下电约束减少器件，移除17只0Ω及接口隔离电路，U5改为TPS22917DBVR/SOT-23-6并新增1nF软启动电容。功率级、温度检测和高压储能保留。详见[简化改版记录](docs/hand-solder-simplification.md)。

打开[gdep133c02-driver.kicad_pro](gdep133c02-driver.kicad_pro)。入口原理图含power/panel/interface三页；本地符号、封装及必要模型随工程保存。当前版本已在KiCad GUI实际打开并核对原理图与PCB。电气性能、实物连接器配接和安全掉电尚未实测；制造文件仍是审阅包。

## 当前文件

- [整套原理图PDF](reports/schematic.pdf)
- [电源详解](docs/power-circuit-explained.md)、[面板详解](docs/panel-circuit-explained.md)、[接口详解](docs/interface-circuit-explained.md)
- [必须遵守的主机上下电约定](docs/interface-power-state.md)、[主控引脚表](docs/host-interface.csv)
- [KiCad学习教程](docs/learning-guide.md)
- [v0.5嘉立创兼容审阅包](releases/jlc-cn-review-v0.5-2026-10-07/README.md)
- [嘉立创下单必读](../../../docs/raw/嘉立创下单必读.md)

## 检查与生产边界

ERC 0；DRC 0、未连接0、一致性问题0；317个连接引脚与设计记录及PCB焊盘一致。无DRC排除或忽略规则。原生pcbnew完成重新铺铜，最终未修改的KiCad CLI完成检查。记录见[验证状态](reports/validation-status.json)、[源文件哈希](reports/check-provenance.json)。GUI实际打开已通过；实物验收缺口已记录，release_allowed=false。

只接受稳压3.3V台式电源和外接3.3V主控，所有地共地；无5V降压、电池、USB、SD或固件。J2.16已改为NC。没有硬件信号隔离：主控先上电、最后断电，屏幕关机前完成命令并将所有输出低、输入无上拉，禁止热插拔。

PCB仍为100×80mm、4层、1.6mm，层序F.Cu/In1.Cu/In2.Cu/B.Cu；In1为GND平面，正反面GND铺铜。最小线宽与间距0.2mm，输入原有0.8mm、功率核心0.5mm；P1新增逻辑连接0.5mm、功率连接0.8mm，逻辑与FPC扇出0.2mm。过孔0.6/0.3mm。四个Ø3.2mm NPTH安装孔的板框相对坐标为(5,5)、(95,5)、(5,75)、(95,75)mm。

绝对板框左上(50,50)、右下(150,130)mm，制造坐标沿用KiCad输出，不独立平移Gerber或CPL。CPL全部顶面；实际元件旋转和连接器接触面仍须核对。[待验收项目](docs/design-review.md)包括有效容量、RMS/峰值电流、Kelvin误差、浪涌、温升和全轨掉电。

## 修改与历史

原生CAD为真源。`design-data.json`记录固定接法，不承诺自动反向同步。修改后重新运行KiCad ERC/DRC、铺铜与导出；新导出器[scripts/export_hand_solder.py](scripts/export_hand_solder.py)使用KiCad内置Python，拒绝覆盖已有版本目录，后续导出应改为新的版本路径。`scripts/check_design.py`检查报告来源、连接、BOM数量和固定引脚。

`cad-review-2026-10-01`和`jlc-cn-review-2026-10-03`是简化前历史包，129个装配件，与当前v0.5不再一致，不能混用。旧STEP、重画专项PDF、旧同步报告也是历史快照；当前学习和制造核对使用上方链接。旧导出器已加保护，避免覆盖历史release。本次改版前源文件保存在`reports/p1-direct-v0.4/before/`，v0.3前的源文件及教程在`reports/hand-solder-v0.3/before/`；不修改用户的`.history`。

P1本次改版说明：[v0.4直供设计](docs/p1-direct-supply-v0.4.md)。v0.3审阅包保留作历史快照，与当前设计不一致。

P4新增R49（0Ω/0805）、TP25/TP26；R13保留在Q7栅极侧，详见[GDRC调试说明](docs/gdrc-debug-v0.5.md)。v0.4审阅包为历史快照，不能与v0.5混用。
