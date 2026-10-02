#!/usr/bin/env python3
"""Redraw only the power sheet. Preserve component UUIDs, pins and fields.
Geometry for passives/transistors/diodes is copied from installed KiCad symbols.
Explicit --apply is required. Does not alter PCB or project design rules.
"""
from pathlib import Path
from copy import deepcopy
import math,json,uuid,sys
from schematic_sexp import Q,parse,dump,kids,one
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'reports/power-redraw'
if '--apply' not in sys.argv:raise SystemExit('Pass --apply to redraw the power sheet from its preserved baseline.')
old=parse((BASE/'power-before.kicad_sch').read_text());lib=parse((BASE/'Driver-before.kicad_sym').read_text())
parts={next(p[2] for p in kids(s,'property') if p[1]=='Reference'):deepcopy(s) for s in kids(old,'symbol')}
original_lib={str(s[1]):s for s in kids(one(old,'lib_symbols'),'symbol')}
KS=Path('/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols');cache={}
def standard(l,n):
 if l not in cache:cache[l]=parse((KS/(l+'.kicad_sym')).read_text())
 return deepcopy(next(s for s in kids(cache[l],'symbol') if s[1]==n))
def uid(s):return Q(str(uuid.uuid5(uuid.NAMESPACE_URL,'album/power-redraw/'+s)))
def obj(s):return parse(s)
def mm(v):return round(v*2.54,6)
def v2(xy):return f'{mm(xy[0]):g} {mm(xy[1]):g}'
newlib={};coords={};placed={};nodes=[];segments=[];labels=[];ground=[];tags=[]
# Retain original symbol identity and metadata; replace graphics and pin layout only.
for ref,s in parts.items():
 name='Driver:P_'+ref if not ref.startswith('#') else 'Driver:SupplyFlag'
 source=deepcopy(original_lib[name]);kind=None
 if ref.startswith('C'):kind=('Device','C')
 elif ref.startswith('R') or ref in ['U1','U2','U3']:kind=('Device','R')
 elif ref in ['L4','L5']:kind=('Device','FerriteBead')
 elif ref.startswith('L'):kind=('Device','L')
 elif ref in ['D1','D2','D4']:kind=('Device','D_Schottky')
 elif ref in ['D3','D5','D6']:kind=('Diode','BAT54S')
 elif ref in ['Q1','Q4']:kind=('Transistor_FET','Q_NMOS_GSD')
 elif ref in ['Q7','Q8']:kind=('Transistor_FET','Q_PMOS_GSD')
 elif ref=='Q3':kind=('Transistor_BJT','Q_PNP_BEC')
 elif ref=='Q6':kind=('Transistor_BJT','Q_NPN_BEC')
 if kind:
  st=standard(*kind);olds={one(p,'number')[1]:p for c in kids(source,'symbol') for p in kids(c,'pin')}
  source=[x for x in source if not (isinstance(x,list) and x[0] in ['symbol','pin_names','pin_numbers'])]
  for k in ['pin_names','pin_numbers']:
   if one(st,k):source.append(deepcopy(one(st,k)))
  for c in kids(st,'symbol'):
   c[1]=Q('P_'+ref+str(c[1])[len(kind[1]):])
   for p in kids(c,'pin'):p[1]=olds[one(p,'number')[1]][1]
   source.append(c)
 elif ref=='U5':
  # VIN left, VOUT right, ON left below VIN, GND downward.
  source=[x for x in source if not (isinstance(x,list) and x[0]=='symbol')]
  source.append(obj('(symbol "P_U5_0_1" (rectangle (start -7.62 6.35) (end 7.62 -6.35) (stroke (width .254) (type default)) (fill (type background))))'))
  c=['symbol',Q('P_U5_1_1')]
  for num,pname,x,y,angle in [('A2','VIN',-10.16,2.54,0),('A1','VOUT',10.16,2.54,180),('B2','ON',-10.16,-2.54,0),('B1','GND',0,-10.16,90)]:
   c.append(obj(f'(pin {"power_in" if num in ["A2","B1"] else "power_out" if num=="A1" else "input"} line (at {x} {y} {angle}) (length {3.81 if num=="B1" else 2.54}) (name "{pname}" (effects (font (size .9 .9)))) (number "{num}" (effects (font (size .9 .9)))))'))
  source.append(c)
 elif ref=='J1':
  source=[x for x in source if not (isinstance(x,list) and x[0]=='symbol')]
  source.append(obj('(symbol "P_J1_0_1" (rectangle (start -2.54 3.81) (end 2.54 -3.81) (stroke (width .254) (type default)) (fill (type background))))'))
  source.append(obj('(symbol "P_J1_1_1" (pin passive line (at 5.08 1.27 180) (length 2.54) (name "+3V3" (effects (font (size .9 .9)))) (number "1" (effects (font (size .9 .9))))) (pin power_out line (at 5.08 -1.27 180) (length 2.54) (name "GND" (effects (font (size .9 .9)))) (number "2" (effects (font (size .9 .9))))))'))
 newlib[name]=source
 coords[ref]={str(one(p,'number')[1]):tuple(map(float,one(p,'at')[1:3])) for c in kids(source,'symbol') for p in kids(c,'pin')}

def place(ref,x,y,angle=0):
 assert ref not in placed,ref
 s=parts[ref];a=one(s,'at');a[1:]=[str(mm(x)),str(mm(y)),str(angle)];rad=math.radians(angle)
 placed[ref]={n:(round(x+(lx*math.cos(rad)-ly*math.sin(rad))/2.54,6),round(y-(lx*math.sin(rad)+ly*math.cos(rad))/2.54,6)) for n,(lx,ly) in coords[ref].items()}
 for prop in kids(s,'property'):
  if prop[1] in ['Reference','Value']:
   # Values horizontal, independent of component rotation.
   if ref in ['Q7','Q8']:dx,dy=3.5,(7.5 if prop[1]=='Reference' else 9)
   elif ref in ['Q3']:dx,dy=5,(-4.5 if prop[1]=='Reference' else -3)
   elif ref.startswith('Q') or ref=='U5':dx,dy=5,(-1.5 if prop[1]=='Reference' else 0)
   elif ref=='J1':dx,dy=0,(-3.5 if prop[1]=='Reference' else -2.3)
   elif ref.startswith('#'):dx,dy=0,-3
   elif angle in [90,270] or ref.startswith('D'):dx,dy=0,(-2.8 if prop[1]=='Reference' else -1.5)
   else:dx,dy=2,(-.7 if prop[1]=='Reference' else .7)
   one(prop,'at')[1:]=[str(mm(x+dx)),str(mm(y+dy)),str(angle%180)]
   eff=one(prop,'effects');font=one(eff,'font');one(font,'size')[1:]=['1','1']
   if one(eff,'justify'):eff.remove(one(eff,'justify'))
   if dx:eff.append(['justify','left'])
  else:one(prop,'at')[1:]=[str(mm(x)),str(mm(y)),'0']
 nodes.append(s)
 return placed[ref]
def pin(r,n):return placed[r][str(n)]
def wire(net,*pts):
 for a,b in zip(pts,pts[1:]):
  a=tuple(a);b=tuple(b)
  if a==b:continue
  assert a[0]==b[0] or a[1]==b[1],(net,a,b)
  segments.append((net,a,b))
def link(net,*refs):wire(net,*[pin(*r) for r in refs])
def lab(net,xy,angle=0):labels.append((net,tuple(xy),angle))
def gnd(x,y):ground.append((x,y))
def block(text,x,y,w,h):
 tags.append(obj(f'(rectangle (start {v2((x,y))}) (end {v2((x+w,y+h))}) (stroke (width .254) (type dash)) (fill (type none)) (uuid {dump(uid(text+"box"))}))'))
 tags.append(obj(f'(text {json.dumps(text)} (at {v2((x+2,y+2))} 0) (effects (font (size 1.8 1.8)) (justify left)) (uuid {dump(uid(text+"title"))}))'))

block('1  3.3V input / load switch / supply distribution',7,7,213,48)
for r,x,y,a in [('J1',12,18.5,0),('R26',27,18,90),('C28',36,30,0),('R27',44,18,90),('U5',61,19,0),('R28',75,18,90),('R29',44,26,90),('R30',53,32,0),('C29',85,30,0),('C30',95,30,0),('L4',107,18,90),('L5',107,45,90),('R31',132,45,90),('R32',169,45,90),('C31',145,49.5,0),('C32',155,49.5,0),('R33',139,18,90),('R34',139,26,90),('C33',121,32,0)]:place(r,x,y,a)
wire('BENCH_3V3',pin('J1',1),pin('R26',1));lab('BENCH_3V3',(19,18))
wire('EPD_VDD',pin('R26',2),pin('R27',1));wire('EPD_VDD',(36,18),pin('C28',1));lab('EPD_VDD',(36,18))
wire('SW_IN',pin('R27',2),pin('U5','A2'));lab('SW_IN',(52,18))
wire('SW_OUT',pin('U5','A1'),pin('R28',1));lab('SW_OUT',(69,18))
wire('EPD_PWR_EN',(31,26),pin('R29',1));lab('EPD_PWR_EN',(31,26))
wire('SW_ON',pin('R29',2),(53,26),(53,20),pin('U5','B2'));wire('SW_ON',(53,26),pin('R30',1));lab('SW_ON',(53,26))
wire('VIN',pin('R28',2),pin('L4',1));wire('VIN',(85,18),pin('C29',1));wire('VIN',(95,18),pin('C30',1));wire('VIN',(100,18),(100,45),pin('L5',1));lab('VIN',(85,18))
wire('EPD_3V3',pin('L4',2),pin('R33',1));wire('EPD_3V3',(121,18),(121,26),pin('R34',1));wire('EPD_3V3',(121,26),pin('C33',1));lab('EPD_3V3',(121,18))
wire('VDD',pin('R33',2),(155,18));lab('VDD',(155,18),180)
wire('VDDIO',pin('R34',2),(155,26));lab('VDDIO',(155,26),180)
wire('AVDD_PRE',pin('L5',2),pin('R31',1));lab('AVDD_PRE',(116,45))
wire('AVDD_CAP',pin('R31',2),pin('R32',1));wire('AVDD_CAP',(145,45),pin('C31',1));wire('AVDD_CAP',(155,45),pin('C32',1));lab('AVDD_CAP',(145,45))
wire('AVDD',pin('R32',2),(186,45));lab('AVDD',(186,45),180)
wire('GND',(14,38),(121,38))
for r,n in [('J1',2),('C28',2),('U5','B1'),('R30',2),('C29',2),('C30',2),('C33',2)]:q=pin(r,n);wire('GND',q,(q[0],38))
wire('GND',(145,53),(155,53))
for r in ['C31','C32']:q=pin(r,2);wire('GND',q,(q[0],53))
gnd(14,38);gnd(155,53)
for r,xy in [('#FLG01',(52,18)),('#FLG02',(121,18))]:place(r,*xy)

block('2  Positive source rail (VDDP)',7,58,63,42)
for r,x,y,a in [('L1',26,66,90),('Q1',38,78,0),('D1',48,66,180),('U1',39,90,0),('R2',24,90,0),('C12',12,90,0),('C13',58,90,0)]:place(r,x,y,a)
wire('AVDD',(12,66),pin('L1',1));wire('AVDD',(12,66),pin('C12',1));lab('AVDD',(12,66))
wire('LX',pin('L1',2),(39,66),pin('D1',2));wire('LX',(39,66),pin('Q1',3));lab('LX',(39,66))
wire('GDRP',(16,78),pin('Q1',1));wire('GDRP',(24,78),pin('R2',1));lab('GDRP',(16,78))
link('RESEP',('Q1',2),('U1',1));lab('RESEP',(39,84))
wire('VDDP',pin('D1',1),(63,66));wire('VDDP',(58,66),pin('C13',1));lab('VDDP',(63,66),180)
wire('GND',(12,97),(58,97))
for r in ['C12','R2','U1','C13']:q=pin(r,2);wire('GND',q,(q[0],97))
gnd(12,97)

for title,off,q,u,l,d,ru,rg,rs,capin,capout,out in [('3  Negative source rail (VDDN)',0,'Q8','U2','L2','D2','R3','R5','R4','C14','C15','VDDN'),('4  VCOM supply branch',74,'Q7','U3','L3','D4','R13','R15','R14','C19','C20','VBB_3P5V')]:
 block(title,76+off,58,76 if off else 68,42)
 for r,x,y,a in [(q,99,78,180),(u,98,69,0),(l,98,89,0),(d,111,84,0),(ru,130,69,0),(rg,111,78,270),(rs,111,73,270),(capin,83,90,0),(capout,135,90,0)]:place(r,x+off,y,a)
 sense='SENSE_N' if not off else 'SENSE_VCOM';gate='GATE_N' if not off else 'GATE_VCOM';sw='SW_N' if not off else 'SW_VCOM';raw='VDDN_RAW' if not off else out
 wire('AVDD',(83+off,64),(130+off,64));wire('AVDD',(83+off,64),pin(capin,1));wire('AVDD',(98+off,64),pin(u,1));wire('AVDD',(130+off,64),pin(ru,1));lab('AVDD',(83+off,64))
 link(sense,(u,2),(q,2));wire(sense,(98+off,73),pin(rs,2));lab(sense,(98+off,73))
 res='RESEN' if not off else 'RESEC';wire(res,pin(rs,1),(120+off,73));lab(res,(120+off,73),180)
 wire(gate,pin(q,1),pin(rg,2));wire(gate,(103+off,78),(103+off,82),(130+off,82),pin(ru,2));lab(gate,(124+off,82))
 gd='GDRN' if not off else 'GDRC';wire(gd,pin(rg,1),(120+off,78));lab(gd,(120+off,78),180)
 link(sw,(q,3),(l,1));wire(sw,(98+off,84),pin(d,1));lab(sw,(98+off,84))
 if not off:
  place('R6',125,84,90);wire(raw,pin(d,2),pin('R6',1));lab(raw,(116,84));wire(out,pin('R6',2),(141,84))
 else:wire(out,pin(d,2),(141+off,84))
 wire(out,(135+off,84),pin(capout,1));lab(out,(141+off,84),180)
 wire('GND',(83+off,97),(135+off,97))
 for r in [capin,l,capout]:qxy=pin(r,2);wire('GND',qxy,(qxy[0],97))
 gnd(83+off,97)
# Mode-accepted zero-ohm connection, drawn once at the output of the VCOM branch.
place('R16',219,89,90);wire('VBB_3P5V',(215,84),(217.5,84),pin('R16',1));wire('VNCP_3P5V',pin('R16',2),(227,89));lab('VNCP_3P5V',(227,89),180)

block('5  Positive gate charge pump (VGH)',7,104,104,51)
for r,x,y,a in [('Q3',34,121,180),('Q4',47,134,0),('R11',48,113,0),('R12',48,143,0),('D3',67,127,0),('C16',73,143,0),('C17',76,133,90),('C18',33,143,0),('R7',82,146,180),('R8',82,138,180),('R9',89,127,90),('R10',89,133,90)]:place(r,x,y,a)
wire('VDDP',(33,110),(48,110),pin('R11',1));wire('VDDP',(33,110),pin('Q3',2));lab('VDDP',(33,110))
wire('BASE_P',pin('Q3',1),(48,121),pin('Q4',3));wire('BASE_P',pin('R11',2),(48,121));lab('BASE_P',(48,121))
wire('PUMP_P_LOW',pin('Q3',3),(33,127),pin('D3',1));wire('PUMP_P_LOW',(33,127),pin('C18',1));lab('PUMP_P_LOW',(43,127))
link('SOURCE_VGP',('Q4',2),('R12',1));lab('SOURCE_VGP',(48,138))
wire('DRVP',(39,134),pin('Q4',1));lab('DRVP',(39,134))
wire('PUMP_P_MID',pin('D3',3),(67,133),pin('C17',1));lab('PUMP_P_MID',(67,133))
link('PUMP_P_AC',('C17',2),('R10',1));lab('PUMP_P_AC',(80,133))
wire('LX',pin('R10',2),(105,133));lab('LX',(105,133),180)
link('VGH_RAW',('D3',2),('R9',1));wire('VGH_RAW',(73,127),pin('C16',1));wire('VGH_RAW',(82,127),pin('R8',2));lab('VGH_RAW',(73,127))
wire('VGH',pin('R9',2),(105,127));lab('VGH',(105,127),180)
link('FBP',('R8',1),('R7',2));wire('FBP',(82,142),(98,142));lab('FBP',(98,142),180)
wire('GND',(33,151),(82,151))
for r,n in [('C18',2),('R12',2),('C16',2),('R7',1)]:qxy=pin(r,n);wire('GND',qxy,(qxy[0],151))
gnd(33,151)

block('6  Negative gate charge pump (VGL)',117,104,107,51)
for r,x,y,a in [('Q6',182,134,0),('D5',141,119,0),('D6',141,134,0),('C21',122,128,0),('C22',151,143,0),('C23',161,123,90),('C24',161,138,90),('C25',138,146,0),('C26',195,143,0),('R17',128,138,0),('R18',128,146,0),('R19',182,123,90)]:place(r,x,y,a)
wire('VGL',(120,119),pin('D5',1));wire('VGL',(122,119),pin('C21',1));wire('VGL',(128,119),pin('R17',1));lab('VGL',(120,119))
wire('PUMP_N_MID',pin('D5',2),(151,119),(151,126),(135,126),(135,134),pin('D6',1));wire('PUMP_N_MID',(151,126),pin('C22',1));lab('PUMP_N_MID',(151,126))
wire('PUMP_N_UP',pin('D5',3),(141,123),pin('C23',1));lab('PUMP_N_UP',(145,123))
wire('PUMP_N_DOWN',pin('D6',3),(141,138),pin('C24',1));lab('PUMP_N_DOWN',(145,138))
wire('PUMP_N_AC',pin('C23',2),(169,123),pin('R19',1));wire('PUMP_N_AC',pin('C24',2),(169,138),(169,123));lab('PUMP_N_AC',(169,123))
wire('LX',pin('R19',2),(210,123));lab('LX',(210,123),180)
wire('PUMP_N_LOW',pin('D6',2),(173,134),(173,130),(195,130),pin('C26',1));wire('PUMP_N_LOW',(183,130),pin('Q6',3));lab('PUMP_N_LOW',(186,130))
wire('DRVN',pin('Q6',1),(177,134),(177,140));lab('DRVN',(177,140))
link('FBN',('R17',2),('R18',1));lab('FBN',(128,141))
wire('REG_VGN',pin('R18',2),(132,147.5),(132,141),(138,141),pin('C25',1));lab('REG_VGN',(138,141))
wire('GND',(122,151),(195,151))
for r,n in [('C21',2),('C22',2),('C25',2),('C26',2),('Q6',2)]:qxy=pin(r,n);wire('GND',qxy,(qxy[0],151))
gnd(195,151)

assert set(parts)==set(placed),('Unplaced',set(parts)-set(placed))
# Ground symbols are graphical power labels; retain local library dependency.
ground_symbol=standard('power','GND');ground_symbol[1]=Q('Driver:GND')
for c in kids(ground_symbol,'symbol'):c[1]=Q(str(c[1]).replace('GND','GND',1))
newlib['Driver:GND']=ground_symbol
path=one(one(one(parts['J1'],'instances'),'project'),'path')[1]
for i,xy in enumerate(ground):
 n=f'#PWRP{i+1:02}'
 nodes.append(obj(f'(symbol (lib_id "Driver:GND") (at {v2(xy)} 0) (unit 1) (in_bom no) (on_board yes) (dnp no) (uuid {dump(uid(n))}) (property "Reference" "{n}" (at {v2(xy)} 0) (effects (font (size 1 1)) (hide yes))) (property "Value" "GND" (at {v2((xy[0],xy[1]+2.5))} 0) (effects (font (size 1 1)))) (pin "1" (uuid {dump(uid(n+"pin"))})) (instances (project "gdep133c02-driver" (path {dump(path)} (reference "{n}") (unit 1)))))'))
# Split wires at actual connection endpoints/pins/labels, and make T junctions explicit.
allpoints={p for net,a,b in segments for p in [a,b]}|{xy for n,xy,a in labels}|set(ground)|{xy for r in placed for xy in placed[r].values()}
def contains(a,b,p):return abs((b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0]))<1e-7 and min(a[0],b[0])-1e-7<=p[0]<=max(a[0],b[0])+1e-7 and min(a[1],b[1])-1e-7<=p[1]<=max(a[1],b[1])+1e-7
outsegments=set()
for n,a,b in segments:
 ps=sorted([p for p in allpoints if contains(a,b,p)],key=lambda p:(p[0]-a[0])**2+(p[1]-a[1])**2)
 for p,q in zip(ps,ps[1:]):outsegments.add((n,*sorted([p,q])))
# A wire endpoint touching foreign copper in a schematic is a real connection.
pointnets={}
for n,a,b in outsegments:
 for p in [a,b]:pointnets.setdefault(p,set()).add(n)
assert all(len(ns)==1 for ns in pointnets.values()),[(p,ns) for p,ns in pointnets.items() if len(ns)>1]
data=json.loads((ROOT/'design-data.json').read_text());expected={p['ref']:p['pins'] for p in data['parts']}
for r in placed:
 if r.startswith('#'):continue
 for num,xy in placed[r].items():assert pointnets.get(xy)=={expected[r][num]},('pin wiring',r,num,xy,pointnets.get(xy),expected[r][num])
root=[x for x in old if not (isinstance(x,list) and x[0] in ['lib_symbols','symbol','wire','global_label','label','junction','no_connect','text','rectangle'])]
one(root,'paper')[1:]=[Q('User'),'594','450']
one(root,'title_block')[1:]=[['title',Q('Power - wired functional circuits')],['date',Q('2026-10-02')],['rev',Q('0.2-CAD-REVIEW')]]
root.append(['lib_symbols',*newlib.values()]);root.extend(tags)
for i,(n,a,b) in enumerate(sorted(outsegments)):
 root.append(obj(f'(wire (pts (xy {v2(a)}) (xy {v2(b)})) (stroke (width 0) (type default)) (uuid {dump(uid("wire"+str(i)))}))'))
for p in sorted(pointnets):
 count=sum(p in [a,b] for n,a,b in outsegments)
 if count>=3:root.append(obj(f'(junction (at {v2(p)}) (diameter 0) (color 0 0 0 0) (uuid {dump(uid("junction"+str(p)))}))'))
# Retain global names used by the already-routed PCB. Labels occur once per block net.
for i,(n,xy,a) in enumerate(labels):
 glob=True  # Preserve original global net names, including internal PCB networks.
 if glob:root.append(obj(f'(global_label {json.dumps(n)} (shape bidirectional) (at {v2(xy)} {a}) (effects (font (size .9 .9)) (justify {"right" if a==180 else "left"})) (uuid {dump(uid("label"+str(i)))}) (property "Intersheetrefs" "" (at {v2(xy)} 0) (effects (font (size .9 .9)) (hide yes))))'))
 else:root.append(obj(f'(label {json.dumps(n)} (at {v2(xy)} {a}) (effects (font (size .9 .9)) (justify left bottom)) (uuid {dump(uid("label"+str(i)))}))'))
root.append(obj(f'(text "Dots join wires; crossings without dots are not connected. Net labels retain the existing PCB net names." (at {v2((9,161))} 0) (effects (font (size 1.1 1.1)) (justify left)) (uuid {dump(uid("reading-note"))}))'))
root.extend(nodes)
(ROOT/'power.kicad_sch').write_text('(kicad_sch\n'+'\n'.join(dump(x) for x in root[1:])+'\n)\n')
# Match project-library graphics to embedded graphics for future editing.
lib=[x for x in lib if not (isinstance(x,list) and x[0]=='symbol' and ('Driver:'+str(x[1])) in newlib)]
for name,s in newlib.items():s=deepcopy(s);s[1]=Q(name.split(':',1)[1]);lib.append(s)
(ROOT/'lib/Driver.kicad_sym').write_text(dump(lib)+'\n')
(BASE/'layout-summary.json').write_text(json.dumps({'existing_symbols':len(parts),'new_ground_symbols':len(ground),'wire_segments':len(outsegments),'net_labels':len(labels),'source':'KiCad standard symbol geometry, project physical pin numbering retained'},indent=2)+'\n')
print(len(parts),'existing symbols,',len(outsegments),'wire segments; local geometry checks passed')
