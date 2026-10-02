#!/usr/bin/env python3
"""Redraw panel/interface from saved baselines; retain all physical pin identities.
Requires --apply; do not rerun after subsequent manual schematic editing.
Standard passive/FET geometry is copied from the installed KiCad library.
"""
from pathlib import Path
from copy import deepcopy
import json,math,uuid,sys
from schematic_sexp import Q,parse,dump,kids,one
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'reports/panel-interface-redraw'
if '--apply' not in sys.argv:raise SystemExit('Pass --apply to rebuild panel/interface from preserved baselines.')
KS=Path('/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols')
cache={};newlib={};summary={}
data={p['ref']:p for p in json.loads((ROOT/'design-data.json').read_text())['parts']}
def standard(l,n):
 if l not in cache:cache[l]=parse((KS/(l+'.kicad_sym')).read_text())
 return deepcopy(next(s for s in kids(cache[l],'symbol') if s[1]==n))
def obj(s):return parse(s)
def mm(x):return round(x*2.54,6)
def v2(p):return f'{mm(p[0]):g} {mm(p[1]):g}'
def uid(s):return Q(str(uuid.uuid5(uuid.NAMESPACE_URL,'album/panel-interface-redraw/'+s)))
def rectangle(x1,y1,x2,y2):return obj(f'(rectangle (start {mm(x1)} {mm(y1)}) (end {mm(x2)} {mm(y2)})(stroke (width .254)(type default))(fill (type background)))')
def textgraphic(s,x,y,size=.9):return obj(f'(text {json.dumps(s)} (at {mm(x)} {mm(y)} 0)(effects (font (size {size} {size}))))')
def linegraphic(pts):return obj(f'(polyline (pts {" ".join("(xy "+v2(p)+")" for p in pts)})(stroke (width .254)(type default))(fill (type none)))')

class Sheet:
 def __init__(self,name):
  self.name=name;self.old=parse((BASE/(name+'-before.kicad_sch')).read_text())
  self.parts={next(p[2] for p in kids(s,'property') if p[1]=='Reference'):deepcopy(s) for s in kids(self.old,'symbol')}
  self.original_lib={str(s[1]):s for s in kids(one(self.old,'lib_symbols'),'symbol')}
  self.coords={};self.defs={};self.nodes=[];self.placed={};self.segments=[];self.labels=[];self.grounds=[];self.tags=[];self.nc=[]
  self.path=one(one(one(next(iter(self.parts.values())),'instances'),'project'),'path')[1]
  for ref,s in self.parts.items():
   name=str(one(s,'lib_id')[1]);source=deepcopy(self.original_lib[name]);kind=None
   if ref.startswith('C'):kind=('Device','C')
   elif ref.startswith('R'):kind=('Device','R')
   elif ref.startswith('Q'):kind=('Transistor_FET','Q_NMOS_GSD')
   if kind:
    st=standard(*kind);olds={str(one(p,'number')[1]):p for c in kids(source,'symbol') for p in kids(c,'pin')}
    source=[x for x in source if not(isinstance(x,list) and x[0] in ['symbol','pin_names','pin_numbers'])]
    for k in ['pin_names','pin_numbers']:
     if one(st,k):source.append(deepcopy(one(st,k)))
    for c in kids(st,'symbol'):
     c[1]=Q(name.split(':',1)[1]+str(c[1])[len(kind[1]):])
     for p in kids(c,'pin'):p[1]=olds[str(one(p,'number')[1])][1]
     source.append(c)
   self.define(ref,source)
 def define(self,ref,source):
  name=str(one(self.parts[ref],'lib_id')[1]);self.defs[name]=source;newlib[name]=source
  self.coords[ref]={str(one(p,'number')[1]):tuple(map(float,one(p,'at')[1:3])) for c in kids(source,'symbol') for p in kids(c,'pin')}
 def custom(self,ref,body,pins,graphics=()):
  name=str(one(self.parts[ref],'lib_id')[1]);source=deepcopy(self.original_lib[name]);oldpins={str(one(p,'number')[1]):p for c in kids(source,'symbol') for p in kids(c,'pin')}
  assert set(map(str,pins))==set(oldpins),(ref,set(pins)^set(oldpins))
  source=[x for x in source if not(isinstance(x,list) and x[0] in ['symbol','pin_names','pin_numbers'])]
  source.append(obj('(pin_names (offset 1.016))'))
  base=name.split(':',1)[1];source.append(['symbol',Q(base+'_0_1'),*body,*graphics]);unit=['symbol',Q(base+'_1_1')]
  for num,(x,y,a,length,pname) in pins.items():
   p=deepcopy(oldpins[str(num)]);one(p,'at')[1:]=[str(mm(x)),str(mm(y)),str(a)];one(p,'length')[1]=str(mm(length));one(p,'name')[1]=Q(str(one(oldpins[str(num)],'name')[1]) if data[ref]['pins'][str(num)] is None else pname)
   for k in ['name','number']:one(one(one(p,k),'effects'),'font')[1:]=[['size','.95','.95']]
   unit.append(p)
  source.append(unit);self.define(ref,source)
 def place(self,ref,x,y,angle=0,fields=None,hide_value=False):
  assert ref not in self.placed,ref
  if ref.startswith('R') and angle==180:
   source=deepcopy(self.defs[str(one(self.parts[ref],'lib_id')[1])])
   for unit in kids(source,'symbol'):
    for pin in kids(unit,'pin'):
     a=one(pin,'at');a[1:]=[str(-float(a[1])),str(-float(a[2])),str((float(a[3])+180)%360)]
   self.define(ref,source);angle=0
  s=self.parts[ref];one(s,'at')[1:]=[str(mm(x)),str(mm(y)),str(angle)];rad=math.radians(angle)
  self.placed[ref]={n:(round(x+(lx*math.cos(rad)-ly*math.sin(rad))/2.54,6),round(y-(lx*math.sin(rad)+ly*math.cos(rad))/2.54,6)) for n,(lx,ly) in self.coords[ref].items()}
  for p in kids(s,'property'):
   if p[1] in ['Reference','Value']:
    if fields:dx,dy=fields[0 if p[1]=='Reference' else 1]
    elif ref.startswith('Q'):dx,dy=4,(-1.2 if p[1]=='Reference' else .3)
    elif angle in [90,270]:dx,dy=0,(-2.7 if p[1]=='Reference' else -1.4)
    else:dx,dy=2,(-.7 if p[1]=='Reference' else .7)
    one(p,'at')[1:]=[str(mm(x+dx)),str(mm(y+dy)),str(angle%180 if not fields else 0)]
    eff=one(p,'effects');one(one(eff,'font'),'size')[1:]=['1','1']
    for k in ['justify','hide']:
     if one(eff,k):eff.remove(one(eff,k))
    if dx:eff.append(['justify','left'])
    if hide_value and p[1]=='Value':eff.append(['hide','yes'])
   else:one(p,'at')[1:]=[str(mm(x)),str(mm(y)),'0']
  self.nodes.append(s)
 def pin(self,r,n):return self.placed[r][str(n)]
 def wire(self,net,*pts):
  for a,b in zip(pts,pts[1:]):
   a=tuple(a);b=tuple(b)
   if a==b:continue
   assert a[0]==b[0] or a[1]==b[1],(net,a,b)
   self.segments.append((net,a,b))
 def lab(self,net,xy,angle=0):self.labels.append((net,tuple(xy),angle))
 def gnd(self,x,y):self.grounds.append((x,y))
 def block(self,t,x,y,w,h):
  self.tags.append(obj(f'(rectangle (start {v2((x,y))})(end {v2((x+w,y+h))})(stroke (width .254)(type dash))(fill (type none))(uuid {dump(uid(self.name+t+"box"))}))'))
  self.note(t,x+2,y+2,1.65)
 def note(self,t,x,y,size=1.0):self.tags.append(obj(f'(text {json.dumps(t)}(at {v2((x,y))} 0)(effects (font (size {size} {size}))(justify left))(uuid {dump(uid(self.name+t+str(x)+str(y)))}))'))
 def export(self):
  assert set(self.parts)==set(self.placed),set(self.parts)-set(self.placed)
  g=standard('power','GND');g[1]=Q('Driver:GND');self.defs['Driver:GND']=g;newlib['Driver:GND']=g
  for i,xy in enumerate(self.grounds):
   ref='#PWR'+('N' if self.name=='panel' else 'I')+f'{i+1:02}'
   self.nodes.append(obj(f'(symbol (lib_id "Driver:GND")(at {v2(xy)} 0)(unit 1)(in_bom no)(on_board yes)(dnp no)(uuid {dump(uid(ref))})(property "Reference" "{ref}"(at {v2(xy)} 0)(effects (font (size 1 1))(hide yes)))(property "Value" "GND"(at {v2((xy[0],xy[1]+2))} 0)(effects (font (size 1 1))))(pin "1"(uuid {dump(uid(ref+"pin"))}))(instances (project "gdep133c02-driver"(path {dump(self.path)}(reference "{ref}")(unit 1)))))'))
  allpoints={p for n,a,b in self.segments for p in [a,b]}|{xy for n,xy,a in self.labels}|set(self.grounds)|{xy for r in self.placed for xy in self.placed[r].values()}
  def contains(a,b,p):return abs((b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0]))<1e-7 and min(a[0],b[0])-1e-7<=p[0]<=max(a[0],b[0])+1e-7 and min(a[1],b[1])-1e-7<=p[1]<=max(a[1],b[1])+1e-7
  out=set()
  for n,a,b in self.segments:
   ps=sorted([p for p in allpoints if contains(a,b,p)],key=lambda p:(p[0]-a[0])**2+(p[1]-a[1])**2)
   for p,q in zip(ps,ps[1:]):out.add((n,*sorted([p,q])))
  pointnets={}
  for n,a,b in out:
   for p in [a,b]:pointnets.setdefault(p,set()).add(n)
  conflicts=[(p,ns) for p,ns in pointnets.items() if len(ns)>1]
  assert not conflicts,conflicts
  for r,ps in self.placed.items():
   for num,xy in ps.items():
    expected=data[r]['pins'][num]
    if expected is None:
     assert xy not in pointnets,(r,num,'NC touches wire');self.nc.append((r,num,xy))
    else:assert pointnets.get(xy)=={expected},(r,num,xy,pointnets.get(xy),expected)
  root=[x for x in self.old if not(isinstance(x,list) and x[0] in ['lib_symbols','symbol','wire','global_label','label','junction','no_connect','text','rectangle'])]
  one(root,'paper')[1:]=[Q('User'),'594','450']
  one(root,'title_block')[1:]=[['title',Q(self.name.capitalize()+' - wired functional circuits')],['date',Q('2026-10-02')],['rev',Q('0.2-CAD-REVIEW')]]
  root.append(['lib_symbols',*self.defs.values()]);root.extend(self.tags)
  for i,(n,a,b) in enumerate(sorted(out)):root.append(obj(f'(wire (pts (xy {v2(a)})(xy {v2(b)}))(stroke (width 0)(type default))(uuid {dump(uid(self.name+"wire"+str(i)))}))'))
  for p in sorted(pointnets):
   if sum(p in [a,b] for n,a,b in out)>=3:root.append(obj(f'(junction (at {v2(p)})(diameter 0)(color 0 0 0 0)(uuid {dump(uid(self.name+"junction"+str(p)))}))'))
  for i,(n,xy,a) in enumerate(self.labels):root.append(obj(f'(global_label {json.dumps(n)}(shape bidirectional)(at {v2(xy)} {a})(effects (font (size .95 .95))(justify {"right" if a==180 else "left"}))(uuid {dump(uid(self.name+"label"+str(i)))})(property "Intersheetrefs" ""(at {v2(xy)} 0)(effects (font (size .95 .95))(hide yes))))'))
  for r,num,xy in self.nc:root.append(obj(f'(no_connect (at {v2(xy)})(uuid {dump(uid(self.name+"nc"+r+num))}))'))
  root.extend(self.nodes)
  (ROOT/(self.name+'.kicad_sch')).write_text('(kicad_sch\n'+'\n'.join(dump(x) for x in root[1:])+'\n)\n')
  summary[self.name]={'physical_components':len(self.parts),'wire_segments':len(out),'interface_labels':len(self.labels),'new_ground_symbols':len(self.grounds),'intentional_nc_pins':len(self.nc)}

# PANEL: connector retains one symbol instance, with pins laid out by function.
p=Sheet('panel');pins={};body=[rectangle(-15,75,15,-75)]
left={9:('AVDD',17),10:('VDD',21),19:('VDDIO',25),12:('VCC',31),18:('VCC1',34),13:('VDDP',40),14:('VDDP',43),16:('VDDN',49),17:('VDDN',52),59:('VGH',58),60:('VGL',62),41:('VNCP_3P5V',68),56:('VBB_3P5V',72),1:('VCOMBD_M',83),36:('VCOMBD_S',88),2:('RESEC',99),3:('GDRC',103),4:('RESEN',107),5:('GDRN',111),6:('RESEP',115),7:('GDRP',119),33:('DRVP',126),34:('FBP',130),37:('DRVN',134),38:('FBN',138),39:('REG_VGN',142),8:('GND',148),26:('GND',152),35:('GND',156)}
right={20:('TSCL',17),21:('TSDA',21),22:('BS0',30),23:('BS1',35),24:('RES_N',42),25:('BUSY_N',47),27:('CS_M_N',52),28:('SCLK',57),29:('SI0',62),30:('SI1',67),31:('SI2',72),32:('SI3',77),58:('CS_S_N',82),54:('FPL_VCOM',85),55:('TFT_VCOM',89)}
for nums,net,y in [((42,45),'VSPH',99),((43,46),'VSPL',110),((44,47),'VSPL2',121),((48,53),'VSNH',132),((49,52),'VSNL',143),((50,51),'VSNL2',154)]:
 for i,n in enumerate(nums):right[n]=(net,y+3*i)
for n,(net,y) in left.items():pins[str(n)]=(-19,88-y,0,4,net)
for n,(net,y) in right.items():pins[str(n)]=(19,88-y,180,4,net)
for i,n in enumerate([11,15,40,57]):pins[str(n)]=(-10+i*6,-78,90,3,'DRVN2 (NC)' if n==40 else 'NC')
graphics=[textgraphic('POWER',-9,73,1.3),textgraphic('LOGIC / SPI',9,63,1.3),textgraphic('GATE / SENSE',-8,-8,1.3),textgraphic('SOURCE RAILS',8,-7,1.3)]
p.custom('FPC1',body,pins,graphics);p.place('FPC1',50,88,fields=[(0,-81),(0,-79.5)])
p.block('1  Screen connector - pin numbers retained; functional pin layout',7,4,74,168)
p.note('Symbol grouping does not represent physical FPC pin positions.',9,170,.85)
for n,(net,y) in left.items():
 if n in [12,18,13,14,16,17,1,36,8,26,35]:continue
 p.wire(net,p.pin('FPC1',n),(15,y));p.lab(net,(15,y))
for nums,net,y in [([12,18],'VCC',31),([13,14],'VDDP',40),([16,17],'VDDN',49)]:
 for n in nums:q=p.pin('FPC1',n);p.wire(net,q,(27,q[1]),(27,y))
 p.wire(net,(27,y),(15,y));p.lab(net,(15,y))
p.place('C7',20,36);p.wire('VCC',(20,31),p.pin('C7',1));p.wire('GND',p.pin('C7',2),(20,41));p.gnd(20,41)
for ref,num,x,y in [('C10',1,12,87),('C11',36,22,93)]:
 net=data[ref]['pins']['1'];p.place(ref,x,y);q=p.pin('FPC1',num);p.wire(net,q,(x,q[1]),p.pin(ref,1));p.lab(net,(x,q[1]));p.wire('GND',p.pin(ref,2),(x,y+4));p.gnd(x,y+4)
for n in [8,26,35]:q=p.pin('FPC1',n);p.wire('GND',q,(27,q[1]))
p.wire('GND',(27,148),(27,160));p.gnd(27,160)
# Mode straps and signal defaults.
p.block('2  SPI mode / signal defaults',83,22,50,76)
for r,n,y in [('R24',22,30),('R25',23,35)]:
 p.place(r,95,y,90);net=data[r]['pins']['1'];p.wire(net,p.pin('FPC1',n),p.pin(r,1));p.wire('VDD',p.pin(r,2),(108,y))
p.wire('VDD',(108,30),(108,35));p.lab('VDD',(108,30),180)
for net,y in [('BS0',30),('BS1',35)]:p.lab(net,(82,y))
for n in [24,25,27,28,29,30,31,32,58]:q=p.pin('FPC1',n);net=data['FPC1']['pins'][str(n)];p.wire(net,q,(120,q[1]));p.lab(net,(120,q[1]),180)
p.place('R1',112,42,180);p.wire('BUSY_N',p.pin('R1',1),(112,47));p.wire('VDDIO',p.pin('R1',2),(112,37));p.lab('VDDIO',(112,37),180)
for r,n,x in [('R35',31,85),('R36',32,116)]:
 p.place(r,x,88);net=data[r]['pins']['1'];p.wire(net,(x,p.pin('FPC1',n)[1]),p.pin(r,1));p.wire('GND',p.pin(r,2),(x,94))
p.wire('GND',(85,94),(116,94));p.gnd(116,94)
# Temperature sensor, direct connector links and pullups.
p.block('3  Panel-controlled temperature sensor',136,4,88,54)
up={'1':(-12,8,0,4,'SDA'),'2':(-12,12,0,4,'SCL'),'3':(12,4,180,4,'ALERT_N'),'4':(7,-15,90,4,'GND'),'5':(-5,-15,90,4,'A2'),'6':(-1,-15,90,4,'A1'),'7':(3,-15,90,4,'A0'),'8':(0,19,270,4,'VDD')}
p.custom('U4',[rectangle(-8,15,8,-11)],up);p.place('U4',154,29,fields=[(-7,1),(-7,3)])
for n,net,y in [(2,'TSCL',17),(1,'TSDA',21)]:
 p.wire(net,p.pin('FPC1',20 if n==2 else 21),p.pin('U4',n));p.lab(net,(90,y))
for r,net,x,y in [('R20','TSCL',100,15.5),('R21','TSDA',125,19.5)]:
 # Pullup pin1 signal, pin2 supply.
 p.place(r,x,y,180)
 p.wire(net,p.pin(r,1),(x,17 if net=='TSCL' else 21));q=p.pin(r,2);p.wire('EPD_3V3',q,(x,7))
p.wire('EPD_3V3',(100,7),(206,7));p.wire('EPD_3V3',(154,7),p.pin('U4',8));p.lab('EPD_3V3',(206,7),180)
p.place('C27',202,38);p.wire('EPD_3V3',(202,7),p.pin('C27',1));p.wire('GND',p.pin('C27',2),(202,49))
for n in [4,5,6,7]:q=p.pin('U4',n);p.wire('GND',q,(q[0],49))
p.wire('GND',(149,49),(202,49));p.gnd(154,49)
p.place('R22',180,18,180);p.wire('EPD_3V3',(180,7),p.pin('R22',2));p.wire('ALERT_N',p.pin('R22',1),(180,25))
p.place('R23',190,34);p.wire('ALERT_N',p.pin('U4',3),(190,25),p.pin('R23',1));p.lab('ALERT_N',(185,25),180);p.wire('GND',p.pin('R23',2),(190,49))
p.note('R23 DNP: alert output is not strapped to ground.',140,55,.9)
# Common-electrode output bypass and six capacitor banks, directly paired at connector.
for ref,n,x,y in [('C9',54,88,88),('C8',55,106,92)]:
 net=data[ref]['pins']['1'];p.place(ref,x,y);q=p.pin('FPC1',n);p.wire(net,q,(x,q[1]),p.pin(ref,1));p.lab(net,(x,q[1]));p.wire('GND',p.pin(ref,2),(x,y+3));p.gnd(x,y+3)
p.block('4  Source outputs / input straps / capacitor banks',83,96,99,74)
for refs,nums,net,y in [(['C1','C103','C104','C105'],[42,45],'VSPH',99),(['C2','C106','C107','C108'],[43,46],'VSPL',110),(['C3','C109','C110','C111'],[44,47],'VSPL2',121),(['C4','C112','C113','C114'],[48,53],'VSNH',132),(['C5','C115','C116','C117'],[49,52],'VSNL',143),(['C6','C118','C119','C120'],[50,51],'VSNL2',154)]:
 for n in nums:q=p.pin('FPC1',n);p.wire(net,q,(75,q[1]),(75,y))
 p.wire(net,(75,y),(148,y));p.lab(net,(78,y))
 for i,r in enumerate(refs):
  x=94+i*18;p.place(r,x,y+5);p.wire(net,(x,y),p.pin(r,1));p.wire('GND',p.pin(r,2),(x,y+9))
 p.wire('GND',(94,y+9),(148,y+9));p.gnd(148,y+9)
 p.note('Nominal 33.3uF; effective capacitance pending.',155,y+6,.85)
p.note('Dots join wires; crossings without dots do not connect. Global labels are cross-sheet interfaces.',9,175,.95)
p.export()

# INTERFACE: complete 8-channel buffers in one symbol, with per-channel arrows.
s=Sheet('interface');s.block('1  Host connector - 3.3V logic / common ground',7,5,47,88)
jpins={}
for i in range(8):
 y=18+i*7;odd=2*i+1;even=odd+1
 jpins[str(odd)]=(6,45-y,180,3,data['J2']['pins'][str(odd)].replace('HOST_',''))
 jpins[str(even)]=(-6,45-y,0,3,'3V3' if even==16 else 'GND')
s.custom('J2',[rectangle(-3,30,3,-26)],jpins);s.place('J2',23,45,fields=[(0,-33),(0,-31.5)])
for n in range(1,17):
 net=data['J2']['pins'][str(n)];q=s.pin('J2',n)
 if n%2:s.wire(net,q,(42,q[1]));s.lab(net,(42,q[1]),180)
 elif n!=16:s.wire('GND',q,(11,q[1]))
 else:s.wire(net,q,(11,q[1]));s.lab(net,(11,q[1]))
s.wire('GND',(11,18),(11,62));s.gnd(11,62)
s.note('J2.16 powers host-side logic only.',9,85,.9)
# Gate rows are drawn internally as buffer triangles and wired externally.
def buffer(ref,cx,rows,oe_rows,bottom):
 pinmap={};graphics=[]
 channelnums=[(2,18),(4,16),(6,14),(8,12),(11,9),(13,7),(15,5),(17,3)]
 for i,((a,b),y) in enumerate(zip(channelnums,rows)):
  group='1' if i<4 else '2';channel=str(i%4+1)
  pinmap[str(a)]=(-14,65-y,0,4,group+'A'+channel);pinmap[str(b)]=(14,65-y,180,4,group+'Y'+channel)
  yy=65-y;graphics.extend([linegraphic([(-10,yy),(-3,yy)]),linegraphic([(-3,yy+2),(-3,yy-2),(3,yy),(-3,yy+2)]),linegraphic([(3,yy),(10,yy)])])
 for n,y in zip([1,19],oe_rows):pinmap[str(n)]=(-14,65-y,0,4,'1OE_N' if n==1 else '2OE_N')
 pinmap['20']=(0,49,270,4,'VCC');pinmap['10']=(0,65-bottom,90,4,'GND')
 s.custom(ref,[rectangle(-10,45,10,65-bottom+4)],pinmap,graphics);s.place(ref,cx,65,fields=[(-8,-46),(-8,-44.5)])

s.block('2  Host to panel - buffered SPI / default levels',58,5,100,141)
rows=[27,39,51,63,75,87,95,103];buffer('U6',94,rows,[111,115],124)
for r,pin_in,pin_out,host,raw,out,y in [('R39',2,18,'HOST_SCLK','BUF_SCLK','SCLK',27),('R40',4,16,'HOST_MOSI','BUF_MOSI','SI0',39),('R41',6,14,'HOST_CS_M_N','BUF_CS_M_N','CS_M_N',51),('R42',8,12,'HOST_CS_S_N','BUF_CS_S_N','CS_S_N',63),('R43',11,9,'HOST_RES_N','BUF_RES_N','RES_N',75)]:
 s.wire(host,(65,y),s.pin('U6',pin_in));s.lab(host,(65,y));s.place(r,122,y,90);s.wire(raw,s.pin('U6',pin_out),s.pin(r,1));s.lab(raw,(113,y));s.wire(out,s.pin(r,2),(153,y));s.lab(out,(153,y),180)
for r,net,y in [('R44','SCLK',27),('R45','SI0',39),('R46','CS_M_N',51),('R47','CS_S_N',63),('R48','RES_N',75)]:
 pullup=r in ['R46','R47'];x=146 if pullup else 140;s.place(r,x,y-4 if pullup else y+4,180 if pullup else 0);s.wire(net,(x,y),s.pin(r,1));q=s.pin(r,2)
 if pullup:s.wire('VDDIO',q,(x,y-8));s.lab('VDDIO',(x,y-8),180)
 else:s.wire('GND',q,(x,y+7));s.gnd(x,y+7)
for n in [13,15,17]:q=s.pin('U6',n);s.wire('GND',q,(76,q[1]))
s.wire('GND',(76,87),(76,106));s.gnd(76,106)
for n in [1,19]:q=s.pin('U6',n);s.wire('OE_PANEL_N',q,(74,q[1]))
s.wire('OE_PANEL_N',(74,111),(74,134));s.wire('OE_PANEL_N',(74,111),(64,111));s.lab('OE_PANEL_N',(64,111))
s.place('Q9',73,136);s.wire('OE_PANEL_N',(74,134),s.pin('Q9',3));s.wire('GND',s.pin('Q9',2),(74,142));s.gnd(74,142);s.wire('EPD_PWR_EN',(61,136),s.pin('Q9',1));s.lab('EPD_PWR_EN',(61,136))
s.place('R37',62,124,180);s.wire('OE_PANEL_N',s.pin('R37',1),(62,130),(74,130));s.wire('EPD_3V3',s.pin('R37',2),(62,119));s.lab('EPD_3V3',(62,119))
s.wire('GND',s.pin('U6',10),(94,128));s.gnd(94,128)
s.place('C34',112,12);s.wire('EPD_3V3',(94,8),(112,8),s.pin('C34',1));s.wire('EPD_3V3',(94,8),s.pin('U6',20));s.lab('EPD_3V3',(94,8));s.wire('GND',s.pin('C34',2),(112,17));s.gnd(112,17)
s.note('EPD_PWR_EN high: Q9 pulls both OE inputs low.',84,140,.85)

s.block('3  Panel to host - BUSY / MISO buffer',162,5,68,141)
rows7=[27,39,51,63,75,87,99,111];buffer('U7',194,rows7,[119,123],132)
for n1,n2,inp,out,y in [(2,18,'BUSY_N','HOST_BUSY_N',27),(4,16,'SI1','HOST_MISO',39)]:
 s.wire(inp,(165,y),s.pin('U7',n1));s.lab(inp,(165,y));s.wire(out,s.pin('U7',n2),(225,y));s.lab(out,(225,y),180)
for n in [6,8,11,13,15,17]:q=s.pin('U7',n);s.wire('GND',q,(173,q[1]))
s.wire('GND',(173,51),(173,114));s.gnd(173,114)
for n in [1,19]:q=s.pin('U7',n);s.wire('OE_HOST_N',q,(176,q[1]))
s.wire('OE_HOST_N',(176,119),(176,134));s.lab('OE_HOST_N',(176,119))
s.place('Q10',175,136);s.wire('OE_HOST_N',(176,134),s.pin('Q10',3));s.wire('GND',s.pin('Q10',2),(176,142));s.gnd(176,142);s.wire('EPD_PWR_EN',(164,136),s.pin('Q10',1));s.lab('EPD_PWR_EN',(164,136))
s.place('R38',165,124,180);s.wire('OE_HOST_N',s.pin('R38',1),(165,130),(176,130));s.wire('HOST_3V3',s.pin('R38',2),(165,119));s.lab('HOST_3V3',(165,119))
s.wire('GND',s.pin('U7',10),(194,138));s.gnd(194,138)
s.place('C35',212,12);s.wire('HOST_3V3',(194,8),(212,8),s.pin('C35',1));s.wire('HOST_3V3',(194,8),s.pin('U7',20));s.lab('HOST_3V3',(194,8));s.wire('GND',s.pin('C35',2),(212,17));s.gnd(212,17)
s.note('Unused inputs grounded; unused outputs marked NC.',182,143,.85)
# Test pads are grouped by measurement purpose, with one shared ground bus.
s.block('4  Power test points',7,147,223,13)
s.block('5  Control test points / common ground pads',7,160,177,13)
for i in range(1,25):
 r='TP'+str(i);source=deepcopy(s.original_lib[str(one(s.parts[r],'lib_id')[1])]);source=[x for x in source if not(isinstance(x,list) and x[0]=='symbol')];nm=str(one(s.parts[r],'lib_id')[1]).split(':',1)[1]
 source.append(obj(f'(symbol "{nm}_0_1"(circle (center 0 0)(radius 1.778)(stroke (width .254)(type default))(fill (type none))))'))
 source.append(obj(f'(symbol "{nm}_1_1"(pin passive line (at 0 -2.54 90)(length .762)(name "1"(effects (font (size .8 .8))))(number "1"(effects (font (size .8 .8))))))'))
 s.define(r,source);row=0 if i<=12 else 1;x=12+(18 if row==0 else 15)*((i-1)%12);y=155+13*row;s.place(r,x,y,180,fields=[(0,1.8),(0,3.2)],hide_value=True);net=data[r]['pins']['1'];s.wire(net,s.pin(r,1),(x,y-4))
 if net!='GND':s.lab(net,(x,y-4))
s.wire('GND',(57,164),(180,164));s.lab('GND',(180,164),180)
s.note('TP1-TP24 are copper pads; DNP crosses mean no assembled component, not an unconnected pin.',20,158.5,.85)
s.note('Dots join wires; crossings without dots do not connect. Global labels retain existing PCB net names.',9,175,.95)
s.export()
lib=parse((BASE/'Driver-before.kicad_sym').read_text());lib=[x for x in lib if not(isinstance(x,list) and x[0]=='symbol' and 'Driver:'+str(x[1]) in newlib)]
for name,source in newlib.items():a=deepcopy(source);a[1]=Q(name.split(':',1)[1]);lib.append(a)
(ROOT/'lib/Driver.kicad_sym').write_text(dump(lib)+'\n')
(BASE/'layout-summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
