#!/usr/bin/env python3
"""Rebuild the editable KiCad schematic and placed board from reviewed pin-level data.
Run with KiCad 10.0.6 bundled Python. Does not fabricate verification results.
"""
from pathlib import Path
import json, uuid, re, shutil, math, csv
ROOT=Path(__file__).resolve().parents[1]
if (ROOT/'reports/check-provenance.json').exists():
    raise SystemExit('Historical initializer disabled: edit the repaired native KiCad project directly.')
KROOT=Path('/Applications/KiCad/KiCad.app/Contents/SharedSupport')
NAME='gdep133c02-driver'
U=lambda: str(uuid.uuid4())
# Stable UUIDs preserve schematic/PCB correspondence across regeneration.
UID=lambda s:str(uuid.uuid5(uuid.NAMESPACE_URL,'album/gdep133c02-driver/'+s))
Q=lambda s:json.dumps(str(s),ensure_ascii=False)
parts=[]
def add(ref,value,pins,fp,xy,group,mpn='',vendor='',url='',names=None,types=None,dnp=False,angle=0):
    parts.append(dict(ref=ref,value=value,pins={str(k):v for k,v in pins.items()},fp=fp,xy=xy,group=group,mpn=mpn or value,vendor=vendor,url=url,names=names or {},types=types or {},dnp=dnp,angle=angle,uuid=UID(ref)))
RFP='Resistor_SMD:R_0603_1608Metric'; CFP='Capacitor_SMD:C_1210_3225Metric'; SOT='Package_TO_SOT_SMD:SOT-23'; SC70='Package_TO_SOT_SMD:SOT-323_SC-70'
def r(n,val,a,b,xy,group='power',fp=RFP,dnp=False):
    code={'0':'0000','2k':'2001','1M':'1004','4.3k':'4301','110k':'1103','2.2':'2R20','100k':'1003','1.5k':'1501','400k':'4003','16k':'1602','4.7k':'4701','10k':'1002','33':'33R0'}.get(val,'')
    add('R'+str(n),val+' ohm',{1:a,2:b},fp,xy,group,mpn=('RC'+('1206' if '1206' in fp else '0603')+('JR-070RL' if val=='0' else 'FR-07'+((val[:-1].replace('.','K')+('K' if '.' not in val else '')) if val.endswith('k') else (val.replace('.','R')+('R' if val.isdigit() else '')))+'L')),vendor='Yageo',dnp=dnp)
def c(n,val,a,b,xy,group='power',fp=CFP,mpn='',angle=0):
    add('C'+str(n),val,{1:a,2:b},fp,xy,group,mpn=mpn or {'10uF/50V':'GRM32ER71H106KA12L','4.7uF/50V':'GRM32ER71H475KA88L','3.3uF/50V':'GRM32DR71H335KA88L','470nF/50V':'GRM21BR71H474KA88L','220nF/50V':'GRM21BR71H224KA01L','1uF/50V':'GRM21BR71H105KA12L','47nF/50V':'GRM188R71H473KA61D','100nF/50V':'GRM188R71H104KA93D','2.2uF/50V':'GRM32ER71H225KA88L','100uF/6.3V':'GRM32ER60J107ME20L'}.get(val,''),vendor='Murata',angle=angle)
# External power (no regulator, battery, USB, or MCU on this prototype).
add('J1','3V3 BENCH ONLY',{1:'BENCH_3V3',2:'GND'},'Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical',(13,69),'entry',mpn='TSW-102-07-G-S',vendor='Samtec')
r(26,'0','BENCH_3V3','EPD_VDD',(20,69),'entry',fp='Resistor_SMD:R_1206_3216Metric')
c(28,'2.2uF/50V','EPD_VDD','GND',(23,65),'entry')
r(27,'0','EPD_VDD','SW_IN',(27,69),'entry',fp='Resistor_SMD:R_1206_3216Metric')
add('U5','TPS22913BYZVT',{'A1':'SW_OUT','A2':'SW_IN','B1':'GND','B2':'SW_ON'},'Package_CSP:WLCSP-4_0.89x0.89mm_Layout2x2_P0.5mm',(32,69),'entry',vendor='Texas Instruments',url='https://www.ti.com/lit/ds/symlink/tps22913.pdf',names={'A1':'VOUT','A2':'VIN','B1':'GND','B2':'ON'},types={'A1':'power_out','A2':'power_in','B1':'power_in','B2':'input'})
r(28,'0','SW_OUT','VIN',(37,69),'entry',fp='Resistor_SMD:R_1206_3216Metric')
r(29,'0','EPD_PWR_EN','SW_ON',(28,73),'entry');r(30,'100k','SW_ON','GND',(32,73),'entry')
c(29,'4.7uF/50V','VIN','GND',(37,64),'entry');c(30,'4.7uF/50V','VIN','GND',(43,64),'entry')
add('L4','BLM18PG221SH1D',{1:'VIN',2:'EPD_3V3'},'Inductor_SMD:L_0603_1608Metric',(48,69),'entry',vendor='Murata')
add('L5','CBG160808U000T',{1:'VIN',2:'AVDD_PRE'},'Inductor_SMD:L_0603_1608Metric',(46,61),'entry',vendor='FH')
r(31,'0','AVDD_PRE','AVDD_CAP',(51,61),'entry',fp='Resistor_SMD:R_1206_3216Metric');r(32,'0','AVDD_CAP','AVDD',(67,61),'entry',fp='Resistor_SMD:R_1206_3216Metric')
c(31,'100uF/6.3V','AVDD_CAP','GND',(56,62),'entry');c(32,'100uF/6.3V','AVDD_CAP','GND',(62,62),'entry')
r(33,'0','EPD_3V3','VDD',(53,69),'entry');r(34,'0','EPD_3V3','VDDIO',(58,69),'entry');c(33,'100nF/50V','EPD_3V3','GND',(54,73),'entry',fp='Capacitor_SMD:C_0603_1608Metric')
# Three inductive converters: preserve manufacturer topology and pin mapping.
for n,xy,nets in [(1,(24,35),('AVDD','LX')),(2,(44,35),('SW_N','GND')),(3,(64,35),('SW_VCOM','GND'))]:
    add('L'+str(n),'15uH',{1:nets[0],2:nets[1]},'Inductor_SMD:L_Coilcraft_MSS1246T-XXX',xy,'converters',mpn='MSS1246T-153MLD',vendor='Coilcraft',url='https://www.coilcraft.com/en-us/products/power/shielded-inductors/ferrite-drum/mss-mos/mss1246/')
add('Q1','DMN3065LW-7',{1:'GDRP',2:'SENSE_P',3:'LX'},SC70,(24,45),'converters',vendor='Diodes',url='https://www.diodes.com/part/view/DMN3065LW',names={'1':'G','2':'S','3':'D'})
add('Q8','DMP3068L-7',{1:'GATE_N',2:'SENSE_N',3:'SW_N'},SOT,(44,45),'converters',vendor='Diodes',url='https://www.diodes.com/datasheet/download/DMP3068L.pdf',names={'1':'G','2':'S','3':'D'})
add('Q7','PJA3433_R1_00001',{1:'GATE_VCOM',2:'SENSE_VCOM',3:'SW_VCOM'},SOT,(64,45),'converters',vendor='Panjit',url='https://www.panjit.com.cn/upload/datasheet/PJA3433.pdf',names={'1':'G','2':'S','3':'D'})
for n,a,b,xy in [(1,'SENSE_P','GND',(24,50)),(2,'AVDD','SENSE_N',(44,50)),(3,'AVDD','SENSE_VCOM',(64,50))]:
    add('U'+str(n),'0.2 ohm',{1:a,2:b},'Resistor_SMD:R_1206_3216Metric',xy,'converters',mpn='WSL1206R2000FEA',vendor='Vishay')
r(2,'1M','GDRP','GND',(19,48),'converters');r(3,'1M','AVDD','GATE_N',(39,48),'converters');r(13,'1M','AVDD','GATE_VCOM',(59,48),'converters')
for n,a,b,xy in [(4,'RESEN','SENSE_N',(39,52)),(5,'GDRN','GATE_N',(39,44)),(6,'VDDN_RAW','VDDN',(50,45)),(14,'RESEC','SENSE_VCOM',(59,52)),(15,'GDRC','GATE_VCOM',(59,44)),(16,'VBB_3P5V','VNCP_3P5V',(70,45))]:r(n,'0',a,b,xy,'converters')
for ref,val,pins,xy,fp in [('D1','MBR230S1F-7',{1:'VDDP',2:'LX'},(29,44),'Diode_SMD:D_SOD-123F'),('D2','MBR230S1F-7',{1:'SW_N',2:'VDDN_RAW'},(49,40),'Diode_SMD:D_SOD-123F'),('D4','B0530W-7-F',{1:'SW_VCOM',2:'VBB_3P5V'},(69,40),'Diode_SMD:D_SOD-123')]:
    add(ref,val,pins,fp,xy,'converters',vendor='Diodes',names={'1':'K','2':'A'})
for n,val,a,xy in [(12,'4.7uF/50V','AVDD',(17,36)),(13,'10uF/50V','VDDP',(30,49)),(14,'4.7uF/50V','AVDD',(37,36)),(15,'10uF/50V','VDDN',(51,49)),(19,'4.7uF/50V','AVDD',(57,36)),(20,'10uF/50V','VBB_3P5V',(71,49))]:c(n,val,a,'GND',xy,'converters')
# Positive gate-voltage pump; BAT54S pin1=A1, pin2=K2, pin3=K1/A2.
add('Q3','MMBT3906-7-F',{1:'BASE_P',2:'VDDP',3:'PUMP_P_LOW'},SOT,(20,57),'pumps',vendor='Diodes',names={'1':'B','2':'E','3':'C'})
add('Q4','DMN3065LW-7',{1:'DRVP',2:'SOURCE_VGP',3:'BASE_P'},SC70,(15,57),'pumps',vendor='Diodes',names={'1':'G','2':'S','3':'D'})
r(11,'100k','VDDP','BASE_P',(15,61),'pumps');r(12,'1.5k','SOURCE_VGP','GND',(11,61),'pumps')
add('D3','BAT54S-7-F',{1:'PUMP_P_LOW',2:'VGH_RAW',3:'PUMP_P_MID'},SOT,(24,56),'pumps',vendor='Diodes',names={'1':'A1','2':'K2','3':'K1_A2'})
c(16,'4.7uF/50V','VGH_RAW','GND',(29,55),'pumps');c(17,'470nF/50V','PUMP_P_MID','PUMP_P_AC',(29,59),'pumps',fp='Capacitor_SMD:C_0805_2012Metric');c(18,'220nF/50V','PUMP_P_LOW','GND',(20,61),'pumps',fp='Capacitor_SMD:C_0805_2012Metric')
r(7,'4.3k','GND','FBP',(34,55),'pumps');r(8,'110k','FBP','VGH_RAW',(34,58),'pumps');r(9,'0','VGH_RAW','VGH',(37,55),'pumps');r(10,'2.2','PUMP_P_AC','LX',(34,61),'pumps')
# Negative gate-voltage doubler.
add('Q6','MMBT3904-7-F',{1:'DRVN',2:'GND',3:'PUMP_N_LOW'},SOT,(81,37),'pumps',vendor='Diodes',names={'1':'B','2':'E','3':'C'})
add('D5','BAT54S-7-F',{1:'VGL',2:'PUMP_N_MID',3:'PUMP_N_UP'},SOT,(86,29),'pumps',vendor='Diodes',names={'1':'A1','2':'K2','3':'K1_A2'})
add('D6','BAT54S-7-F',{1:'PUMP_N_MID',2:'PUMP_N_LOW',3:'PUMP_N_DOWN'},SOT,(86,37),'pumps',vendor='Diodes',names={'1':'A1','2':'K2','3':'K1_A2'})
c(21,'4.7uF/50V','VGL','GND',(92,25),'pumps');c(22,'1uF/50V','PUMP_N_MID','GND',(81,29),'pumps',fp='Capacitor_SMD:C_0805_2012Metric');c(23,'470nF/50V','PUMP_N_UP','PUMP_N_AC',(92,29),'pumps',fp='Capacitor_SMD:C_0805_2012Metric');c(24,'470nF/50V','PUMP_N_DOWN','PUMP_N_AC',(92,37),'pumps',fp='Capacitor_SMD:C_0805_2012Metric');c(25,'1uF/50V','REG_VGN','GND',(87,45),'pumps',fp='Capacitor_SMD:C_0805_2012Metric');c(26,'47nF/50V','PUMP_N_LOW','GND',(81,41),'pumps',fp='Capacitor_SMD:C_0603_1608Metric')
r(17,'400k','VGL','FBN',(91,41),'pumps');r(18,'16k','FBN','REG_VGN',(91,45),'pumps');r(19,'2.2','PUMP_N_AC','LX',(92,33),'pumps')
# Panel-side temperature sensor.
add('U4','TCN75AVOA713',{1:'TSDA',2:'TSCL',3:'ALERT_N',4:'GND',5:'GND',6:'GND',7:'GND',8:'EPD_3V3'},'Package_SO:SOIC-8_3.9x4.9mm_P1.27mm',(12,27),'panel',vendor='Microchip',url='https://ww1.microchip.com/downloads/en/DeviceDoc/21935c.pdf',names={'1':'SDA','2':'SCL','3':'ALERT','4':'GND','5':'A2','6':'A1','7':'A0','8':'VDD'},types={'1':'bidirectional','2':'input','3':'open_collector','4':'power_in','5':'input','6':'input','7':'input','8':'power_in'})
r(20,'4.7k','TSCL','EPD_3V3',(9,20),'panel');r(21,'4.7k','TSDA','EPD_3V3',(14,20),'panel');r(22,'10k','ALERT_N','EPD_3V3',(9,33),'panel');r(23,'0','ALERT_N','GND',(14,33),'panel',dnp=True);c(27,'100nF/50V','EPD_3V3','GND',(9,24),'panel',fp='Capacitor_SMD:C_0603_1608Metric')
# Mode straps and unused serial inputs: weak pull-downs, not direct shorts.
r(24,'0','BS0','VDD',(30,11),'panel');r(25,'0','BS1','VDD',(35,11),'panel');r(1,'2k','BUSY_N','VDDIO',(72,12),'panel');r(35,'100k','SI2','GND',(40,11),'panel');r(36,'100k','SI3','GND',(45,11),'panel')
# Source buffers: 3*10uF + 3.3uF =33.3uF nominal per reference 33uF node.
# This deliberately avoids choosing an unverifiable single high-voltage 33uF MLCC.
for i,net in enumerate(['VSPH','VSPL','VSPL2','VSNH','VSNL','VSNL2'],1):
    x=25+(i-1)*9
    c(i,'10uF/50V',net,'GND',(x-2.5,17),'panel',angle=90)
    for j,(val,dx,y) in enumerate([('10uF/50V',2.5,17),('10uF/50V',-2.5,23),('3.3uF/50V',2.5,23)]):c(100+i*3+j,val,net,'GND',(x+dx,y),'panel',angle=90)
for n,val,net,xy,fp in [(7,'10uF/50V','VCC',(76,18),CFP),(8,'4.7uF/50V','TFT_VCOM',(82,18),CFP),(9,'470nF/50V','FPL_VCOM',(87,18),'Capacitor_SMD:C_0805_2012Metric'),(10,'470nF/50V','VCOMBD_M',(91,12),'Capacitor_SMD:C_0805_2012Metric'),(11,'470nF/50V','VCOMBD_S',(91,18),'Capacitor_SMD:C_0805_2012Metric')]:c(n,val,net,'GND',xy,'panel',fp)
# Interface isolation: one 8-bit Ioff buffer toward panel, one toward host.
# OE pull-ups ensure disabled default; NMOS pulls OE low only when EPD_PWR_EN is asserted.
fpbuf='Package_SO:TSSOP-20_4.4x6.5mm_P0.65mm'
ins=['HOST_SCLK','HOST_MOSI','HOST_CS_M_N','HOST_CS_S_N','HOST_RES_N','GND','GND','GND'];outs=['BUF_SCLK','BUF_MOSI','BUF_CS_M_N','BUF_CS_S_N','BUF_RES_N',None,None,None]
inpins=[2,4,6,8,11,13,15,17];outpins=[18,16,14,12,9,7,5,3]
for ref,domain,ip,op,oe,xy in [('U6','EPD_3V3',ins,outs,'OE_PANEL_N',(56,72)),('U7','HOST_3V3',['BUSY_N','SI1','GND','GND','GND','GND','GND','GND'],['HOST_BUSY_N','HOST_MISO',None,None,None,None,None,None],'OE_HOST_N',(76,69))]:
    pins={1:oe,19:oe,10:'GND',20:domain};names={'1':'1OE_N','19':'2OE_N','10':'GND','20':'VCC'};types={'1':'input','19':'input','10':'power_in','20':'power_in'}
    for j,(a,b) in enumerate(zip(inpins,outpins)):
        pins[a]=ip[j];pins[b]=op[j];names[str(a)]='A'+str(j+1);names[str(b)]='Y'+str(j+1);types[str(a)]='input';types[str(b)]='tri_state'
    add(ref,'SN74LVC244APWR',pins,fpbuf,xy,'interface',vendor='Texas Instruments',url='https://www.ti.com/lit/ds/symlink/sn74lvc244a.pdf',names=names,types=types)
for ref,oe,xy in [('Q9','OE_PANEL_N',(68,73)),('Q10','OE_HOST_N',(84,72))]:add(ref,'2N7002-7-F',{1:'EPD_PWR_EN',2:'GND',3:oe},SOT,xy,'interface',vendor='Diodes',names={'1':'G','2':'S','3':'D'})
r(37,'10k','OE_PANEL_N','EPD_3V3',(65,69),'interface');r(38,'10k','OE_HOST_N','HOST_3V3',(84,68),'interface')
for j,(a,b) in enumerate(zip(outs[:5],['SCLK','SI0','CS_M_N','CS_S_N','RES_N']),39):r(j,'33',a,b,(49+(j-39)*5,77),'interface')
# Panel-side valid inactive levels when buffer outputs are disabled.
for j,(a,b) in enumerate([('SCLK','GND'),('SI0','GND'),('CS_M_N','VDDIO'),('CS_S_N','VDDIO'),('RES_N','GND')],44):r(j,'100k',a,b,(49+(j-44)*5,64),'interface')
c(34,'100nF/50V','EPD_3V3','GND',(52,72),'interface',fp='Capacitor_SMD:C_0603_1608Metric');c(35,'100nF/50V','HOST_3V3','GND',(80,64),'interface',fp='Capacitor_SMD:C_0603_1608Metric')
conn=['HOST_SCLK','GND','HOST_MOSI','GND','HOST_MISO','GND','HOST_CS_M_N','GND','HOST_CS_S_N','GND','HOST_RES_N','GND','HOST_BUSY_N','GND','EPD_PWR_EN','HOST_3V3']
add('J2','HOST 3V3 LOGIC',{i+1:n for i,n in enumerate(conn)},'Connector_PinHeader_2.54mm:PinHeader_2x08_P2.54mm_Vertical',(88,55),'interface',mpn='TSW-108-07-G-D',vendor='Samtec')
# Panel FPC symbol retains actual pin names; unused outputs explicitly NC.
orig=list(csv.DictReader((ROOT.parents[1]/'reference/gdep133c02/pin-map.csv').open()))
nets=['VCOMBD_M','RESEC','GDRC','RESEN','GDRN','RESEP','GDRP','GND','AVDD','VDD',None,'VCC','VDDP','VDDP',None,'VDDN','VDDN','VCC','VDDIO','TSCL','TSDA','BS0','BS1','RES_N','BUSY_N','GND','CS_M_N','SCLK','SI0','SI1','SI2','SI3','DRVP','FBP','GND','VCOMBD_S','DRVN','FBN','REG_VGN',None,'VNCP_3P5V','VSPH','VSPL','VSPL2','VSPH','VSPL','VSPL2','VSNH','VSNL','VSNL2','VSNL2','VSNL','VSNH','FPL_VCOM','TFT_VCOM','VBB_3P5V',None,'CS_S_N','VGH','VGL']
add('FPC1','FPC-05FB-60PH20',{i+1:n for i,n in enumerate(nets)},'Driver:FPC_05FB_60PH20_UNVERIFIED',(50,5),'panel',vendor='Xunpu',url='https://atta.szlcsc.com/upload/public/pdf/source/20210922/C2856839_B700DB1A2B95976B214AB1FEFC031E2B.pdf',names={str(i+1):a['datasheet_signal'] for i,a in enumerate(orig)},types={str(i+1):{'I':'input','O':'output','I/O':'bidirectional','P':'passive','NC':'no_connect'}.get(a['type'],'passive') for i,a in enumerate(orig)})
# Exposed current-sense pin RESEP is a panel input, coupled to Q1 source.
# Reference has no discrete zero-ohm between RESEP and Q1 source.
for p in parts:
    if p['ref']=='Q1':p['pins']['2']='RESEP'
    if p['ref']=='U1':p['pins']['1']='RESEP'
# Test pads along board sides; voltage names, no guessed source-rail setpoints.
for i,(net,xy) in enumerate([('BENCH_3V3',(7,69)),('VIN',(7,63)),('AVDD',(7,57)),('EPD_3V3',(7,51)),('VDDP',(7,45)),('VDDN',(7,39)),('VGH',(96,54)),('VGL',(96,48)),('VBB_3P5V',(96,42)),('VNCP_3P5V',(96,36)),('TFT_VCOM',(96,30)),('VCC',(96,24)),('BUSY_N',(75,8)),('EPD_PWR_EN',(80,8)),('RES_N',(85,8))],1):
    add('TP'+str(i),net,{1:net},'TestPoint:TestPoint_Pad_D1.5mm',xy,'test',mpn='PCB test pad',vendor='PCB',dnp=True)
for i,xy in enumerate([(7,73),(7,60),(7,48),(7,36),(96,57),(96,45),(96,33),(96,21),(80,12)],16):add('TP'+str(i),'GND',{1:'GND'},'TestPoint:TestPoint_Pad_D1.5mm',xy,'test',mpn='PCB test pad',vendor='PCB',dnp=True)
(ROOT/'design-data.json').write_text(json.dumps({'name':NAME,'revision':'0.1-draft','parts':parts,'board_mm':[100,80],'fpc_footprint_verified':False},ensure_ascii=False,indent=2)+'\n')
print('Wrote',len(parts),'parts to design-data.json')

# Placement corrections reserve inductor bodies and interface courtyards.
positions={'U6':(73,64),'U7':(82,64),'Q9':(68,68),'Q10':(88,67),'R37':(68,72),'R38':(88,71),'C34':(79,59),'C35':(88,60),'C7':(78,16),'C8':(78,22),'C9':(85,18),'C12':(14,40),'C14':(34,40),'C19':(54,40),'J2':(72,76),'TP16':(11,73)}
for p in parts:
 if p['ref'] in positions:p['xy']=positions[p['ref']]
 if p['ref'] in ['R44','R45','R46','R47','R48']:p['xy']=(p['xy'][0],58)
 if p['ref']=='J2':p['angle']=90
 if p['ref'].startswith('L') and p['ref'] in ['L1','L2','L3']:p['mpn']='MSS1246-153MLC'
(ROOT/'design-data.json').write_text(json.dumps({'name':NAME,'revision':'0.1-draft','parts':parts,'board_mm':[100,80],'fpc_footprint_verified':False},ensure_ascii=False,indent=2)+'\n')
