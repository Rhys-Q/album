#include "board.h"
#include "driver/gpio.h"
#include "driver/spi_master.h"
#include "esp_heap_caps.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "sdkconfig.h"
#include <string.h>
static spi_device_handle_t device;
static bool bus_active;
static volatile bool busy_seen;
static uint8_t *tx_dma, *rx_dma;
static const int outputs[]={PIN_SCLK,PIN_MOSI,PIN_CS_M,PIN_CS_S,PIN_RESET};
static int low_outputs(void) {
    int r=0;
    for(unsigned i=0;i<sizeof(outputs)/sizeof(outputs[0]);i++) {
        r|=gpio_set_level(outputs[i],0);
        r|=gpio_set_direction(outputs[i],GPIO_MODE_OUTPUT);
        r|=gpio_set_pull_mode(outputs[i],GPIO_FLOATING);
    }
    return r;
}
static int safe_off(void *ctx) {
    (void)ctx;
    int r=0;
    if(device) { r|=spi_bus_remove_device(device); device=NULL; }
    if(bus_active) { r|=spi_bus_free(SPI3_HOST); bus_active=false; }
    /* Always attempt EN low even if releasing SPI or a GPIO fails. */
    r|=low_outputs();
    r|=gpio_set_direction(PIN_MISO,GPIO_MODE_INPUT);
    r|=gpio_set_pull_mode(PIN_MISO,GPIO_FLOATING);
    r|=gpio_set_pull_mode(PIN_BUSY,GPIO_FLOATING);
    r|=gpio_set_level(PIN_ENABLE,0);
    if(r)ESP_LOGE("epd","GPIO/SPI shutdown error: %d; physical state unconfirmed",r);
    return r?EPD_IO:0;
}
static int power(void *ctx, bool on) { (void)ctx; return gpio_set_level(PIN_ENABLE,on)?EPD_IO:0; }
static int reset(void *ctx, bool high) { (void)ctx; return gpio_set_level(PIN_RESET,high)?EPD_IO:0; }
static int select_chip(void *ctx, unsigned mask) {
    (void)ctx;
    if(!bus_active) {
        spi_bus_config_t bus={.mosi_io_num=PIN_MOSI,.miso_io_num=PIN_MISO,.sclk_io_num=PIN_SCLK,
            .quadwp_io_num=-1,.quadhd_io_num=-1,.max_transfer_sz=4096};
        if(spi_bus_initialize(SPI3_HOST,&bus,SPI_DMA_CH_AUTO))return EPD_IO;
        bus_active=true;
        spi_device_interface_config_t dev={.clock_speed_hz=CONFIG_EPD_SPI_HZ,.mode=0,.spics_io_num=-1,.queue_size=1};
        if(spi_bus_add_device(SPI3_HOST,&dev,&device))return EPD_IO;
    }
    return (gpio_set_level(PIN_CS_M,!(mask&1)) | gpio_set_level(PIN_CS_S,!(mask&2)))?EPD_IO:0;
}
static int transfer(void *ctx, const uint8_t *tx, uint8_t *rx, size_t n) {
    (void)ctx;
    if(!device)return EPD_IO;
    while(n) {
        size_t chunk=n>4096?4096:n;
        if(tx)memcpy(tx_dma,tx,chunk); else memset(tx_dma,0,chunk);
        spi_transaction_t t={.length=chunk*8,.rxlength=rx?chunk*8:0,.tx_buffer=tx_dma,.rx_buffer=rx?rx_dma:NULL};
        if(spi_device_transmit(device,&t))return EPD_IO;
        if(rx) { memcpy(rx,rx_dma,chunk); rx+=chunk; }
        if(tx)tx+=chunk;
        n-=chunk;
    }
    return 0;
}
static void busy_isr(void *ctx) { (void)ctx; __atomic_store_n(&busy_seen,true,__ATOMIC_RELAXED); }
static int busy(void *ctx) { (void)ctx; return gpio_get_level(PIN_BUSY); }
static void arm(void *ctx) { (void)ctx; __atomic_store_n(&busy_seen,false,__ATOMIC_RELAXED); }
static bool saw(void *ctx) { (void)ctx; return __atomic_load_n(&busy_seen,__ATOMIC_RELAXED); }
static uint64_t now(void *ctx) { (void)ctx; return esp_timer_get_time()/1000; }
static void delay(void *ctx,unsigned ms) { (void)ctx; vTaskDelay(pdMS_TO_TICKS(ms)?pdMS_TO_TICKS(ms):1); }
static void log_time(void *ctx,const char *name,uint64_t ms) { (void)ctx; ESP_LOGI("epd","%s: %llu ms",name,(unsigned long long)ms); }
int board_init(epd_hal_t *h) {
    if(gpio_set_level(PIN_ENABLE,0) || gpio_set_direction(PIN_ENABLE,GPIO_MODE_OUTPUT) ||
       gpio_set_pull_mode(PIN_ENABLE,GPIO_FLOATING) || low_outputs())return EPD_IO;
    gpio_config_t in={.pin_bit_mask=(1ULL<<PIN_BUSY)|(1ULL<<PIN_MISO),.mode=GPIO_MODE_INPUT,
        .pull_up_en=GPIO_PULLUP_DISABLE,.pull_down_en=GPIO_PULLDOWN_DISABLE,.intr_type=GPIO_INTR_DISABLE};
    if(gpio_config(&in) || gpio_install_isr_service(0) || gpio_set_intr_type(PIN_BUSY,GPIO_INTR_NEGEDGE) ||
       gpio_isr_handler_add(PIN_BUSY,busy_isr,NULL))return EPD_IO;
    tx_dma=heap_caps_malloc(4096,MALLOC_CAP_DMA|MALLOC_CAP_INTERNAL);
    rx_dma=heap_caps_malloc(4096,MALLOC_CAP_DMA|MALLOC_CAP_INTERNAL);
    if(!tx_dma || !rx_dma)return EPD_IO;
    *h=(epd_hal_t){.power=power,.reset=reset,.select=select_chip,.transfer=transfer,.busy=busy,.arm_busy=arm,
        .saw_busy=saw,.now_ms=now,.delay_ms=delay,.safe_off=safe_off,.log=log_time};
    return 0;
}
