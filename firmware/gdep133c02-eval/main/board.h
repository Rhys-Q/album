#pragma once
#include "epd.h"
enum { PIN_SCLK=9, PIN_MOSI=41, PIN_MISO=40, PIN_CS_M=18, PIN_CS_S=17, PIN_RESET=6, PIN_BUSY=7, PIN_ENABLE=8 };
int board_init(epd_hal_t *hal);
