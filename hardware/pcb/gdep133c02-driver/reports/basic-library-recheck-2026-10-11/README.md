# 2026-10-11 基础库复查证据

这是当前 v0.10-e01 的选型复查，不是制造release。本轮不修改既有release与CAD源文件。

- `products.json`：逐C号公开产品API和国内商品SSR必要字段快照（已去掉图片、有限替代列表等无关字段）。`metadata.productPriceList`来自国际接口，可能为美元，**不用于人民币费用**。`pricing.productPriceList`来自国内替代接口的mainProduct，人民币价。
- `group-review.json`：E02—E25全部24组的实际节点、审核结论和具体证据缺口。
- `datasheet-evidence.json`：原厂PDF阅读状态、页数及SHA256。PDF下载缓存位于 `/tmp/review24-pdfs`，不作为永久相对路径依赖；准确来源URL保存在清单中。通用目录不是具体型号的偏压曲线。
- `baseline-check.json`：与既有release内129项源SHA256核对结果；当前原型号与design-data匹配。原理图—PCB一致性使用当前release已有验收作为基础，没有宣称本轮重新跑过GUI/ERC/DRC。
- `fetch-public-products.py`：正常公开接口查询，原封装不作候选过滤；不解决验证码。已有记录默认不覆盖，重新查询需另建快照，以保留原查询时刻。
- `generate-review.py`：根据本次快照、人工电气审查和正式基线生成报告/CSV。设计基线改变时会停止，不能用旧审查直接套新版。

采购量：`minBuyNumber × theRatio` 得商城MOQ（只），阶梯起点也按购买单位乘theRatio。1/5板、各型号加0/2件备品分别按倍数向上取整。表中不重复累加共享C号MOQ，不用商城价代替SMT价。未知SMT库存不是0，退回扩展标签也不证明没有合作免换料费。

检索来源：国内精确C号商品页（products.json.url）及所附OEM数据手册；嘉立创国际基础库目录 https://jlcpcb.com/parts/basic_parts 为线索；准确型号/参数网络检索包括50V陶瓷、C0G、PNP、双肖特基、LM75和15µH功率电感。第三方表格/索引只提供线索，全部免费判断需回到国内字段；发现C1588被第三方写为C0G，官方参数实际X7R，已拒绝。国际目录C338088以及部分电阻海外Basic线索不能作为国内Basic证据。

国内参数搜索页面在正常公开请求下返回验证页；没有规避验证。浏览器工具 getState 超时并重置，未取得新的登录SMT页合作免换料费/实际订单报价。因此原普通扩展组免费合作身份尚未重新全面核实，报告以“未取得免费证据”表述，不声称全库穷尽或合作库已经查无。
