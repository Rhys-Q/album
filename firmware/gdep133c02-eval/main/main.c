#include "board.h"
#include "esp_console.h"
#include "esp_heap_caps.h"
#include "esp_psram.h"
#include "esp_system.h"
#include "sdkconfig.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
static epd_t epd;
static uint8_t *frame;
extern const uint8_t photo_start[] asm("_binary_photo_epf_start");
extern const uint8_t photo_end[] asm("_binary_photo_epf_end");
static int result(int r) {
    printf("result=%d; screen_power=%s; fault=%s\n",r,epd.powered?"ON":"OFF",epd.fault?"LATCHED":"none");
    if(epd.fault)puts("Abnormal stop: high-voltage discharge NOT confirmed. Inspect hardware before resetting MCU; no automatic retry.");
    return r?1:0;
}
static int info(int argc,char **argv) {
    (void)argc;(void)argv;
    printf("GDEP133C02 eval / Waveshare N8R8 / IDF %s\nPSRAM=%u; SPI=%d Hz; rotation=%d\n",esp_get_idf_version(),(unsigned)esp_psram_get_size(),CONFIG_EPD_SPI_HZ,CONFIG_EPD_ROTATION);
    printf("GPIO: CLK=%d MOSI=%d MISO=%d CS_M=%d CS_S=%d RESET=%d BUSY=%d EN=%d\n",PIN_SCLK,PIN_MOSI,PIN_MISO,PIN_CS_M,PIN_CS_S,PIN_RESET,PIN_BUSY,PIN_ENABLE);
    return result(0);
}
static int status(int argc,char **argv) {
    (void)argc;(void)argv;
    uint8_t raw[2][3];
    int r=epd_start(&epd);
    if(!r)r=epd_read_status(&epd,raw);
    if(!r)for(int i=0;i<2;i++)printf("IC%d F2 raw: %02x %02x %02x (diagnostic, not hardware acceptance)\n",i,raw[i][0],raw[i][1],raw[i][2]);
    if(!r)r=epd_off(&epd);
    return result(r);
}
static int test(int argc,char **argv) {
    if(argc!=2) { puts("test colors|corners|checkerboard"); return 1; }
    unsigned p;
    if(!strcmp(argv[1],"colors"))p=0;
    else if(!strcmp(argv[1],"corners"))p=1;
    else if(!strcmp(argv[1],"checkerboard"))p=2;
    else return 1;
    frame_pattern(frame,p);
    return result(epd_show(&epd,frame,CONFIG_EPD_ROTATION));
}
static int show(int argc,char **argv) {
    if(argc!=2 || strcmp(argv[1],"photo"))return 1;
    int r=epf_validate(photo_start,(size_t)(photo_end-photo_start));
    if(r)return result(r);
    memcpy(frame,photo_start+32,FRAME_BYTES);
    return result(epd_show(&epd,frame,CONFIG_EPD_ROTATION));
}
static int off(int argc,char **argv) { (void)argc;(void)argv; return result(epd_off(&epd)); }
void app_main(void) {
    if(board_init(&epd.h)) { puts("Board initialization failed; do not connect screen power."); return; }
    if(CONFIG_EPD_ROTATION!=90 && CONFIG_EPD_ROTATION!=270) { puts("Invalid rotation; use 90 or 270."); return; }
    frame=heap_caps_malloc(FRAME_BYTES,MALLOC_CAP_SPIRAM|MALLOC_CAP_8BIT);
    if(!frame) { puts("PSRAM frame allocation failed; screen remains OFF."); return; }
    const esp_console_cmd_t commands[]={
      {.command="info",.help="Board, memory and fault state (no screen power)",.func=info},
      {.command="status",.help="Power/reset/init, read raw status, then shut down",.func=status},
      {.command="test",.help="One refresh: colors|corners|checkerboard",.func=test},
      {.command="show",.help="show photo: one embedded EPF image",.func=show},
      {.command="off",.help="Normal shutdown; does not clear fault latch",.func=off}
    };
    esp_console_repl_t *repl=NULL;
    esp_console_repl_config_t cfg=ESP_CONSOLE_REPL_CONFIG_DEFAULT();
    cfg.prompt="epd>"; cfg.task_stack_size=8192;
    esp_console_dev_uart_config_t uart=ESP_CONSOLE_DEV_UART_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_console_new_repl_uart(&uart,&cfg,&repl));
    for(unsigned i=0;i<sizeof(commands)/sizeof(commands[0]);i++)ESP_ERROR_CHECK(esp_console_cmd_register(&commands[i]));
    puts("Screen OFF. Connect external regulated 3.3V to J1, common GND. No automatic refresh.");
    ESP_ERROR_CHECK(esp_console_start_repl(repl));
}
