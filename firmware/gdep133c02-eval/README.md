# GDEP133C02 评估板验证固件

适用：自制 gdep133c02-driver v0.11 驱动板 + 微雪 ESP32-S3-DEV-KIT-N8R8 + GDEP133C02。仅提供评估固件，不改变硬件制造文件。

按用户最新要求直接使用本机已安装的 **ESP-IDF v6.1**，提交 `fff9895c82d744c7237be8847347bdd1b07c6643`。本轮不再使用原计划的 5.5.1。默认 8MB Flash、8MB Octal PSRAM、UART0 115200、SPI mode 0 / 1MHz。Wi-Fi/蓝牙不启动，不实现 SD、按键或电池相框逻辑。

## 1. 先接线

先关闭屏幕电源与开发板 USB，核对 J2 的 1 脚标记；下表是 **GPIO 编号，不是开发板排针顺序**。排线尽量不超过 10cm。

| 驱动板接口 | 信号 | 微雪开发板 |
|---|---|---|
| J2.1 | SCLK | GPIO9 |
| J2.3 | MOSI | GPIO41 |
| J2.5 | SI1 / MISO | GPIO40（输入） |
| J2.7 | CS_M_N | GPIO18 |
| J2.9 | CS_S_N | GPIO17 |
| J2.11 | RES_N | GPIO6 |
| J2.13 | BUSY_N | GPIO7（输入） |
| J2.15 | EPD_PWR_EN | GPIO8 |
| J2.2/4/6/8/10/12/14 | GND | 共地，建议保留信号旁的地线 |
| J2.16 | NC | 留空 |
| J1.1 | BENCH_3V3 | 外部稳压 3.3V 正极 |
| J1.2 | GND | 外部电源负极，与开发板共地 |

开发板 USB 供电；屏幕 J1 单独使用稳压 3.3V 电源，**不能接 USB 5V，不默认从开发板 3V3 脚带屏幕**。电源需满足约 1A 级屏幕峰值并留余量，电源限流应结合首板检查、实测压降设置。FPC 不带电插拔，插入方向按已核对的 pin1→pin1。

本板已移除硬件信号隔离：主控先上电、最后断电。屏幕断电时 SPI 输出、两片选和 RESET 均为低，MISO/BUSY 无内部上拉。代码中的 `board.h` 是默认 GPIO 唯一配置处；未使用 GPIO45 启动绑带脚、GPIO35–37 存储脚和 GPIO38 板载 RGB。

依据：仓库 `hardware/pcb/gdep133c02-driver/docs/interface-power-state.md` 与 `host-interface.csv`；[微雪原理图](https://files.waveshare.com/wiki/ESP32-S3-DEV-KIT-N8R8/ESP32-S3-DEV-KIT-N8R8-schematic.pdf)。

## 2. 构建与烧录

在本目录运行，脚本直接读取本机 EIM 已有激活脚本中的环境，**不下载或安装 IDF**：

```bash
./tools/idf.sh build
ls /dev/cu.*
./tools/flash.sh /dev/cu.usbserial-实际设备名称
```

选择 CH343 USB 转 UART 端口，串口 115200；不自动选择或擦写任何已连接板子。退出 monitor 用 Ctrl+]。烧录前保持 J1 断电；刷写/复位不要发生在屏幕刷新期间。

默认激活脚本：`$HOME/.espressif/tools/activate_idf_v6.1.sh`。其他电脑用 `EVAL_IDF_ACTIVATE=/实际路径/activate_idf_v6.1.sh ./tools/idf.sh build` 指定同版本 EIM 环境。脚本检查准确 IDF 提交，CMake 也检查 6.1.0。

构建输出在 `build/idf6.1/`，固件交付在 `releases/eval-v0.1/`。不需要运行旧厂家压缩包中的 build。烧录固件不等于完成点屏验收。

## 3. 第一次点屏

1. J1 断电，仅插开发板 USB。烧录后进入 `epd>`，执行 `info`。确认 8MB PSRAM、SPI=1000000、GPIO 对应无误；开机不会刷新。
2. 检查板上 EN=0、受控 3.3V 关闭；检查焊接、供电短路、FPC 引脚方向后，再接 J1 稳压 3.3V。
3. 执行 `status`：上电、复位、初始化，分别读取主从 IC 的 F2 三字节原始状态，然后正常关机。读数是诊断，不把未知位解释为电源或显示验收。全 00/FF 通常应先检查接线和供电。
4. 执行 `test colors`：一次六色色条刷新，完成后自动关屏。检查红、黄、蓝、绿是否正确。
5. 执行 `test corners`：逻辑左上红、右上黄、左下蓝、右下绿，黑色边框与中央十字。用于检查旋转、边缘和两个控制器拼接。
6. 执行 `test checkerboard`：六色棋盘；随后 `show photo` 显示嵌入图片。默认嵌入的是本项目生成的测试图，需按下一节替换为个人照片。
7. 正常返回 `result=0`、`screen_power=OFF` 只表示软件流程完成。用仪器确认高压轨残压和放电后，先断屏幕电源，再拔开发板 USB。

命令串行执行，刷新时新命令不会打断当前操作；`off` 也不是实时急停。默认不自动轮播、不无限重试。不要在刷新中复位、烧录、拔线。

`test colors`、`test corners`、`test checkerboard`、`show photo` 每次完整执行上电→初始化→传图→PON→DRF→POF→深睡→接口置低→关闭电源。

遇到 `BUSY timeout` 或 `fault=LATCHED`：停止后续刷新，保留日志，排查 BUSY、供电、SPI 以及硬件；`off` 不清除故障锁存。排查并确认屏幕掉电/残压后才能复位重试。超时处理会尝试停总线、拉低接口并关 EN，这属于**异常切断**，不能称为已完成安全放电。

## 4. 显示自己的照片

照片工具独立于 IDF 环境，使用 Python 3.12/3.13 均可：

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r tools/requirements.txt
.venv/bin/python tools/convert_photo.py /绝对路径/photo.jpg assets/photo.epf
./tools/idf.sh build
./tools/flash.sh /dev/cu.usbserial-实际设备名称
```

然后执行 `show photo`。支持 JPEG/PNG，EXIF 方向校正、透明背景合成白底、等比留白至 1600×1200、六色 Floyd–Steinberg 抖动。调色板为初始近似值，未做实屏色彩校准。EPF1 为应用索引格式，不能直接当作屏幕原生数据。

每个像素索引 0–5 为黑白红黄蓝绿，驱动映射原生色码 0/1/3/2/5/6；每个字节先高半字节再低半字节。960000 字节帧按旋转转换成 1200×1600，左右两半分别发送给主从，每半 480000 字节。

默认逻辑→原生旋转 90°。如果实物上下颠倒，用 `./tools/idf.sh menuconfig` 的 `GDEP133C02 evaluation` 将 rotation 改为 270，重新构建；只支持 90/270，其他值启动时拒绝供屏。不要通过翻转 FPC 插向改变图像方向。

## 5. 软件检查与参数边界

```bash
PATH="$PWD/.venv/bin:$PATH" ./tools/test.sh
./tools/idf.sh build
python3 tools/package_release.py
```

主机 C 测试启用 AddressSanitizer/UndefinedBehaviorSanitizer，使用模拟硬件验证 EPF、CRC、色码、旋转、双控制器拆分、BUSY 置忙/释放以及每个 SPI 传输失败点的处理。Python 测试覆盖照片格式、非法输入、留白和透明背景。测试模拟不代表实物波形合格。

上电等待 10ms、RESET 低/高各20ms、BUSY 置忙超时1s、复位空闲等待5s、PON/POF完成上限30s、DRF上限180s、深睡后等待1ms。这些是可审查的评估起点，必须用实物波形核对，尤其不能跳过 BUSY 置忙来让失败测试“通过”。BUSY 下降沿中断用于记录命令发送期间的短脉冲，轮询阶段让出任务调度。

见 [验证记录](docs/validation.md) 和 [实现说明](docs/architecture.md)。固件不控制 TCN75A 的 I²C：它连接屏幕侧，保留厂家的温度相关初始化，不伪造温度值。尚未做低温/高温显示验证。
