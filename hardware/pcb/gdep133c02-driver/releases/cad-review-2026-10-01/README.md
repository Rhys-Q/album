# CAD 审阅包（未生产放行）

来源为本目录上两级的KiCad 10.0.6原生工程，ERC/DRC零违规；源哈希与状态见reports/。Gerber共四铜层、双面阻焊/丝印及板框，钻孔分PTH/NPTH；无盲埋孔。100×80mm、四层、1.6mm。

bom.csv由PCB字段按料号/封装分组，排除DNP和测试焊盘；THT输入/主控排针需手工装配。坐标表仅包含SMD且排除DNP；cpl-jlc-review.csv是嘉立创列格式，未绑定立创料号，旋转需装配预览复核。绝对原点与KiCad一致，不单独偏移文件。

连接器实物方向、有效电容量、采样功率及瞬态环路仍待验收，不能凭DRC通过直接接屏或放行装配。完整门槛见工程README和docs/design-review.md。没有上传文件、报价或下单。
