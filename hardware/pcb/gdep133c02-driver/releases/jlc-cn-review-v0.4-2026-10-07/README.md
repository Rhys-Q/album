# v0.4 嘉立创制造审阅包

2026-10-07，KiCad 10.0.6。P1已删除L4/L5，开关后供电合并为EPD_3V3并用铜线直连。当前102个装配件：100个顶面SMT、J1/J2两个直插排针；24个铜测试点DNP。

| 文件 | 用途 |
|---|---|
| gdep133c02-driver-gerber-rs274x.zip | 裸板：9个RS-274X Gerber与PTH/NPTH两个钻孔文件 |
| gdep133c02-driver-bom-all.csv | 自己采购全部102件，共37组 |
| gdep133c02-driver-bom-smt.csv | SMT采购/上传：100件，共35组 |
| gdep133c02-driver-cpl-smt.csv | SMT坐标：100项，mm，全部顶面T |
| gdep133c02-driver-bom-manual.csv | J1/J2两件手工直插 |
| positions-kicad.csv | KiCad原始坐标核对文件 |
| stencil-optional/ | 可选顶面钢网Gerber，手焊不要求购买 |
| verification.json | CAD来源及产物SHA256、数量与检查结果 |

ERC0、DRC违规/未连接/原理图一致性问题均0，313个连接引脚逐脚一致。当前GUI打开被电脑控制工具拒绝，硬件测试、平台解析/库存匹配和装配方向验收尚未完成。此包未生产放行；旧v0.3仍保留，但不能混用。

详细说明：[P1改版](../../docs/p1-direct-supply-v0.4.md)、[嘉立创下单必读](../../../../../docs/raw/嘉立创下单必读.md)。
