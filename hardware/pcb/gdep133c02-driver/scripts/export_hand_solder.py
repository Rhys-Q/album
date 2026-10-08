#!/usr/bin/env python3
"""Check and export v0.5 review artifacts; no hardware or production sign-off.
Run with KiCad 10.0.6 bundled Python; native API zone fill avoids macOS CLI refill bug.
Refuses to overwrite an existing versioned release.
"""
from pathlib import Path
import subprocess,json,csv,hashlib,zipfile
import pcbnew as p
R=Path(__file__).resolve().parents[1];CLI='/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli';NAME='gdep133c02-driver';BOARD=R/(NAME+'.kicad_pcb');SCH=R/(NAME+'.kicad_sch');OUT=R/'releases/jlc-cn-review-v0.5-linkfix-2026-10-08'
assert not OUT.exists(),'Existing review version must not be overwritten'
def run(*args):subprocess.run([CLI,*map(str,args)],check=True)
def digest(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def write(f,cols,rows):
 with f.open('w',newline='') as out:
  w=csv.DictWriter(out,fieldnames=cols);w.writeheader();w.writerows(rows)
b=p.LoadBoard(str(BOARD));b.BuildConnectivity();assert p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(BOARD),b)
run('sch','erc',SCH,'--format','json','-o',R/'reports/erc.json','--exit-code-violations')
run('sch','export','netlist',SCH,'--format','kicadxml','-o',R/'reports/netlist.xml')
run('pcb','drc',BOARD,'--schematic-parity','--format','json','-o',R/'reports/drc.json','--exit-code-violations')
run('sch','export','pdf',SCH,'-o',R/'reports/schematic.pdf')
pads=[]
for f in b.GetFootprints():
 for pad in f.Pads():
  q=pad.GetPosition();sz=pad.GetSize();pads.append(dict(ref=f.GetReference(),pin=pad.GetNumber(),net=pad.GetNetCode(),netname=pad.GetNetname(),x=p.ToMM(q.x)-50,y=p.ToMM(q.y)-50,sx=p.ToMM(sz.x),sy=p.ToMM(sz.y),tht=pad.GetAttribute() in [p.PAD_ATTRIB_PTH,p.PAD_ATTRIB_NPTH],npth=pad.GetAttribute()==p.PAD_ATTRIB_NPTH))
(R/'reports/pads.json').write_text(json.dumps(pads,indent=2)+'\n')
tracks=list(b.GetTracks())
summary=dict(revision='0.5-GDRC-DEBUG',footprints=len(list(b.GetFootprints())),pads=len(pads),tracks=sum(not isinstance(t,p.PCB_VIA) for t in tracks),vias=sum(isinstance(t,p.PCB_VIA) for t in tracks),minimum_track_mm=min(p.ToMM(t.GetWidth()) for t in tracks if not isinstance(t,p.PCB_VIA)),missing_3d_models=[f.GetReference() for f in b.GetFootprints() if not len(f.Models())])
(R/'reports/board-summary.json').write_text(json.dumps(summary,indent=2)+'\n')

source=[f for f in R.iterdir() if f.suffix in ['.kicad_sch','.kicad_pro','.kicad_pcb','.kicad_dru']]+[R/'design-data.json',R/'lib/Driver.kicad_sym']+list((R/'lib/Driver.pretty').glob('*.kicad_mod'))
proof=dict(date='2026-10-08',kicad_version='10.0.6',gui_open=json.loads((R/'reports/gui-open.json').read_text())['status'],zone_refill='PASS - native pcbnew ZONE_FILLER.Fill returned true; saved source checked by unmodified CLI',scope='v0.5 native CAD, full ERC/DRC/parity, pad map, supply and direct signal fixed requirements',source_sha256={str(f.relative_to(R)):digest(f) for f in source})
(R/'reports/check-provenance.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n')
subprocess.run(['python3',str(R/'scripts/check_design.py')],check=True)
OUT.mkdir();(OUT/'gerber').mkdir();(OUT/'stencil-optional').mkdir();(R/'reports/preview').mkdir(exist_ok=True)
run('pcb','export','gerbers',BOARD,'-l','F.Cu,In1.Cu,In2.Cu,B.Cu,F.Mask,B.Mask,F.Silkscreen,B.Silkscreen,Edge.Cuts','--no-x2','--no-netlist','-o',OUT/'gerber')
run('pcb','export','drill',BOARD,'--excellon-separate-th','--generate-map','--generate-report','-o',OUT/'gerber')
run('pcb','export','gerbers',BOARD,'-l','F.Paste','--no-x2','--no-netlist','-o',OUT/'stencil-optional')
run('pcb','export','pos',BOARD,'--format','csv','--units','mm','--smd-only','--exclude-dnp','-o',OUT/'positions-kicad.csv')
for label,layers in [('top','F.Cu,F.Silkscreen,Edge.Cuts'),('ground','In1.Cu,Edge.Cuts'),('bottom','B.Cu,B.Silkscreen,Edge.Cuts')]:
 run('pcb','export','svg',BOARD,'--mode-single','--fit-page-to-board','--exclude-drawing-sheet','-l',layers,'-o',R/f'reports/preview/{label}.svg')
with (OUT/'positions-kicad.csv').open(newline='') as f:positions=list(csv.DictReader(f))
refs={r['Ref'] for r in positions};assert len(refs)==len(positions)==101;assert all(r['Side']=='top' for r in positions)
cpl=[{'Designator':r['Ref'],'Mid X':r['PosX'],'Mid Y':r['PosY'],'Layer':'T','Rotation':r['Rot']} for r in positions]
write(OUT/(NAME+'-cpl-smt.csv'),['Designator','Mid X','Mid Y','Layer','Rotation'],cpl)
data=json.loads((R/'design-data.json').read_text());groups={}
for z in data['parts']:
 if z['dnp']:continue
 key=(z['value'],z['fp'],z['vendor'],z['mpn']);groups.setdefault(key,[]).append(z['ref'])
cols=['Comment','Designator','Footprint','Quantity','Manufacturer','MPN'];allbom=[];smt=[];manual=[]
fpnames={'FPC_05FB_60PH20':'FPC 60P 0.5mm','Inductor_SMD:L_Coilcraft_MSS1246T-XXX':'MSS1246'}
for (v,fp,vendor,mpn),rr in sorted(groups.items()):
 short=fpnames.get(fp, '0805' if '0805_' in fp else '0603' if '0603_' in fp else '1206' if '1206_' in fp else '1210' if '1210_' in fp else 'SOT-23-6' if 'SOT-23-6' in fp else 'SOT-323' if 'SOT-323' in fp else 'SOT-23' if 'SOT-23' in fp else 'SOD-123F' if 'SOD-123F' in fp else 'SOD-123' if 'SOD-123' in fp else 'SOIC-8' if 'SOIC-8' in fp else 'PinHeader 1x02 2.54mm' if '1x02' in fp else 'PinHeader 2x08 2.54mm' if '2x08' in fp else fp)
 row=dict(Comment=v+' '+mpn,Designator=','.join(sorted(rr)),Footprint=short,Quantity=len(rr),Manufacturer=vendor,MPN=mpn);allbom.append(row)
 assert all(ref in refs for ref in rr) or not any(ref in refs for ref in rr)
 (smt if rr[0] in refs else manual).append(row)
assert sum(r['Quantity'] for r in allbom)==103
assert {ref for row in smt for ref in row['Designator'].split(',')}==refs
assert {ref for row in manual for ref in row['Designator'].split(',')}=={'J1','J2'}
for suffix,rows in [('bom-all',allbom),('bom-smt',smt),('bom-manual',manual)]:write(OUT/(NAME+'-'+suffix+'.csv'),cols,rows)
files=[f for f in (OUT/'gerber').iterdir() if f.suffix in ['.gtl','.gbl','.g1','.g2','.gts','.gbs','.gto','.gbo','.gm1','.drl']];assert len(files)==11
with zipfile.ZipFile(OUT/(NAME+'-gerber-rs274x.zip'),'w',zipfile.ZIP_DEFLATED) as z:
 for f in sorted(files):z.write(f,f.name)
assert all(digest(R/name)==value for name,value in proof['source_sha256'].items()),'Source mutation during export'
report=dict(date='2026-10-08',revision='0.5-GDRC-DEBUG',kicad_version='10.0.6',production_released=False,source_sha256=proof['source_sha256'],assembled_components=103,smt_components=101,smt_bom_groups=len(smt),cpl_components=101,manual_components=['J1','J2'],all_smt_on_top=True,erc_violations=0,drc_violations=0,unconnected_items=0,schematic_parity=0,gui_open=proof['gui_open'],zone_refill=proof['zone_refill'],jlc_part_numbers='NOT MATCHED',hardware_tests='NOT PERFORMED',files_sha256={str(f.relative_to(OUT)):digest(f) for f in sorted(OUT.rglob('*')) if f.is_file()})
(OUT/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'output':str(OUT),'assembled':103,'smt':101,'smt_groups':len(smt),'CAD_checks':'PASS','production_released':False},ensure_ascii=False))
