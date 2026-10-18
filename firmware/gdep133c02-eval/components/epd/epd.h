#pragma once
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#define FRAME_BYTES 960000u
#define FRAME_WIDTH 1600u
#define FRAME_HEIGHT 1200u
enum { EPD_OK=0, EPD_IO=-1, EPD_TIMEOUT=-2, EPD_INVALID=-3, EPD_FAULT=-4 };
typedef struct {
    void *ctx;
    int (*power)(void *, bool);
    int (*reset)(void *, bool);
    int (*select)(void *, unsigned); /* bit0 master, bit1 slave; 0 deselect */
    int (*transfer)(void *, const uint8_t *, uint8_t *, size_t);
    int (*busy)(void *); /* 0 busy, 1 idle */
    void (*arm_busy)(void *); /* latch falling edge, including during SPI */
    bool (*saw_busy)(void *);
    uint64_t (*now_ms)(void *);
    void (*delay_ms)(void *, unsigned);
    int (*safe_off)(void *); /* stop SPI, outputs low, then EN low */
    void (*log)(void *, const char *, uint64_t);
} epd_hal_t;
typedef struct { epd_hal_t h; bool powered, fault, initialized; } epd_t;
int epd_start(epd_t *e);
int epd_read_status(epd_t *e, uint8_t data[2][3]);
int epd_show(epd_t *e, const uint8_t *frame, unsigned rotation);
int epd_off(epd_t *e);
void epd_abort(epd_t *e);
int epf_validate(const uint8_t *file, size_t length);
int frame_validate(const uint8_t *frame);
uint32_t frame_crc32(const uint8_t *data, size_t length);
void frame_pattern(uint8_t *frame, unsigned pattern);
void frame_native_row(const uint8_t *frame, unsigned half, unsigned y, unsigned rotation, uint8_t out[300]);
