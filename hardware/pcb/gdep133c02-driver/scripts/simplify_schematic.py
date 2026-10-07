#!/usr/bin/env python3
"""Apply approved v0.3 simplification from a preserved native baseline once."""
from pathlib import Path
from copy import deepcopy
import json,uuid,math
from schematic_sexp import Q,parse,dump,kids,one
R=Path(__file__).resolve().parents[1];B=R/'reports/hand-solder-v0.3/before'
# Migration helper only. The final native files are authoritative.
import sys
if '--rebuild-from-baseline' not in sys.argv:
 raise SystemExit('Migration already applied; rebuilding from the archived baseline discards subsequent layout/edits. Use --rebuild-from-baseline only in a disposable project copy.')
def obj(s):return parse(s)
def uid(s):return Q(str(uuid.uuid5(uuid.NAMESPACE_URL,'album/hand-solder-v03/'+s)))
def props(s):return {p[1]:p[2] for p in kids(s,'property')}
def setprop(s,k,v):next(p for p in kids(s,'property') if p[1]==k)[2]=Q(v)
def wire(a,b):
 assert a[0]==b[0] or a[1]==b[1],(a,b)
 return obj(f'(wire (pts (xy {a[0]} {a[1]})(xy {b[0]} {b[1]}))(stroke (width 0)(type default))(uuid {dump(uid(str(a)+str(b)))}))')
def label(n,pt,angle=0):return obj(f'(global_label {json.dumps(n)}(shape bidirectional)(at {pt[0]} {pt[1]} {angle})(effects (font (size 1 1))(justify left))(uuid {dump(uid(n+str(pt)))})(property "Intersheetrefs" "${{INTERSHEET_REFS}}"(at {pt[0]} {pt[1]} {angle})(effects (font (size 1 1))(hide yes))))')
def nc(pt):return obj(f'(no_connect(at {pt[0]} {pt[1]})(uuid {dump(uid("nc"+str(pt)))}))')
def text(s,x,y,size=1.5):return obj(f'(text {json.dumps(s)}(at {x} {y} 0)(effects(font(size {size} {size}))(justify left))(uuid {dump(uid(s))}))')
alias={
'EPD_VDD':'BENCH_3V3','SW_IN':'BENCH_3V3','SW_OUT':'VIN','SW_ON':'EPD_PWR_EN',
'AVDD_PRE':'AVDD','AVDD_CAP':'AVDD','VDD':'EPD_3V3','VDDIO':'EPD_3V3','BS0':'EPD_3V3','BS1':'EPD_3V3',
'SENSE_N':'RESEN','GATE_N':'GDRN','VDDN_RAW':'VDDN','SENSE_VCOM':'RESEC','GATE_VCOM':'GDRC',
'VNCP_3P5V':'VBB_3P5V','VGH_RAW':'VGH','BUF_SCLK':'HOST_SCLK','BUF_MOSI':'HOST_MOSI',
'BUF_CS_M_N':'HOST_CS_M_N','BUF_CS_S_N':'HOST_CS_S_N','BUF_RES_N':'HOST_RES_N',
'HOST_BUSY_N':'BUSY_N','HOST_MISO':'SI1'}
removed=set('R4 R5 R6 R9 R14 R15 R16 R24 R25 R26 R27 R28 R29 R31 R32 R33 R34 U6 U7 Q9 Q10 R37 R38 C34 C35 R22 R23'.split())
data=json.loads((B/'design-data.json').read_text());oldparts={p['ref']:p for p in data['parts']}
newdefs={};pages={}
def pinpos(s,d):
 x,y,ang=map(float,one(s,'at')[1:]);rad=math.radians(ang);out={}
 for c in kids(d,'symbol'):
  for p in kids(c,'pin'):
   px,py=map(float,one(p,'at')[1:3]);out[str(one(p,'number')[1])]=(round(x+px*math.cos(rad)-py*math.sin(rad),6),round(y-px*math.sin(rad)-py*math.cos(rad),6))
 return out
for name in ['power','panel','interface']:
 a=parse((B/(name+'.kicad_sch')).read_text());defs={s[1]:s for s in kids(one(a,'lib_symbols'),'symbol')};parts={props(s)['Reference']:s for s in kids(a,'symbol')};pages[name]=(a,defs,parts)
 # Bridge every removed 0-ohm link exactly at its previous physical symbol pins.
 for ref in removed&set(parts):
  if oldparts[ref]['value']=='0 ohm' and not oldparts[ref]['dnp']:
   pp=pinpos(parts[ref],defs[one(parts[ref],'lib_id')[1]]);a.append(wire(pp['1'],pp['2']))
 for s in list(kids(a,'symbol')):
  if props(s)['Reference'] in removed:a.remove(s)
 for lab in kids(a,'global_label')+kids(a,'label'):
  lab[1]=Q(alias.get(str(lab[1]),str(lab[1])))
 tb=one(a,'title_block');one(tb,'rev')[1]=Q('0.3-HAND-SOLDER');one(tb,'date')[1]=Q('2026-10-03')
# Power: six-pin U5, keeping original four pin positions for existing wires.
a,defs,parts=pages['power'];u=parts['U5'];d=deepcopy(defs['Driver:P_U5']);d=[x for x in d if not(isinstance(x,list) and x[0]=='symbol')]
d.append(obj('(symbol "P_U5_0_1"(rectangle(start -7.62 6.35)(end 7.62 -6.35)(stroke(width .254)(type default))(fill(type background))))'))
c=['symbol',Q('P_U5_1_1')]
for n,pn,x,y,ang,typ in [('1','VIN',-10.16,2.54,0,'power_in'),('2','GND',0,-10.16,90,'power_in'),('3','ON',-10.16,-2.54,0,'input'),('4','CT',0,10.16,270,'passive'),('5','QOD',10.16,-2.54,180,'passive'),('6','VOUT',10.16,2.54,180,'power_out')]:
 c.append(obj(f'(pin {typ} line(at {x} {y} {ang})(length {3.81 if n in ["2","4"] else 2.54})(name "{pn}"(effects(font(size .9 .9))))(number "{n}"(effects(font(size .9 .9)))))'))
d.append(c);newdefs['Driver:P_U5']=d
for k,v in {'Value':'TPS22917DBVR','MPN':'TPS22917DBVR','Footprint':'Driver:Package_TO_SOT_SMD__SOT-23-6','Datasheet':'https://www.ti.com/lit/ds/symlink/tps22917.pdf'}.items():setprop(u,k,v)
for p in list(kids(u,'pin')):u.remove(p)
for n in range(1,7):u.append(['pin',Q(str(n)),['uuid',uid('U5pin'+str(n))]])
p=pinpos(u,d);a.append(label('SW_CT',p['4']));a.append(wire(p['5'],(180.34,p['5'][1])));a.append(wire((180.34,p['5'][1]),(180.34,p['6'][1])))
# C36 horizontal in the vacated upper-left input area, connected CT-to-VIN.
s=deepcopy(parts['C28']);one(s,'uuid')[1]=uid('C36');one(s,'lib_id')[1]=Q('Driver:P_C36');one(s,'at')[1:]=['134.62','27.94','90']
for k,v in {'Reference':'C36','Value':'1nF/50V C0G','Footprint':'Driver:Capacitor_SMD__C_0805_2012Metric','MPN':'C0805C102J5GACTU','Manufacturer':'KEMET','Datasheet':'https://search.kemet.com/download/specsheet/C0805C102J5GACTU'}.items():setprop(s,k,v)
for prop in kids(s,'property'):one(prop,'at')[1:]=['134.62', '20.32' if prop[1]=='Reference' else '24.13' if prop[1]=='Value' else '27.94','0']
for pin in kids(s,'pin'):one(pin,'uuid')[1]=uid('C36pin'+str(pin[1]))
one(one(one(s,'instances'),'project'),'path')[-2][1]=Q('C36')
cd=deepcopy(defs['Driver:P_C28']);cd[1]=Q('Driver:P_C36')
for ch in kids(cd,'symbol'):ch[1]=Q(str(ch[1]).replace('P_C28','P_C36'))
newdefs['Driver:P_C36']=cd;a.append(s);cp=pinpos(s,cd)
a.extend([wire(cp['1'],(121.92,27.94)),label('BENCH_3V3',(121.92,27.94)),wire(cp['2'],(p['4'][0],27.94)),wire((p['4'][0],27.94),p['4'])])
a.append(text('v0.3: direct links; SOT-23-6 switch; C36 connects CT to VIN',25.4,144.78,1.2))
# Panel ALERT is unused. Remove its wire branch by tracing electrical geometry.
a,defs,parts=pages['panel'];u4=parts['U4'];alert=pinpos(u4,defs['Driver:P_U4'])['3']
wires=kids(a,'wire');points=set()
for w in wires:
 for xy in one(w,'pts')[1:]:points.add(tuple(map(float,xy[1:])))
parent={p:p for p in points}
def find(p):
 while parent[p]!=p:parent[p]=parent[parent[p]];p=parent[p]
 return p
def union(p,q):parent[find(p)]=find(q)
for w in wires:
 aa,bb=[tuple(map(float,x[1:])) for x in one(w,'pts')[1:]]
 for pp in points:
  if abs((bb[0]-aa[0])*(pp[1]-aa[1])-(bb[1]-aa[1])*(pp[0]-aa[0]))<1e-7 and min(aa[0],bb[0])-1e-7<=pp[0]<=max(aa[0],bb[0])+1e-7 and min(aa[1],bb[1])-1e-7<=pp[1]<=max(aa[1],bb[1])+1e-7:union(aa,pp)
branch=find(alert)
for w in wires:
 pp=tuple(map(float,one(w,'pts')[1][1:]));
 if find(pp)==branch:a.remove(w)
for l in kids(a,'global_label'):
 if l[1]=='ALERT_N':a.remove(l)
a.append(nc(alert))
# Interface: rebuild as direct, wired signal chains; retain surviving component UUIDs.
a,defs,parts=pages['interface'];keep=[x for x in a if not(isinstance(x,list) and x[0] in ['wire','junction','global_label','label','no_connect','text','rectangle','symbol'])]
nodes=[]
def place(ref,x,y,ang=0):
 s=deepcopy(parts[ref]);one(s,'at')[1:]=[str(x),str(y),str(ang)]
 for prop in kids(s,'property'):
  dx=0 if ang==90 else 5.08;dy=-7.62 if prop[1]=='Reference' else -3.81 if prop[1]=='Value' else 0
  one(prop,'at')[1:]=[str(x+dx),str(y+dy),'0']
 nodes.append(s);return pinpos(s,defs[one(s,'lib_id')[1]])
for rr in ['R44','R45','R46','R47','R48']:
 dd=deepcopy(defs['Driver:P_'+rr])
 for cc in kids(dd,'symbol'):
  for pp in kids(cc,'pin'):
   nn=str(one(pp,'number')[1]);one(pp,'at')[1:]=['0','3.81' if nn=='1' else '-3.81','270' if nn=='1' else '90']
 defs['Driver:P_'+rr]=dd;newdefs['Driver:P_'+rr]=dd
j=place('J2',58.42,114.3)
# J2 pin16 now NC, leave the physical header unchanged.
jd=deepcopy(defs['Driver:P_J2'])
for ch in kids(jd,'symbol'):
 for pp in kids(ch,'pin'):
  if one(pp,'number')[1]=='16':one(pp,'name')[1]=Q('NC')
newdefs['Driver:P_J2']=jd
for pin,r,net,pull,target in [('1','R39','SCLK','R44','GND'),('3','R40','SI0','R45','GND'),('7','R41','CS_M_N','R46','EPD_3V3'),('9','R42','CS_S_N','R47','EPD_3V3'),('11','R43','RES_N','R48','GND')]:
 y=j[pin][1];rp=place(r,116.84,y,90);pp=place(pull,152.4,y+5.08,0)
 keep.extend([wire(j[pin],rp['1']),label(oldparts['J2']['pins'][pin],(91.44,y)),wire(rp['2'],(190.5,y)),label(net,(190.5,y),180),wire((152.4,y),pp['1']),wire(pp['2'],(152.4,y+12.7)),label(target,(152.4,y+12.7))])
for pin,net in [('5','SI1'),('13','BUSY_N'),('15','EPD_PWR_EN')]:keep.extend([wire(j[pin],(190.5,j[pin][1])),label(net,(190.5,j[pin][1]),180)])
for n in ['2','4','6','8','10','12','14']:
 keep.extend([wire(j[n],(30.48,j[n][1])),label('GND',(30.48,j[n][1]))])
keep.append(nc(j['16']))
# Test pads remain copper-only DNP; two rows outside signal diagram.
for i in range(1,25):
 ref='TP'+str(i);col=(i-1)%12;row=(i-1)//12;p=place(ref,30.48+col*40.64,330.2+row*50.8,180)['1']
 keep.extend([wire(p,(p[0],p[1]+10.16)),label(alias.get(oldparts[ref]['pins']['1'],oldparts[ref]['pins']['1']),(p[0],p[1]+10.16))])
keep.extend(nodes);keep.extend([text('Direct 3.3V host interface - NO power-off signal isolation',25.4,15.24,2),text('Host first ON / last OFF. Screen OFF: no GPIO HIGH, no pull-ups.',25.4,254,1.5),text('J2.16 unused. No live plugging. Short cable <= 10cm.',25.4,264.16,1.5),text('Test pads: copper only, no parts to buy or solder',25.4,304.8,1.5)])
pages['interface']=(keep,defs,parts)
# Update embedded and project libraries together; prune unused per-instance definitions.
lib=parse((B/'lib/Driver.kicad_sym').read_text())
for name,d in newdefs.items():
 for old in list(kids(lib,'symbol')):
  if old[1]==name:lib.remove(old)
 lib.append(deepcopy(d))
for name,(a,defs,parts) in pages.items():
 # Split all T connections and prune dangling wire remnants left by removed parts.
 def posof(w):return [tuple(map(float,x[1:])) for x in one(w,'pts')[1:]]
 pins=set()
 for sy in kids(a,'symbol'):
  dd=newdefs.get(str(one(sy,'lib_id')[1]),defs.get(str(one(sy,'lib_id')[1])))
  pins.update(pinpos(sy,dd).values())
 protected=pins|{tuple(map(float,one(l,'at')[1:3])) for l in kids(a,'global_label')+kids(a,'label')}
 ws=kids(a,'wire');pts=protected|{p for w in ws for p in posof(w)}
 split=[]
 for w in ws:
  aa,bb=posof(w)
  pp=sorted([p for p in pts if abs((bb[0]-aa[0])*(p[1]-aa[1])-(bb[1]-aa[1])*(p[0]-aa[0]))<1e-7 and min(aa[0],bb[0])-1e-7<=p[0]<=max(aa[0],bb[0])+1e-7 and min(aa[1],bb[1])-1e-7<=p[1]<=max(aa[1],bb[1])+1e-7],key=lambda p:(p[0]-aa[0])**2+(p[1]-aa[1])**2)
  split.extend(zip(pp,pp[1:]))
 edges=set(tuple(sorted([aa,bb])) for aa,bb in split if aa!=bb)
 while True:
  degree={p:sum(p in e for e in edges) for e in edges for p in e}
  dead={p for p,n in degree.items() if n==1 and p not in protected}
  if not dead:break
  edges={e for e in edges if not set(e)&dead}
 a[:]=[x for x in a if not(isinstance(x,list) and x[0] in ['wire','junction'])]
 a.extend(wire(aa,bb) for aa,bb in sorted(edges))
 degree={p:sum(p in e for e in edges) for e in edges for p in e}
 for p,n in degree.items():
  if n>2:a.append(obj(f'(junction(at {p[0]} {p[1]})(diameter 0)(color 0 0 0 0)(uuid {dump(uid(name+str(p)))}))'))
 used={str(one(s,'lib_id')[1]) for s in kids(a,'symbol')};ls=one(a,'lib_symbols');ls[:]=['lib_symbols']+[deepcopy(newdefs[n] if n in newdefs else defs[n]) for n in sorted(used)]
 (R/(name+'.kicad_sch')).write_text(dump(a)+'\n')
(R/'lib/Driver.kicad_sym').write_text(dump(lib)+'\n')
# Update fixed design mapping, maintaining stable surviving UUIDs and MPNs.
data['revision']='0.3-hand-solder';data['parts']=[p for p in data['parts'] if p['ref'] not in removed]
for p in data['parts']:
 p['pins']={n:alias.get(net,net) for n,net in p['pins'].items()}
 if p['ref']=='J2':p['pins']['16']=None
 if p['ref']=='U4':p['pins']['3']=None
 if p['ref']=='U5':p.update(value='TPS22917DBVR',mpn='TPS22917DBVR',fp='Package_TO_SOT_SMD:SOT-23-6',url='https://www.ti.com/lit/ds/symlink/tps22917.pdf',pins={'1':'BENCH_3V3','2':'GND','3':'EPD_PWR_EN','4':'SW_CT','5':'VIN','6':'VIN'})
p=deepcopy(oldparts['C28']);p.update(ref='C36',value='1nF/50V C0G',mpn='C0805C102J5GACTU',vendor='KEMET',fp='Capacitor_SMD:C_0805_2012Metric',url='https://search.kemet.com/download/specsheet/C0805C102J5GACTU',pins={'1':'BENCH_3V3','2':'SW_CT'},uuid=str(uid('C36')),xy=[34,66]);data['parts'].append(p)
(R/'design-data.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
(R/'reports/hand-solder-v0.3/change-map.json').write_text(json.dumps({'removed':sorted(removed),'aliases':alias,'assembled_before':129,'assembled_after':104,'smt_after':102},indent=2)+'\n')
print('Updated three native schematics and design mapping')
