# 设计变更与尚待审核

基线为归档的13.3E6 V1.0外围图及`pin-map.csv`的采用连接字段。BS0/BS1、D/C、DRVN2采用用户已接受的方案，不修改厂家原始文件。

- Q1/Q4完整型号DMN3065LW-7是SOT-323，不能按名称相似改成SOT-23；Q8是DMP3068L-7/SOT-23，Q7沿用PJA3433/P沟道、G1/S2/D3。规格书GDRC说明称N沟道，与参考Q7及Panjit料号有差异，本轮保留参考器件和拓扑，需要控制波形及实测审核。
- U5使用TPS22913BYZVT，A1=VOUT、A2=VIN、B1=GND、B2=ON；YZV为0.5mm间距2×2球、约0.89mm边长，依据已归档TI手册p36。模型缺失，因此从封装删除失效全局模型引用；当前STEP不包含U5实体。
- U1/U2/U3使用0.2Ω采样电阻候选WSL1206R2000FEA。采样连接分别为RESEP到GND、AVDD到RESEN节点、AVDD到RESEC节点；原厂WSL资料已归档：1206额定0.25W（70°C），0.2Ω对应连续RMS约1.12A；按50%功率预算为0.79A。尚无三路电感实际RMS/峰值/占空比，不能用输入987.4mA代替各支路电流。若超过预算，须升级采样电阻功率与封装并重布，不可仅改BOM。
- L1–L3候选MSS1246-153MLC/15µH，原厂系列表的Isat是指定下降比例下的电流，不是电路已经测得的峰值。封装采用KiCad MSS1246T图库；已核对归档MSS1246原厂图：12.0±0.3mm方形、4.6±0.2mm高，推荐焊盘中心距8.5mm、4.0×5.5mm；现有封装旋转90°后对应此焊盘，尺寸一致。15µH料号DCR最大54.1mΩ，25°C下10%电感下降电流4.58A，20°C温升Irms2.85A；这些是器件数据，不能证明实际环路峰值符合要求。
- C1–C6每个33µF参考节点改为三只10µF和一只3.3µF、50V陶瓷并联，名义33.3µF。原位号C1–C6各为其中一只10µF，新增C103–C120对应其余器件。这是候选工程改动：尚未取得全部偏压曲线和轨电压上限，不能认定等效于参考图或符合有效容量要求。若原厂曲线和环路审核不支持，必须恢复合适的33µF单件或重新选择电容组合与封装。
- 其他高压电容的候选耐压50V，输入逻辑侧100µF候选6.3V。候选型号不等于有效容量已达标，也不等于已验证供货。
- R24/R25从参考图到GND改为到VDD；D/C直接接地；SI2/SI3增加弱下拉；保持源极配对、内部VCC连接、温度传感器供电域和BUSY上拉来源。
- 已重布输入0.8mm、电源核心0.5mm走线，信号与FPC扇出最小0.2mm；过孔0.6/0.3mm。增加In1.Cu连续GND平面及正反面铺铜，删除悬空支线并补齐连接。KiCad完整DRC、原理图一致性均为零；仍须审核功率回路寄生、采样Kelvin误差、窄扇出压降及瞬态温升。网络类优选宽度不表示整条网络每一段都达到该宽度。

项目库中标准封装及其可取得模型来自本机KiCad 10.0.6官方安装的图库，保留原描述及生成信息；遵循KiCad图库CC-BY-SA 4.0及设计使用例外。项目自定义符号与FPC封装由本项目管理；FPC焊盘已依据原厂图修正，见fpc-footprint-review.md。旧UNVERIFIED文件仅为历史记录，工程不再引用。

关键在线资料：[DMN3065LW](https://www.diodes.com/part/view/DMN3065LW)、[DMP3068L](https://www.diodes.com/datasheet/download/DMP3068L.pdf)、[PJA3433](https://www.panjit.com.cn/upload/datasheet/PJA3433.pdf)、[SN74LVC244A](https://www.ti.com/lit/ds/symlink/sn74lvc244a.pdf)、[MSS1246-153](https://www.coilcraft.com/en-us/products/power/shielded-inductors/ferrite-drum/mss-mos/mss1246/mss1246-153/)。在线资料没有全部下载归档，也没有声称全部器件选型已完成。

原厂资料：[WSL规格书](https://www.vishay.com/docs/30100/wsl.pdf)、[MSS1246规格书](https://www.coilcraft.com/getmedia/960fadbe-0ca0-40e2-ae20-64edb15f3a07/mss1246.pdf)，PDF归档在sources/。电容偏压/环路与实物匹配未验收，因此制造导出当前为审阅包，release_allowed=false。
