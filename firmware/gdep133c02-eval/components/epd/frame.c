#include "epd.h"
#include <string.h>
static uint16_t u16(const uint8_t *p) { return p[0] | (uint16_t)p[1]<<8; }
static uint32_t u32(const uint8_t *p) { return u16(p) | (uint32_t)u16(p+2)<<16; }
uint32_t frame_crc32(const uint8_t *p, size_t n) {
    uint32_t c=~0u;
    while(n--) { c^=*p++; for(int i=0;i<8;i++) c=(c>>1)^((0u-(c&1))&0xedb88320u); }
    return ~c;
}
int frame_validate(const uint8_t *p) {
    if(!p) return EPD_INVALID;
    for(size_t i=0;i<FRAME_BYTES;i++) if((p[i]>>4)>5 || (p[i]&15)>5) return EPD_INVALID;
    return 0;
}
int epf_validate(const uint8_t *p, size_t n) {
    if(!p || n!=FRAME_BYTES+32 || memcmp(p,"EPF1",4) || u16(p+4)!=1 || u16(p+6)!=32 ||
       u16(p+8)!=1600 || u16(p+10)!=1200 || p[12]!=1 || p[13]!=0 || u16(p+14)!=0 || u32(p+16)!=FRAME_BYTES) return EPD_INVALID;
    for(int i=24;i<32;i++) if(p[i]) return EPD_INVALID;
    if(u32(p+20)!=frame_crc32(p+32,FRAME_BYTES)) return EPD_INVALID;
    return frame_validate(p+32);
}
static unsigned pixel(const uint8_t *p, unsigned x, unsigned y) {
    unsigned v=p[(y*1600+x)/2]; return (x&1)?v&15:v>>4;
}
void frame_native_row(const uint8_t *p, unsigned half, unsigned y, unsigned rotation, uint8_t out[300]) {
    static const uint8_t native[]={0,1,3,2,5,6};
    for(unsigned i=0;i<300;i++) {
        unsigned v=0;
        for(unsigned k=0;k<2;k++) {
            unsigned nx=half*600+i*2+k;
            /* Logical 1600x1200 -> native 1200x1600, clockwise or counterclockwise. */
            unsigned x=rotation==90?y:1599-y;
            unsigned ly=rotation==90?1199-nx:nx;
            v=(v<<4)|native[pixel(p,x,ly)];
        }
        out[i]=(uint8_t)v;
    }
}
void frame_pattern(uint8_t *p, unsigned pattern) {
    for(unsigned y=0;y<1200;y++) for(unsigned x=0;x<1600;x+=2) {
        unsigned c=pattern==0?x*6/1600:((x/100+y/100)%6);
        if(pattern==1) {
            c=1;
            if(y<200 && x<200)c=2; /* red TL */
            if(y<200 && x>=1400)c=3; /* yellow TR */
            if(y>=1000 && x<200)c=4; /* blue BL */
            if(y>=1000 && x>=1400)c=5; /* green BR */
            if(x==798 || y==600 || x==0 || x==1598 || y==0 || y==1199)c=0;
        }
        p[(y*1600+x)/2]=(uint8_t)(c*17);
    }
}
