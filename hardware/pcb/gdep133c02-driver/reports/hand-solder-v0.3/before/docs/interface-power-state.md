# 外部主控接口与电源状态

外部控制仅允许3.3V逻辑。J1独立供应稳压3.3V屏幕电源，Pin1为正、Pin2为地；不允许5V或4AA直连。J2 Pin16为开发板HOST_3V3，用于主控侧缓冲器，不供应屏幕刷新。所有地共地。

J2引脚表在`host-interface.csv`；不指定ESP32-S3具体GPIO，开发板接线必须另按实际模组存储、绑带和RTC约束核对，本轮不交付固件。

U6从EPD_3V3供电，向屏幕缓冲SCLK、MOSI、双片选及RESET；U7从HOST_3V3供电，向主控缓冲BUSY和MISO。候选SN74LVC244APWR有Ioff，具体依据为[TI数据手册](https://www.ti.com/lit/ds/symlink/sn74lvc244a.pdf)，不使用未在数据手册承诺Ioff的SN74LVC125A替代。

U6/U7的OE各自上拉本侧供电，通过Q9/Q10在EPD_PWR_EN为高时拉低。EPD_PWR_EN经R29接负载开关ON并由R30=100k下拉，使主控断开或复位时默认关闭。与任何其他默认关闭电路一样，这会中断意外复位中的刷新，不构成安全异常掉电保证。

屏幕侧SCLK/MOSI/RESET由100k下拉，两个片选由100k上拉VDDIO；BUSY继续使用厂家R1=2k上拉VDDIO。SI2/SI3增加100k下拉作为Standard SPI原型未用输入处理的工程选择，不能说成厂家明确给出的标准接法。缓冲器未用输入接地，未用输出不接。

初始操作：EPD_PWR_EN=0，J1及HOST_3V3就绪；配置SCLK/MOSI低、片选高、RESET低；再使能屏幕，等待供电稳定后按面板要求复位并初始化。不得通过保持片选低而直接启动供电。

正常关闭：完整刷新→POF(02,00)→有界等待BUSY置忙/释放→深睡(07,A5)→停串口→至少满足规格书>10µs间隔，原型起点1ms→EPD_PWR_EN=0。顺序来自已接受PCB方案，未进行波形验证。Q9/Q10与U5释放的相对时序及全部高压残压须实测，不能由Ioff静态额定值证明。
