#include "epd.h"
#define TRY(x) do { int r_=(x); if(r_) { epd_abort(e); return r_; } } while(0)
static int command(epd_t *e, unsigned mask, uint8_t cmd, const uint8_t *data, size_t n) {
    epd_hal_t *h=&e->h;
    if(h->select(h->ctx,mask)) return EPD_IO;
    int r=h->transfer(h->ctx,&cmd,0,1);
    if(!r && n) r=h->transfer(h->ctx,data,0,n);
    int end=h->select(h->ctx,0);
    return (r||end)?EPD_IO:0;
}
static int idle(epd_t *e, unsigned timeout) {
    uint64_t start=e->h.now_ms(e->h.ctx);
    while(!e->h.busy(e->h.ctx)) {
        if(e->h.now_ms(e->h.ctx)-start>=timeout)return EPD_TIMEOUT;
        e->h.delay_ms(e->h.ctx,1);
    }
    return 0;
}
static int cycle(epd_t *e, uint8_t cmd, const uint8_t *data, size_t n, unsigned timeout, const char *name) {
    epd_hal_t *h=&e->h;
    if(!h->busy(h->ctx))return EPD_TIMEOUT;
    h->arm_busy(h->ctx);
    uint64_t start=h->now_ms(h->ctx);
    int r=command(e,3,cmd,data,n);
    if(r)return r;
    bool low=false;
    for(;;) {
        low=low||h->saw_busy(h->ctx)||!h->busy(h->ctx);
        uint64_t elapsed=h->now_ms(h->ctx)-start;
        if(low && h->busy(h->ctx)) { h->log(h->ctx,name,elapsed); return 0; }
        if((!low && elapsed>=1000) || elapsed>=timeout) { h->log(h->ctx,"BUSY timeout",elapsed); return EPD_TIMEOUT; }
        h->delay_ms(h->ctx,1);
    }
}
void epd_abort(epd_t *e) {
    e->h.safe_off(e->h.ctx); e->powered=false; e->initialized=false; e->fault=true;
}
int epd_start(epd_t *e) {
    if(e->fault)return EPD_FAULT;
    if(e->powered)return EPD_INVALID;
    TRY(e->h.power(e->h.ctx,true)); e->powered=true;
    e->h.delay_ms(e->h.ctx,10);
    TRY(e->h.select(e->h.ctx,0));
    TRY(e->h.reset(e->h.ctx,false)); e->h.delay_ms(e->h.ctx,20);
    TRY(e->h.reset(e->h.ctx,true)); e->h.delay_ms(e->h.ctx,20);
    TRY(idle(e,5000));
    /* Exact register sequence from archived manufacturer's initEPD(), not generic EPD LUTs. */
    static const struct { uint8_t mask,cmd,n,d[9]; } init[]={
      {1,0x74,9,{0xc0,0x1e,0x1e,0xce,0xce,0xce,0x15,0x15,0x55}},
      {3,0xf0,6,{0x49,0x55,0x13,0x5d,0x05,0x10}}, {3,0x00,2,{0xdf,0x69}},
      {3,0x60,2,{3,3}}, {3,0x86,1,{0x10}}, {3,0xe3,1,{0x22}}, {3,0xe0,1,{1}},
      {3,0x61,4,{4,0xb0,3,0x20}}, {1,0x01,6,{0x0f,0,0x28,0x2c,0x28,0x38}},
      {1,0xb6,1,{7}}, {1,0x06,2,{0xe8,0x28}}, {1,0xb7,1,{1}},
      {1,0x05,2,{0xe8,0x28}}, {1,0xb0,1,{1}}, {1,0xb1,1,{2}}
    };
    for(unsigned i=0;i<sizeof(init)/sizeof(init[0]);i++) TRY(command(e,init[i].mask,init[i].cmd,init[i].d,init[i].n));
    e->initialized=true; return 0;
}
int epd_read_status(epd_t *e, uint8_t data[2][3]) {
    if(!e->initialized)return EPD_INVALID;
    for(unsigned half=0;half<2;half++) {
        uint8_t cmd=0xf2, zeros[3]={0};
        TRY(e->h.select(e->h.ctx,1u<<half));
        TRY(e->h.transfer(e->h.ctx,&cmd,0,1));
        TRY(e->h.transfer(e->h.ctx,zeros,data[half],3));
        TRY(e->h.select(e->h.ctx,0));
    }
    return 0; /* raw diagnostic only: do not assert optical/power health */
}
int epd_off(epd_t *e) {
    if(!e->powered) { if(e->h.safe_off(e->h.ctx))e->fault=true; return e->fault?EPD_FAULT:0; }
    uint8_t zero=0, key=0xa5;
    TRY(cycle(e,0x02,&zero,1,30000,"POF"));
    TRY(command(e,3,0x07,&key,1));
    e->h.delay_ms(e->h.ctx,1);
    int result=e->h.safe_off(e->h.ctx); e->powered=false; e->initialized=false;
    if(result)e->fault=true;
    return result;
}
int epd_show(epd_t *e, const uint8_t *frame, unsigned rotation) {
    if((rotation!=90 && rotation!=270) || frame_validate(frame))return EPD_INVALID;
    TRY(epd_start(e));
    uint8_t row[300], cmd=0x10;
    for(unsigned half=0;half<2;half++) {
        TRY(e->h.select(e->h.ctx,1u<<half));
        TRY(e->h.transfer(e->h.ctx,&cmd,0,1));
        for(unsigned y=0;y<1600;y++) {
            frame_native_row(frame,half,y,rotation,row);
            TRY(e->h.transfer(e->h.ctx,row,0,sizeof(row)));
            e->h.delay_ms(e->h.ctx,1);
        }
        TRY(e->h.select(e->h.ctx,0));
    }
    TRY(cycle(e,0x04,0,0,30000,"PON"));
    e->h.delay_ms(e->h.ctx,30);
    uint8_t one=1;
    TRY(cycle(e,0x12,&one,1,180000,"DRF"));
    return epd_off(e);
}
