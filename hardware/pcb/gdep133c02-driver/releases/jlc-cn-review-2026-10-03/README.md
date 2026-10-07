# 嘉立创国内站兼容审阅包

2026-10-03，KiCad 10.0.6。未上传、未下单、未生产放行。

- PCB上传：`gdep133c02-driver-gerber-rs274x.zip`，9层RS-274-X Gerber及2份钻孔。
- 顶面SMT BOM：`gdep133c02-driver-bom-smt.csv`，41组、127个器件。
- SMT坐标：`gdep133c02-driver-cpl-smt.csv`，127项，数字单位为毫米。
- 手工装配：`gdep133c02-driver-bom-manual.csv`，J1、J2，不上传为SMT BOM。
- `positions-kicad.csv`保留原始坐标；`verification.json`记录源文件、产物哈希及兼容转换核对。

几何、位号、完整MPN、坐标原点和旋转保持不变。制造物料编号与库存未匹配；不声明已通过平台导入或实物验证。使用已保存覆铜，未重新填充或保存PCB。

下单前阅读[嘉立创下单必读](../../../../../docs/raw/嘉立创下单必读.md)。
