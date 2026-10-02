# CAD 修复记录（2026-10-01）

初次完整DRC：238条违规、53个未连接、196个原理图一致性问题。最终检查：上述三项均为0，ERC也是0。真实报告见reports/drc.json和erc.json，检查对应源哈希见check-provenance.json。

- 修复Footprint字段、MPN/Manufacturer/Datasheet、DNP、测试焊盘、安装孔和NC网络的原理图一致性。
- 调整重叠器件与丝印，依据Xunpu图修正60针FPC信号焊盘及固定脚，重新布线。
- 重布0.8mm输入和0.5mm电源核心路径，FPC扇出与信号至少0.2mm；增加In1地平面和表面GND铺铜及连接。
- 修复铜间距、交叉短路、重复/过近过孔、未居中过孔端点与悬空支线。检查规则无排除，五项KiCad默认忽略检查亦启用，最终均为0。
- KiCad原理图自动修复后保存；PCB实际打开及GUI DRC通过。恢复CLI检查，移除过期环境阻塞说明。
- 刷新PDF/STEP/SVG、Gerber/钻孔/BOM/CPL和状态。历史初始化脚本加保护，检查脚本改为读取真实DRC及源哈希，避免写入硬编码旧状态。

制造文件以Gerbonara 1.6.3解析：四铜层、双面阻焊/丝印、四段板框、200个PTH（182过孔+18排针焊盘）及4个NPTH。渲染顶层和内层地平面后实际查看，地平面未被信号走线切断；顶层扇出、铜区间隙和安装孔清晰可见。解析器对KiCad在M95之后的G90有语法提示，文件能完整解析；没有修改KiCad原始钻孔输出。统计见manufacturing-file-check.json，渲染见preview/gerber-*.svg/png。

这些是CAD修复结果，不是功率性能、实物装配或安全掉电的测量结果；下一阶段验收仍见design-review.md及工程README。
