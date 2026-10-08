#!/usr/bin/env python3
"""Generate project-local KiCad libraries, hierarchical schematic, and placed PCB.
All pad-net assignments are explicit and can be independently compared with the netlist.
Uses KiCad 10 Python API; no routes are invented by this generator.
"""
from pathlib import Path
import json,uuid,shutil,re,math,csv,sys
import pcbnew as pcb
ROOT=Path(__file__).resolve().parents[1]; DATA=json.loads((ROOT/'design-data.json').read_text());PARTS=DATA['parts'];NAME=DATA['name']
if (ROOT/'reports/check-provenance.json').exists():
    raise SystemExit('Historical initializer disabled: edit the repaired native KiCad project directly.')
K=Path('/Applications/KiCad/KiCad.app/Contents/SharedSupport')
Q=lambda x:json.dumps(str(x),ensure_ascii=False)
ID=lambda x:str(uuid.uuid5(uuid.NAMESPACE_URL,'album/gdep133c02-driver/'+x))
# Footprints used by this project are copied into a local library. 3D references
# are copied and rewritten as KIPRJMOD-relative paths where available.
fpnames={}
for part in PARTS:
 lib,name=part['fp'].split(':')
 if lib=='Driver':continue
 src=K/'footprints'/f'{lib}.pretty'/f'{name}.kicad_mod'
 assert src.exists(),src
 text=src.read_text(); local=lib+'__'+name; fpnames[part['fp']]=local
 text=text.replace('(footprint '+Q(name),'(footprint '+Q(local),1)
 def model(m):
  path=m.group(1).replace('${KICAD10_3DMODEL_DIR}',str(K/'3dmodels')).replace('${KICAD9_3DMODEL_DIR}',str(K/'3dmodels'))
  source=Path(path)
  if source.is_file():
   target=ROOT/'models'/source.name
   if not target.exists():shutil.copy2(source,target)
   return '(model '+Q('${KIPRJMOD}/models/'+source.name)
  return '(model '+Q(m.group(1))
 text=re.sub(r'\(model "([^"]+)"',model,text)
 # Remove unresolved optional models instead of retaining machine-global references.
 text=re.sub(r'\(model "\$\{KICAD[^"]+".*?\(rotate\s*\(xyz[^)]*\)\s*\)\s*\)', '', text, flags=re.S)
 (ROOT/'lib/Driver.pretty'/f'{local}.kicad_mod').write_text(text)
# FPC pads deliberately marked provisional until the exact manufacturer's drawing
# is accessible. This footprint must not be released to fabrication.
fpc='FPC_05FB_60PH20_UNVERIFIED'
s=[f'(footprint {Q(fpc)} (version 20260206) (generator "album") (layer "F.Cu")',
 '(descr "UNVERIFIED placeholder: exact Xunpu drawing required. DO NOT FABRICATE")',
 '(attr smd)', '(property "Reference" "FPC1" (at 0 4) (layer "F.SilkS") (effects (font (size 1 1) (thickness .15))))',
 '(property "Value" "DRAWING REQUIRED" (at 0 5.5) (layer "F.Fab") (effects (font (size 1 1))))']
for i in range(60):s.append(f'(pad "{i+1}" smd rect (at {(-14.75+i*.5):.3f} 2.5) (size .3 1.6) (layers "F.Cu" "F.Paste" "F.Mask"))')
for i,x in enumerate([-16.4,16.4],61):s.append(f'(pad "{i}" smd rect (at {x} 0) (size 2 2.4) (layers "F.Cu" "F.Paste" "F.Mask"))')
for layer,width,margin in [('F.Fab',.1,0),('F.CrtYd',.05,.5)]:s.append(f'(fp_rect (start {-17.5-margin} {-2-margin}) (end {17.5+margin} {3.6+margin}) (stroke (width {width}) (type solid)) (fill none) (layer "{layer}"))')
s.append(')');(ROOT/'lib/Driver.pretty'/f'{fpc}.kicad_mod').write_text('\n'.join(s))
(ROOT/'fp-lib-table').write_text('(fp_lib_table (version 7) (lib (name "Driver") (type "KiCad") (uri "${KIPRJMOD}/lib/Driver.pretty") (options "") (descr "Project-local footprints")))\n')
(ROOT/'sym-lib-table').write_text('(sym_lib_table (version 7) (lib (name "Driver") (type "KiCad") (uri "${KIPRJMOD}/lib/Driver.kicad_sym") (options "") (descr "Physical pin symbols")))\n')
# Custom symbols are physical-pin blocks with explicit names and electric types.
# Passive two-pin parts use resistor/capacitor/inductor glyphs; active blocks expose
# every physical pin, keeping package pin checks straightforward.
def symbol(p,name):
 pinlist=list(p['pins']); n=len(pinlist); rows=(n+1)//2 if n>2 else 1
 height=max(5.08,rows*2.54); width=10.16 if n<20 else 15.24
 out=[f'(symbol {Q(name)} (pin_names (offset .635)) (in_bom yes) (on_board yes)',f'(property "Reference" {Q(re.sub(r"[0-9]+$","",p["ref"]))} (at 0 {height/2+2.54} 0) (effects (font (size 1.27 1.27))))',f'(property "Value" {Q(p["value"])} (at 0 {-height/2-2.54} 0) (effects (font (size 1.27 1.27))))',f'(property "Footprint" {Q("Driver:"+fpnames.get(p["fp"],fpc))} (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))',f'(property "Datasheet" {Q(p["url"])} (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))',f'(symbol {Q(name+"_0_1")}']
 if n==2:
  if p['ref'].startswith('C'):
   out.extend(['(polyline (pts (xy -.635 -2.54) (xy -.635 2.54)) (stroke (width .3) (type default)) (fill (type none)))','(polyline (pts (xy .635 -2.54) (xy .635 2.54)) (stroke (width .3) (type default)) (fill (type none)))'])
  elif p['ref'].startswith(('R','L','U')):
   out.append('(rectangle (start -2.54 1.27) (end 2.54 -1.27) (stroke (width .254) (type default)) (fill (type none)))')
  else:out.append('(rectangle (start -2.54 2.54) (end 2.54 -2.54) (stroke (width .254) (type default)) (fill (type background)))')
 else:out.append(f'(rectangle (start {-width/2} {height/2}) (end {width/2} {-height/2}) (stroke (width .254) (type default)) (fill (type background)))')
 out.append(')');out.append(f'(symbol {Q(name+"_1_1")}')
 coords={}
 for i,num in enumerate(pinlist):
  if n==2:
   x=-5.08 if i==0 else 5.08;y=0;angle=0 if i==0 else 180;length=4.445 if p['ref'].startswith('C') else 2.54
  else:
   left=i<rows;row=i if left else i-rows;x=-(width/2+2.54) if left else width/2+2.54;y=(rows-1)*1.27-row*2.54;angle=0 if left else 180;length=2.54
  coords[num]=(x,-y)
  typ=p['types'].get(num,'passive');typ='power_out' if (p['ref']=='J1' and num=='2') or (p['ref']=='J2' and num=='16') else typ;pn=p['names'].get(num,num)
  out.append(f'(pin {typ} line (at {x} {y} {angle}) (length {length}) (name {Q(pn)} (effects (font (size .8 .8)))) (number {Q(num)} (effects (font (size .8 .8)))))')
 out.extend([')',')']);return '\n'.join(out),coords,height
symbols={};coords={};heights={}
for p in PARTS:
 name='P_'+p['ref'];symbols[p['ref']],coords[p['ref']],heights[p['ref']]=symbol(p,name)
(ROOT/'lib/Driver.kicad_sym').write_text('(kicad_symbol_lib (version 20250114) (generator "album")\n'+'\n'.join(symbols.values())+'\n)\n')
rootid=ID('schematic');sections=[('power','Power converters',[p for p in PARTS if p['group'] in ['entry','converters','pumps']]),('panel','Panel and temperature',[p for p in PARTS if p['group']=='panel']),('interface','Host isolation and test points',[p for p in PARTS if p['group'] in ['interface','test']])]
root=[f'(kicad_sch (version 20250114) (generator "eeschema") (uuid {rootid}) (paper "A4") (lib_symbols)', '(title_block (title "GDEP133C02 minimum driver - DRAFT") (date "2026-10-01") (rev "0.1") (company "album"))']
for page,(key,title,group) in enumerate(sections,2):
 sid=ID('sheet/'+key);childid=ID('schematic/'+key);filename=key+'.kicad_sch'
 x=35;y=35+(page-2)*35
 root.append(f'(sheet (at {x} {y}) (size 90 20) (stroke (width 0) (type default)) (fill (color 0 0 0 0)) (uuid {sid}) (property "Sheetname" {Q(title)} (at {x} {y-1} 0) (effects (font (size 1.27 1.27)) (justify left bottom))) (property "Sheetfile" {Q(filename)} (at {x} {y+21} 0) (effects (font (size 1.27 1.27)) (justify left top))) (instances (project {Q(NAME)} (path "/{rootid}" (page {Q(page)})))))')
 child=[f'(kicad_sch (version 20250114) (generator "eeschema") (uuid {childid}) (paper "A2") (title_block (title {Q(title)}) (rev "0.1-DRAFT")) (lib_symbols']
 for p in group:child.append(symbols[p['ref']].replace('(symbol "P_', '(symbol "Driver:P_',1))
 child.append(')')
 # FPC is tall and occupies the first column; other symbols are packed by column.
 ordered=sorted(group,key=lambda p:(0 if p['ref']=='FPC1' else 1, -len(p['pins']) if len(p['pins'])>2 else 0,p['ref']))
 col=0;cy=20
 for p in ordered:
  h=heights[p['ref']];span=max(h+15,20)
  if cy+span>375:col+=1;cy=20
  sx=round((35+col*72)/1.27)*1.27;sy=round((cy+h/2+5)/1.27)*1.27;cy+=span
  assert sx<560,(key,p['ref'],sx)
  ref=p['ref'];pid=p['uuid'];fp='Driver:'+fpnames.get(p['fp'],fpc)
  child.append(f'(symbol (lib_id {Q("Driver:P_"+ref)}) (at {sx} {sy} 0) (unit 1) (in_bom {"no" if p["group"]=="test" else "yes"}) (on_board yes) (dnp {"yes" if p["dnp"] else "no"}) (uuid {pid})')
  for k,v,px,py,hidden in [('Reference',ref,sx,sy-h/2-2.5,False),('Value',p['value'],sx,sy+h/2+2.5,False),('Footprint',fp,sx,sy,True),('Datasheet',p['url'],sx,sy,True),('MPN',p['mpn'],sx,sy,True),('Manufacturer',p['vendor'],sx,sy,True)]:child.append(f'(property {Q(k)} {Q(v)} (at {px} {py} 0) (effects (font (size .9 .9)){" (hide yes)" if hidden else ""}))')
  for num in p['pins']:child.append(f'(pin {Q(num)} (uuid {ID(ref+"/pin/"+num)}))')
  child.append(f'(instances (project {Q(NAME)} (path "/{rootid}/{sid}" (reference {Q(ref)}) (unit 1)))) )')
  for num,net in p['pins'].items():
   dx,dy=coords[ref][num];px=sx+dx;py=sy+dy
   if net is None:child.append(f'(no_connect (at {px} {py}) (uuid {ID(ref+"/nc/"+num)}))');continue
   end=px+(-5.08 if dx<0 else 5.08)
   child.append(f'(wire (pts (xy {px} {py}) (xy {end} {py})) (stroke (width 0) (type default)) (uuid {ID(ref+"/wire/"+num)}))')
   child.append(f'(global_label {Q(net)} (shape bidirectional) (at {end} {py} {0 if dx<0 else 180}) (effects (font (size .75 .75)) (justify {"left" if dx<0 else "right"})) (uuid {ID(ref+"/label/"+num)}) (property "Intersheetrefs" "${{INTERSHEET_REFS}}" (at {end} {py} 0) (effects (font (size .75 .75)) (hide yes))))')
 if key=='power':
  flag='(symbol "Driver:SupplyFlag" (power) (in_bom no) (on_board no) (property "Reference" "#FLG" (at 0 0 0) (effects (font (size 1 1)) (hide yes))) (property "Value" "PWR_FLAG" (at 0 2.54 0) (effects (font (size 1 1)))) (symbol "SupplyFlag_1_1" (pin power_out line (at 0 0 90) (length 0) (name "pwr" (effects (font (size 1 1)))) (number "1" (effects (font (size 1 1)))))))'
  libpath=ROOT/'lib/Driver.kicad_sym';libtext=libpath.read_text();libpath.write_text(libtext.rsplit(')',1)[0]+flag.replace('Driver:SupplyFlag','SupplyFlag')+'\n)\n');child[1:1]=[flag]  # inside lib_symbols opened in child[0]
  for fi,net in enumerate(['SW_IN','EPD_3V3']):
   fx=500.38;fy=round((340+fi*12.7)/1.27)*1.27;fid=ID('flag/'+net)
   child.append(f'(symbol (lib_id "Driver:SupplyFlag") (at {fx} {fy} 0) (unit 1) (in_bom no) (on_board no) (uuid {fid}) (property "Reference" "#FLG{fi+1:02}" (at {fx} {fy} 0) (effects (font (size 1 1)) (hide yes))) (property "Value" "PWR_FLAG" (at {fx} {fy-2.54} 0) (effects (font (size 1 1)))) (pin "1" (uuid {ID("flagpin/"+net)})) (instances (project {Q(NAME)} (path "/{rootid}/{sid}" (reference "#FLG{fi+1:02}") (unit 1)))))')
   child.append(f'(global_label {Q(net)} (shape bidirectional) (at {fx} {fy} 0) (effects (font (size 1 1)) (justify left)) (uuid {ID("flaglabel/"+net)}) (property "Intersheetrefs" "" (at {fx} {fy} 0) (effects (font (size 1 1)) (hide yes))))')
 child.append(')');(ROOT/filename).write_text('\n'.join(child)+'\n')
root.append(')');(ROOT/(NAME+'.kicad_sch')).write_text('\n'.join(root)+'\n')
# Minimal project with explicit manufacturing limits, no disabled checker classes.
pro={'meta':{'filename':NAME+'.kicad_pro','version':3},'board':{'design_settings':{'defaults':{'board_outline_line_width':.05},'rules':{'min_clearance':.2,'min_track_width':.2,'min_via_diameter':.7,'min_through_hole_diameter':.3,'min_via_annular_width':.2,'min_copper_edge_clearance':.3,'min_silk_clearance':.15,'min_silk_text_height':1.0,'min_silk_text_thickness':.15}}},'net_settings':{'meta':{'version':4},'classes':[{'name':'Default','clearance':.2,'track_width':.2,'via_diameter':.7,'via_drill':.3}]},'schematic':{'meta':{'version':1}}}
base=json.loads((K/'template/kicad.kicad_pro').read_text());base['meta']['filename']=NAME+'.kicad_pro';base['board']['design_settings']['rules'].update(pro['board']['design_settings']['rules']);(ROOT/(NAME+'.kicad_pro')).write_text(json.dumps(base,indent=2)+'\n')
# Physical board coordinates use the lower-left source-plan convention translated
# into KiCad's standard top-left XY; drawing is at (50,50) mm.
b=pcb.BOARD();b.SetCopperLayerCount(4);ds=b.GetDesignSettings();ds.m_MinClearance=pcb.FromMM(.2);ds.m_TrackMinWidth=pcb.FromMM(.2);ds.m_CopperEdgeClearance=pcb.FromMM(.3)
allnets=sorted({v for p in PARTS for v in p['pins'].values() if v});nm={}
for i,name in enumerate(allnets,1):n=pcb.NETINFO_ITEM(b,name,i);b.Add(n);nm[name]=n
origin=(50,50)
for p in PARTS:
 local=fpnames.get(p['fp'],fpc);f=pcb.FootprintLoad(str(ROOT/'lib/Driver.pretty'),local);assert f,local
 f.SetFPID(pcb.LIB_ID('Driver',local));f.SetReference(p['ref']);f.SetValue(p['value']);f.SetUuid(pcb.KIID(p['uuid']));f.SetPath(pcb.KIID_PATH('/'+ID('sheet/'+next(k for k,t,g in sections if p in g))+'/'+p['uuid']))
 f.SetPosition(pcb.VECTOR2I(pcb.FromMM(p['xy'][0]+50),pcb.FromMM(p['xy'][1]+50)));f.SetOrientationDegrees(p['angle']);f.Value().SetVisible(False)
 f.Reference().SetTextSize(pcb.VECTOR2I(pcb.FromMM(1),pcb.FromMM(1)));f.Reference().SetTextThickness(pcb.FromMM(.15))
 for pad in f.Pads():
  num=pad.GetNumber();net=p['pins'].get(num)
  if net:pad.SetNet(nm[net])
 b.Add(f)
for i,(x,y) in enumerate([(5,5),(95,5),(5,75),(95,75)],1):
 f=pcb.FootprintLoad(str(K/'footprints/MountingHole.pretty'),'MountingHole_3.2mm_M3');f.SetReference('H'+str(i));f.SetPosition(pcb.VECTOR2I(pcb.FromMM(x+50),pcb.FromMM(y+50)));f.Reference().SetVisible(False);f.Value().SetVisible(False);b.Add(f)
for start,end in [((50,50),(150,50)),((150,50),(150,130)),((150,130),(50,130)),((50,130),(50,50))]:
 sh=pcb.PCB_SHAPE();sh.SetShape(pcb.SHAPE_T_SEGMENT);sh.SetStart(pcb.VECTOR2I(*[pcb.FromMM(v) for v in start]));sh.SetEnd(pcb.VECTOR2I(*[pcb.FromMM(v) for v in end]));sh.SetLayer(pcb.Edge_Cuts);sh.SetWidth(pcb.FromMM(.05));b.Add(sh)
for text,xy,size in [('GDEP133C02 DRIVER 0.1 DRAFT',(50,3),1.2),('FPC FOOTPRINT NOT VERIFIED',(50,9),1),('3.3V ONLY - NO 5V',(25,76),1),('POWER OFF BEFORE FPC',(25,72),1)]:
 t=pcb.PCB_TEXT(b);t.SetText(text);t.SetPosition(pcb.VECTOR2I(*[pcb.FromMM(x+50) for x in xy]));t.SetTextSize(pcb.VECTOR2I(pcb.FromMM(size),pcb.FromMM(size)));t.SetTextThickness(pcb.FromMM(.15));t.SetLayer(pcb.F_SilkS);b.Add(t)
pcb.SaveBoard(str(ROOT/(NAME+'.kicad_pcb')),b)
# Routing input is generated from actual pad geometry, not guessed pin coordinates.
pads=[]
for f in b.GetFootprints():
 for p in f.Pads():
  pos=p.GetPosition();size=p.GetSize();ang=p.GetOrientationDegrees();sx=pcb.ToMM(size.x);sy=pcb.ToMM(size.y)
  if round(ang)%180==90:sx,sy=sy,sx
  pads.append({'ref':f.GetReference(),'pin':p.GetNumber(),'net':p.GetNetCode(),'netname':p.GetNetname(),'x':pcb.ToMM(pos.x)-50,'y':pcb.ToMM(pos.y)-50,'sx':sx,'sy':sy,'tht':p.GetAttribute() in [pcb.PAD_ATTRIB_PTH,pcb.PAD_ATTRIB_NPTH],'npth':p.GetAttribute()==pcb.PAD_ATTRIB_NPTH})
(ROOT/'reports/pads.json').write_text(json.dumps(pads,indent=2)+'\n')
print('Generated native hierarchical schematic and placed PCB;',len(pads),'pads;',len(allnets),'nets')
