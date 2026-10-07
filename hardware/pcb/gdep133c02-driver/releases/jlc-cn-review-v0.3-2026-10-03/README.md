# v0.3手焊版：嘉立创兼容制造审阅包

2026-10-03，KiCad10.0.6。此包对应当前v0.3原生原理图与PCB；104个装配件（102个顶面SMT＋J1/J2两个排针）。旧129件版本不能与本包混用。

| 文件 | 用途 |
|---|---|
| `gdep133c02-driver-gerber-rs274x.zip` | 裸PCB：9份RS-274-X Gerber＋PTH/NPTH钻孔，四层100×80mm |
| `gdep133c02-driver-bom-all.csv` | 手焊完整采购BOM：104件，39组 |
| `gdep133c02-driver-bom-smt.csv` | 如改用SMT：102件，37组 |
| `gdep133c02-driver-bom-manual.csv` | J1/J2两只手工直插排针 |
| `gdep133c02-driver-cpl-smt.csv` | 102个SMT坐标，纯数字毫米，全部T顶面 |
| `positions-kicad.csv` | 原生坐标核对，不优先上传 |
| `gerber/*drl_map.pdf`、钻孔报告 | 钻孔审阅，不包含在制板ZIP |
| `stencil-optional/*F_Paste.gtp` | 可选顶面钢网层，不包含在制板ZIP |
| `verification.json` | CAD与产物SHA256、检查状态 |

TP1–TP24是DNP铜测试点，不买不贴。移除的0Ω和隔离器件也不购买；U5为TPS22917DBVR/SOT-23-6，新增C36为1nF/50V C0G0805。Gerber与CPL沿用原生坐标，不单独平移或镜像。核对实际元件旋转、连接器Pin1与接触面。

原生重新铺铜完成；未修改的KiCad CLI检查ERC0、DRC0、未连接0、一致性问题0；317个连接引脚逐脚核对。当前GUI打开被工具拒绝，平台导入、物料库存、供电波形、掉电与显示实测未完成，因此production_released=false。本包用于审阅与工程样板准备，没有上传或下单。

主控3.3V、J2.16 NC；无硬件隔离，必须按[上下电约定](../../docs/interface-power-state.md)接线和操作。流程见[下单必读](../../../../../docs/raw/嘉立创下单必读.md)。
