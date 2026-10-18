# 预编译包烧录

本包来自 ESP-IDF v6.1；只适用于 README 中接线的 N8R8 评估板。
先断开屏幕 J1 电源；选择 CH343 串口，禁止刷新中烧录。

在已激活的本机 IDF v6.1 终端，进入本目录运行：

```bash
python -m esptool --chip esp32s3 --port /dev/cu.usbserial-实际端口 --baud 460800 --before default-reset --after hard-reset write-flash @flash_args
```

偏移以 flash_args 为准：bootloader=0x0、分区表=0x8000、app=0x10000。
串口115200；上电不刷新。完整操作见源工程 README.md；本包 README 是来源快照，其中构建脚本路径指源工程。
