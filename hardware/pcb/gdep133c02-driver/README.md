# GDEP133C02 驱动板：当前 v0.9 工程

KiCad **10.0.6**，维护日期2026-10-10。正式源文件是本目录的 `.kicad_pro`、四份 `.kicad_sch` 和 `.kicad_pcb`；本地 `lib/`、`models/`、库表及设计规则随工程管理。

打开[gdep133c02-driver.kicad_pro](gdep133c02-driver.kicad_pro)。三张分层原理图对应同一块100×80mm、四层、1.6mm PCB。104个装配件＝102个顶面SMT＋J1/J2两个直插排针；26个DNP铜测试点无需采购，另有4个安装孔。PCB共134个封装。

## 当前资料

- [v0.9选型审查](docs/三组电阻免换料费改版-v0.9.md)、[逐位号对照](docs/逐位号替换对照-v0.9.csv)、[采购清单](docs/采购清单-v0.9.csv)、[手焊说明](docs/手焊说明-v0.9.md)

- [原理图PDF](reports/schematic.pdf)、[PCB顶层PDF](reports/preview/board.pdf)
- [Power详解](docs/power-circuit-explained.md)、[Panel详解](docs/panel-circuit-explained.md)、[Interface详解](docs/interface-circuit-explained.md)
- [当前配置与手焊说明](docs/current-configuration.md)、[P1供电](docs/p1-supply.md)、[GDRC调试](docs/gdrc-debug.md)
- [上下电约定](docs/interface-power-state.md)、[主机引脚表](docs/host-interface.csv)
- [KiCad学习指南](docs/learning-guide.md)、[从原理图到PCB教程](../../../docs/design/从原理图到PCB的KiCad新手教程.md)
- [v0.9 制造审阅包](releases/jlc-cn-review-v0.9-resistors-2026-10-10/README.md)、[嘉立创下单必读](../../../docs/raw/嘉立创下单必读.md)

## 检查与验收

ERC 0；DRC 0、未连接0、原理图一致性问题0；319个连接引脚与设计记录及PCB逐脚对应，130个符号关联通过检查。v0.9正式工程实际打开及“从原理图更新PCB”预览通过，按UUID匹配不重复新增器件，保存后的第二次预览没有待应用操作；FPC固定焊脚61/62的两个提示已明确记录。详见[验证状态](reports/validation-status.json)、[源文件哈希](reports/check-provenance.json)、[符号关联说明](docs/pcb-symbol-links.md)。没有忽略规则或DRC排除。

本版仅更换三组电阻的5个位号，保留0805焊盘/阻值/数量；其余器件和装配方式保持，见[改版说明](docs/三组电阻免换料费改版-v0.9.md)。

只接受稳压3.3V台式电源和3.3V外接主控。无接口硬件隔离，主控先上电、最后断电；屏幕关机前按约定执行命令并将GPIO输出低、输入无上拉，禁止热插拔。R49正常必须装上。电源瞬态、温升、有效容量、实物FPC配接、显示及安全掉电仍待验收，制造文件供工程审阅，[待审核项目](docs/design-review.md)未完成前不视为已验证产品。

层序F.Cu/In1.Cu/In2.Cu/B.Cu；In1为GND平面，顶底面GND铺铜。201个过孔，其中27个GND过孔。最小线宽/铜间距0.2mm，功率核心常用0.5mm、输入及部分供电0.8mm；通孔过孔0.6/0.3mm。四个Ø3.2mm NPTH安装孔相对板框左上角为(5,5)、(95,5)、(5,75)、(95,75)mm。绝对板框(50,50)至(150,130)mm；导出时不要独立平移CPL。

## 维护

原生CAD为真源，`design-data.json`记录固定接法，不自动双向同步。保留三个维护脚本：`check_design.py`检查连接/关联/报告来源，`export_hand_solder.py`检查并导出制造文件，`schematic_sexp.py`解析原生文件。导出器使用KiCad内置Python，拒绝覆盖现有release；下次正式改版应设置新的输出目录，验收新包后只保留最新包。

此前过期release、历史CAD副本、一次性迁移/布线脚本、旧专项报告和本地历史目录已清理。原厂屏幕资料、候选器件资料及总体设计保留。Git负责正式版本历史；自动历史和缓存不纳入当前交付。目录与恢复说明见[仓库维护约定](../../../docs/design/仓库目录与维护约定.md)。
