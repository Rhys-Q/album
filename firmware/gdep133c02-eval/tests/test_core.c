#include "epd.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef struct {
    uint64_t time, armed_at;
    unsigned mask, calls, fail_at, command_count, dtm_bytes[2], sleeping;
    unsigned commands[64];
    bool power, armed, sent, never_low, stuck_low, immediate;
    uint8_t current;
    bool expecting_command;
} mock_t;
static int power(void *v,bool b) { ((mock_t*)v)->power=b; return 0; }
static int reset(void *v,bool b) { (void)v;(void)b; return 0; }
static int select_chip(void *v,unsigned mask) { mock_t *m=v; m->mask=mask; m->expecting_command=true; return 0; }
static int tx(void *v,const uint8_t *p,uint8_t *rx,size_t n) {
    mock_t *m=v;
    if(++m->calls==m->fail_at)return EPD_IO;
    if(m->expecting_command) {
        assert(n==1); m->current=*p; m->expecting_command=false;
        assert(m->command_count<64); m->commands[m->command_count++]=*p;
        if(m->armed)m->sent=true;
    } else if(m->current==0x10) {
        assert(m->mask==1 || m->mask==2); m->dtm_bytes[m->mask==2]+=n;
    } else if(m->current==7) { assert(n==1 && p[0]==0xa5); m->sleeping++; }
    if(rx)memset(rx,1,n);
    return 0;
}
static int busy(void *v) {
    mock_t *m=v;
    if(!m->armed || !m->sent || m->never_low || m->immediate)return 1;
    return m->time-m->armed_at<2?1: (m->stuck_low || m->time-m->armed_at<5)?0:1;
}
static void arm(void *v) { mock_t*m=v; m->armed=true; m->sent=false; m->armed_at=m->time; }
static bool saw(void*v) { mock_t*m=v; return m->immediate && m->sent; }
static uint64_t now(void*v) { return ((mock_t*)v)->time; }
static void delay(void*v,unsigned ms) { ((mock_t*)v)->time+=ms; }
static int off(void*v) { ((mock_t*)v)->power=false; return 0; }
static void log_time(void*v,const char*s,uint64_t ms) { (void)v;(void)s;(void)ms; }
static epd_t device(mock_t*m) {
    epd_t e={.h={m,power,reset,select_chip,tx,busy,arm,saw,now,delay,off,log_time}}; return e;
}
static void put(uint8_t*p,unsigned x,unsigned y,unsigned c) {
    size_t i=(y*1600+x)/2; if(x&1)p[i]=(p[i]&0xf0)|c; else p[i]=(p[i]&15)|(c<<4);
}
int main(int argc,char**argv) {
    assert(argc==2);
    FILE*f=fopen(argv[1],"rb"); assert(f);
    uint8_t *file=malloc(FRAME_BYTES+33); assert(file);
    assert(fread(file,1,FRAME_BYTES+33,f)==FRAME_BYTES+32); fclose(f);
    assert(epf_validate(file,FRAME_BYTES+32)==0);
    assert(epf_validate(file,FRAME_BYTES+31)==EPD_INVALID);
    assert(epf_validate(file,FRAME_BYTES+33)==EPD_INVALID);
    file[100]^=1; assert(epf_validate(file,FRAME_BYTES+32)==EPD_INVALID); file[100]^=1;
    file[24]=1; assert(epf_validate(file,FRAME_BYTES+32)==EPD_INVALID); file[24]=0;
    file[12]=2; assert(epf_validate(file,FRAME_BYTES+32)==EPD_INVALID); file[12]=1;
    assert(frame_crc32((const uint8_t*)"123456789",9)==0xcbf43926);
    uint8_t *p=file+32; memset(p,0x11,FRAME_BYTES);
    uint8_t row[300];
    static const uint8_t codes[]={0,1,3,2,5,6};
    for(unsigned c=0;c<6;c++) {
        memset(p,c*17,FRAME_BYTES);
        frame_native_row(p,0,0,90,row);
        for(unsigned i=0;i<300;i++)assert(row[i]==codes[c]*17);
    }
    memset(p,0x11,FRAME_BYTES);
    put(p,0,1199,2); put(p,1599,0,5); put(p,0,599,4);
    frame_native_row(p,0,0,90,row); assert(row[0]==0x31);
    frame_native_row(p,1,0,90,row); assert(row[0]==0x51);
    frame_native_row(p,0,0,270,row); assert(row[0]==0x61);
    frame_native_row(p,1,1599,270,row); assert(row[299]==0x13);
    p[0]=0x61; assert(frame_validate(p)==EPD_INVALID); p[0]=0x11;
    mock_t m={0}; epd_t e=device(&m);
    assert(epd_show(&e,p,0)==EPD_INVALID && !m.power && m.calls==0);
    assert(epd_show(&e,p,90)==0 && !m.power && !e.fault && m.sleeping==1);
    assert(m.dtm_bytes[0]==480000 && m.dtm_bytes[1]==480000);
    assert(m.commands[m.command_count-4]==4 && m.commands[m.command_count-3]==0x12 &&
           m.commands[m.command_count-2]==2 && m.commands[m.command_count-1]==7);
    unsigned success_calls=m.calls;
    /* Every SPI failure point: initialization, image, PON/DRF/POF and deep sleep. */
    for(unsigned fail=1;fail<=success_calls;fail++) {
        m=(mock_t){.fail_at=fail}; e=device(&m);
        assert(epd_show(&e,p,90)==EPD_IO && !m.power && e.fault);
        assert(epd_start(&e)==EPD_FAULT);
    }
    m=(mock_t){.never_low=true}; e=device(&m);
    assert(epd_show(&e,p,90)==EPD_TIMEOUT && e.fault && !m.power && !m.sleeping);
    m=(mock_t){.stuck_low=true}; e=device(&m);
    assert(epd_show(&e,p,90)==EPD_TIMEOUT && e.fault && !m.power);
    m=(mock_t){.immediate=true}; e=device(&m);
    assert(epd_show(&e,p,270)==0 && !m.power);
    m=(mock_t){0}; e=device(&m); assert(epd_start(&e)==0);
    uint8_t raw[2][3]; assert(epd_read_status(&e,raw)==0 && raw[0][0]==1 && raw[1][0]==1);
    assert(epd_off(&e)==0 && epd_off(&e)==0);
    free(file); puts("PASS: EPF, CRC, palette, rotation, split, BUSY and all SPI failure points");
}
