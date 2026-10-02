# GDEP133C02 最小驱动板：CAD 修复版

2026-10-01，KiCad **10.0.6**。本轮已修复 CAD 连接与设计规则问题，原理图、PCB 均已实际打开验证。实物和关键功率参数尚未验收，当前制造文件用于审阅，尚未生产放行。

2026-10-02，电源页已重画为六个功能区的导线式原理图，器件连接与PCB保持一致，重新执行ERC/DRC通过。本次新页的GUI打开复查因工具访问被拒绝而待完成；上面的实际打开记录为2026-10-01版本。查看[电源页PDF](reports/power-redraw/power.pdf)及[阅读说明](docs/power-redraw.md)。

范围：外接 ESP32-S3 开发板、稳压3.3V限流台式电源，只做最小屏幕驱动硬件；不含固件、电池、SD、USB和整机结构。

2026-10-02，Panel 与 Interface 页也已重画为导线式功能电路，完整网表和器件属性保持一致，最终 ERC/DRC 通过。查看 [Panel PDF](reports/panel-interface-redraw/panel.pdf)、[Interface PDF](reports/panel-interface-redraw/interface.pdf)及[阅读说明](docs/panel-interface-redraw.md)。当前新页的 GUI 打开复查仍因工具拒绝访问而待完成。

学习本工程：[从原理图到 PCB 的实操教程](docs/learning-guide.md)，包含电源与接口讲解、七课练习和自测答案。

电源专项：[电源页原理详解](docs/power-circuit-explained.md)，逐项解释70个元器件、六个功能区、开关周期电流路径、反馈计算及设计理由。

接口与面板专项：[Interface 原理详解](docs/interface-circuit-explained.md)覆盖43个对象及缓冲／使能／默认状态；[Panel 原理详解](docs/panel-circuit-explained.md)覆盖41个器件、温度接口、六组电容及FPC全部60脚。

## 工程和检查

打开 `gdep133c02-driver.kicad_pro`；顶层原理图包含power/panel/interface三页。项目库与可取得的3D模型随工程保存。100×80mm四层板、1.6mm厚；四个Ø3.2mm NPTH安装孔，板框相对位置(5,5)、(95,5)、(5,75)、(95,75)mm。

- ERC：0违规。
- 完整CLI DRC：0违规、0未连接、0原理图一致性问题。
- GUI DRC：0违规、0未连接、0忽略检查；独立PCB编辑器的原理图一致性由CLI另行检查。
- 无DRC排除，无忽略规则；最小铜间距/线宽0.2mm，孔间距0.25mm，铜到板边0.5mm。过孔0.6/0.3mm。
- 输入主回路优选0.8mm、电源核心0.5mm，FPC扇出及信号最小0.2mm；In1.Cu为GND平面，正反面增加GND铺铜与连接。
- 清除元件/丝印重叠、短路、悬空支线及重复过孔，修正器件字段、DNP、NC和安装孔属性的一致性。
- FPC信号焊盘0.30×1.20mm、0.5mm间距，固定脚2.0×1.8mm；已按原厂60针公式修正，不再使用占位封装。

报告见 `reports/erc.json`、`reports/drc.json`、`reports/validation-status.json`；源文件校验哈希见 `reports/check-provenance.json`。最初238条违规、53个未连接和196个一致性问题的报告留作修复历史。原理图曾提示自动修复，已通过编辑器保存为本机原生格式并重新检查。

## 审阅文件

`releases/cad-review-2026-10-01/` 保存四层Gerber、PTH/NPTH钻孔、孔位图、BOM、KiCad坐标和嘉立创格式CPL。`reports/`保存原理图PDF、STEP及top/ground/bottom SVG预览。导出成功不代表制造放行；尚未上传或下单。CPL旋转和连接器方向需结合实际选料检查。

CAD绝对原点为(0,0)，板框左上为(50,50)mm，右下为(150,130)mm；坐标文件使用KiCad导出的毫米和Y轴惯例。不能单独移动Gerber或CPL原点。板厚1.6mm，建议审阅工艺为FR4四层、外层1oz；内层铜厚与介质叠层须在下单时明确，不以默认厚度计算温升。

## 尚待工程验收

1. 实际连接器/屏幕FPC的Pin1、接触面、插入方向和厚度；机械尺寸核对不能代替实物配接。
2. C1–C6组合名义33.3µF，50V陶瓷的有效容量、轨电压边界和控制环路尚未通过审核。
3. 三只0.2Ω采样电阻的RMS/脉冲功率、Kelvin采样误差及电感峰值；具体限制见 `docs/design-review.md`。
4. 器件供货、装配方向和完整BOM复核；U5/FPC缺少精确3D实体，STEP不能作为全部器件的装配空间证明。
5. 限流供电、全轨波形、温升、显示和安全掉电实测，全部未进行。

## 修改和复查

原生KiCad文件为后续修改依据。`design-data.json`保留录入和固定接法记录，不承诺反向同步；历史初始化脚本已加保护，避免覆盖修复后的工程。路由实验不是KiCad DRC或电源性能验收的替代品。

关闭编辑器后，以KiCad内置Python运行 `scripts/export_review.py` 刷新真实ERC/DRC及导出，再用Python运行 `scripts/check_design.py` 检查398个连接管脚、固定接法、本地库和检查报告哈希。检查脚本不会授予生产放行。任何原生源文件修改后须重新执行检查并更新GUI验证记录。
