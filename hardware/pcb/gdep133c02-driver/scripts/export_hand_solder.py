#!/usr/bin/env python3
"""Check and export v0.11 review artifacts; no hardware or production sign-off.
Run with KiCad 10.0.6 bundled Python; native API zone fill avoids macOS CLI refill bug.
Refuses to overwrite an existing versioned release.
"""
from pathlib import Path
import subprocess,json,csv,hashlib,zipfile,argparse,shutil
import wx
app=wx.App(False)
import pcbnew as p
R=Path(__file__).resolve().parents[1];CLI='/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli';NAME='gdep133c02-driver';BOARD=R/(NAME+'.kicad_pcb');SCH=R/(NAME+'.kicad_sch');OUT=R/'releases/jlc-cn-review-v0.11-basic17-2026-10-11'
args=argparse.ArgumentParser();args.add_argument('--draft',action='store_true',help='Export staging artifacts while GUI acceptance is pending');options=args.parse_args()
if options.draft:OUT=R/'reports/staging-v0.11-basic17-2026-10-11'
data=json.loads((R/'design-data.json').read_text())
assert not OUT.exists(),'Existing review version must not be overwritten'
assembly_plan=json.loads((R/'assembly-plan.json').read_text())
manual_refs=set(assembly_plan['manual_smd_refs']+assembly_plan['manual_tht_refs'])
def run(*args):subprocess.run([CLI,*map(str,args)],check=True)
def digest(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def write(f,cols,rows):
 with f.open('w',newline='') as out:
  w=csv.DictWriter(out,fieldnames=cols,lineterminator="\n");w.writeheader();w.writerows(rows)
b=p.LoadBoard(str(BOARD));b.BuildConnectivity();assert p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(BOARD),b)
gui=json.loads((R/'reports/gui-open.json').read_text())
if not options.draft:
 assert gui['status'].startswith('PASS') and gui['date']==data['date'] and gui.get('new_footprints')==0,'Current GUI update preview acceptance required before release'
 assert all(digest(R/name)==value for name,value in gui['source_sha256'].items()),'CAD changed since native GUI acceptance'
 preview=(R/gui['update_preview']).read_text()
 assert all(line.startswith(('信息:','警告:')) for line in preview.splitlines() if line.strip()),'Native update preview still contains actions'
 assert '总计警告: 2, 错误: 0' in preview,'Unexpected GUI update warnings/errors'
run('sch','erc',SCH,'--format','json','-o',R/'reports/erc.json','--exit-code-violations')
run('sch','export','netlist',SCH,'--format','kicadxml','-o',R/'reports/netlist.xml')
run('pcb','drc',BOARD,'--schematic-parity','--format','json','-o',R/'reports/drc.json','--exit-code-violations')
run('sch','export','pdf',SCH,'-o',R/'reports/schematic.pdf')
pads=[]
for f in b.GetFootprints():
 for pad in f.Pads():
  q=pad.GetPosition();sz=pad.GetSize();pads.append(dict(ref=f.GetReference(),pin=pad.GetNumber(),net=pad.GetNetCode(),netname=pad.GetNetname(),x=p.ToMM(q.x)-50,y=p.ToMM(q.y)-50,sx=p.ToMM(sz.x),sy=p.ToMM(sz.y),tht=pad.GetAttribute() in [p.PAD_ATTRIB_PTH,p.PAD_ATTRIB_NPTH],npth=pad.GetAttribute()==p.PAD_ATTRIB_NPTH))
(R/'reports/pads.json').write_text(json.dumps(pads,indent=2)+'\n')
assert b.GetCopperLayerCount()==4
bb=b.GetBoardEdgesBoundingBox()
assert abs(p.ToMM(bb.GetWidth())-100)<.1 and abs(p.ToMM(bb.GetHeight())-80)<.1
tracks=list(b.GetTracks())
summary=dict(revision=data['revision'],footprints=len(list(b.GetFootprints())),pads=len(pads),tracks=sum(not isinstance(t,p.PCB_VIA) for t in tracks),vias=sum(isinstance(t,p.PCB_VIA) for t in tracks),minimum_track_mm=min(p.ToMM(t.GetWidth()) for t in tracks if not isinstance(t,p.PCB_VIA)),missing_3d_models=[f.GetReference() for f in b.GetFootprints() if not len(f.Models())])
(R/'reports/board-summary.json').write_text(json.dumps(summary,indent=2)+'\n')

source=[f for f in R.iterdir() if f.suffix in ['.kicad_sch','.kicad_pro','.kicad_pcb','.kicad_dru']]+[R/'design-data.json',R/'assembly-plan.json',R/'lib/Driver.kicad_sym']+list((R/'lib/Driver.pretty').glob('*.kicad_mod'))+list((R/'models').rglob('*.step'))+list((R/'scripts').glob('*.py'))+[R/'docs/采购清单-v0.10.csv',R/'docs/例外决定-v0.9.csv',R/'reports/basic-library-recheck-2026-10-11/products.json',R/'reports/basic-library-recheck-2026-10-11/group-review.json']+[R/'reports/baseline-design-v010.json',R/'reports/stock-refresh-v011.json',R/'reports/silkscreen-labels-v011.json',R/'reports/gui-observation-v011.md']+[R/'fp-lib-table',R/'sym-lib-table',R/'reports/procurement-v011.json',R/'reports/cost-change-geometry-v011.json',R/'reports/update-preview-first-v011.txt',R/'reports/update-preview-v011.txt',R/'reports/gui-open.json',R/'reports/update-preview.txt',R/'README.md']+list((R/'docs/sources').rglob('*.pdf'))+list((R/'docs').glob('*v0.11*'))+list((R/'docs').glob('*.md'))
proof=dict(date=data['date'],kicad_version='10.0.6',gui_open=json.loads((R/'reports/gui-open.json').read_text())['status'],zone_refill='PASS - native pcbnew ZONE_FILLER.Fill returned true; saved source checked by unmodified CLI',scope='v0.11 17 user-selected basic-library prototype groups; 147 assembled, 145 physical SMD, 138 machine SMT and 9 manual; 14 groups electrical equivalence unverified; native CAD/full ERC/DRC/parity/pad map/link checks',source_sha256={str(f.relative_to(R)):digest(f) for f in source})
(R/'reports/check-provenance.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n')
subprocess.run(['python3',str(R/'scripts/check_design.py')],check=True)
OUT.mkdir();(OUT/'gerber').mkdir();(OUT/'stencil-optional').mkdir();(R/'reports/preview').mkdir(exist_ok=True)
run('pcb','export','gerbers',BOARD,'-l','F.Cu,In1.Cu,In2.Cu,B.Cu,F.Mask,B.Mask,F.Silkscreen,B.Silkscreen,Edge.Cuts','--no-x2','--no-netlist','-o',OUT/'gerber')
run('pcb','export','drill',BOARD,'--excellon-separate-th','--generate-map','--generate-report','-o',OUT/'gerber')
run('pcb','export','gerbers',BOARD,'-l','F.Paste','--no-x2','--no-netlist','-o',OUT/'stencil-optional')
run('pcb','export','pos',BOARD,'--format','csv','--units','mm','--smd-only','--exclude-dnp','-o',OUT/'positions-kicad.csv')
for label,layers in [('top','F.Cu,F.Silkscreen,Edge.Cuts'),('ground','In1.Cu,Edge.Cuts'),('bottom','B.Cu,B.Silkscreen,Edge.Cuts')]:
 run('pcb','export','svg',BOARD,'--mode-single','--fit-page-to-board','--exclude-drawing-sheet','-l',layers,'-o',R/f'reports/preview/{label}.svg')
# Normalize native SVG whitespace without changing rendered geometry.
for preview in (R/'reports/preview').glob('*.svg'):
 preview.write_text('\n'.join(line.rstrip() for line in preview.read_text().splitlines())+'\n')
with (OUT/'positions-kicad.csv').open(newline='') as f:positions=list(csv.DictReader(f))
# Native position export retains physical SMDs; assembly-plan determines machine placement.
assert len(positions)==data['smt_components']
positions=[row for row in positions if row['Ref'] not in manual_refs]
machine_count=data['smt_components']-len(assembly_plan['manual_smd_refs'])
refs={r['Ref'] for r in positions};assert len(refs)==len(positions)==machine_count;assert all(r['Side']=='top' for r in positions)
footprints={f.GetReference():f for f in b.GetFootprints()}
for row in positions:
 fp=footprints[row['Ref']];q=fp.GetPosition()
 assert abs(float(row['PosX'])-p.ToMM(q.x))<1e-5 and abs(float(row['PosY'])+p.ToMM(q.y))<1e-5,('CPL coordinate mismatch',row['Ref'])
 assert abs(float(row['Rot'])-fp.GetOrientationDegrees())<1e-5,('CPL rotation mismatch',row['Ref'])
 assert row['Val']==fp.GetValue() and row['Package']==fp.GetFPID().GetLibItemName(),('CPL footprint/value mismatch',row['Ref'])
cpl=[{'Designator':r['Ref'],'Mid X':r['PosX'],'Mid Y':r['PosY'],'Layer':'T','Rotation':r['Rot']} for r in positions]
write(OUT/(NAME+'-cpl-smt.csv'),['Designator','Mid X','Mid Y','Layer','Rotation'],cpl)
data=json.loads((R/'design-data.json').read_text());groups={}
for z in data['parts']:
 if z['dnp']:continue
 key=(z['value'],z['fp'],z['vendor'],z['mpn']);groups.setdefault(key,[]).append(z['ref'])
cols=['Comment','Designator','Footprint','Quantity','Manufacturer','MPN','LCSC Part #'];allbom=[];smt=[];manual=[]
fpnames={'FPC_05FB_60PH20':'FPC 60P 0.5mm','Inductor_SMD:L_Coilcraft_MSS1246T-XXX':'MSS1246'}
for (v,fp,vendor,mpn),rr in sorted(groups.items()):
 short=fpnames.get(fp, 'FPC 60P 0.5mm' if 'FPC_05FB_60PH20' in fp else 'PCR1040 11.5x10.5mm' if 'L_JIERR_PCR1040' in fp else 'MSS1246 12x12mm' if 'MSS1246' in fp else '0805' if '0805_' in fp else '0603' if '0603_' in fp else '1206' if '1206_' in fp else '1210' if '1210_' in fp else 'SOT-23-6' if 'SOT-23-6' in fp else 'SOT-323' if 'SOT-323' in fp or 'SOT323' in fp else 'SOT-23' if 'SOT-23' in fp else 'SMA' if 'SMA_' in fp else 'SOD-123F' if 'SOD-123F' in fp else 'SOD-123' if 'SOD-123' in fp else 'SOIC-8' if 'SOIC-8' in fp else 'PinHeader 1x02 2.54mm' if '1x02' in fp else 'PinHeader 2x08 2.54mm' if '2x08' in fp else fp)
 row=dict(Comment=v+' '+mpn,Designator=','.join(sorted(rr)),Footprint=short,Quantity=len(rr),Manufacturer=vendor,MPN=mpn); codes={z['lcsc'] for z in data['parts'] if z['ref'] in rr};assert len(codes)==1 and next(iter(codes)).startswith('C');row['LCSC Part #']=next(iter(codes));allbom.append(row)
 assert all(ref in refs for ref in rr) or not any(ref in refs for ref in rr)
 (smt if rr[0] in refs else manual).append(row)
assert sum(r['Quantity'] for r in allbom)==data['assembled_components']
assert {ref for row in smt for ref in row['Designator'].split(',')}==refs
assert {ref for row in manual for ref in row['Designator'].split(',')}==manual_refs
for suffix,rows in [('bom-all',allbom),('bom-smt',smt),('bom-manual',manual)]:write(OUT/(NAME+'-'+suffix+'.csv'),cols,rows)
files=[f for f in (OUT/'gerber').iterdir() if f.suffix in ['.gtl','.gbl','.g1','.g2','.gts','.gbs','.gto','.gbo','.gm1','.drl']];assert len(files)==11
with zipfile.ZipFile(OUT/(NAME+'-gerber-rs274x-latest.zip'),'w',zipfile.ZIP_DEFLATED) as z:
 for f in sorted(files):z.write(f,f.name)
run('pcb','export','pdf',BOARD,'-l','F.Cu,F.Silkscreen,Edge.Cuts','-o',R/'reports/preview/board.pdf')
run('pcb','export','pdf',BOARD,'-l','F.Fab,F.Silkscreen,Edge.Cuts','-o',OUT/'assembly-top.pdf')
for name in ['gui-open.json','erc.json','drc.json','validation-status.json','cost-change-geometry-v011.json','silkscreen-labels-v011.json','gui-observation-v011.md']:
 shutil.copy2(R/'reports'/name,OUT/name)
shutil.copy2(R/'reports/schematic.pdf',OUT/'schematic-v0.11.pdf')
shutil.copy2(R/'reports/preview/board.pdf',OUT/'pcb-v0.11.pdf')
for filename in ['采购清单-v0.11.csv','逐位号替换对照-v0.11.csv','基础库17组改版-v0.11.md','手焊说明-v0.11.md','17组决定及剩余例外-v0.11.csv']:shutil.copy2(R/'docs'/filename,OUT/filename)
(OUT/'README.md').write_text('# v0.11 17组基础库原型制造审阅包\n\n147个装配件，145个顶面SMD；其中138个机器贴片、9个手工装配，36组完整BOM。BOM/CPL/制造文件来源见verification.json。'+('\n\n暂存包：GUI验收尚未通过。' if options.draft else '\n\nCAD及原生KiCad更新预览已通过；电气实板性能尚未验收。')+'\n\nGerber压缩包含四层铜、双面阻焊/丝印、板框及PTH/NPTH钻孔。基础库17组由用户指定采用；3组参数审核通过，14组等效性能未验证。组合新增43件，不承诺订单总价节省。C15008 SMT库存未知，部分公开库存刷新未成功；订单重核。剩余7组保留原型号；E02/E07/E16/E23/E25由用户淘宝采购手焊，U4/U5/Q3/D3/D5/D6/FPC1不进入机器BOM/CPL；J1/J2手工插件。装配分配以assembly-plan.json为准，positions-kicad.csv为包含全部145个SMD的原生坐标，仅cpl-smt.csv用于机器贴片。\n\n新增密集区部分位号仅在F.Fab，装配时结合assembly-top.pdf与BOM。Q7保留R49；低栅压驱动、瞬态、偏压容量、温升、显示和安全掉电需焊后验收。\n')
assert all(digest(R/name)==value for name,value in proof['source_sha256'].items()),'Source mutation during export'
report=dict(date=data['date'],revision=data['revision'],kicad_version='10.0.6',production_released=False,source_sha256=proof['source_sha256'],assembled_components=data['assembled_components'],smt_components=machine_count,physical_smd_components=data['smt_components'],smt_bom_groups=len(smt),cpl_components=machine_count,manual_components=sorted(manual_refs),all_smt_on_top=True,erc_violations=0,drc_violations=0,unconnected_items=0,schematic_parity=0,gui_open=proof['gui_open'],zone_refill=proof['zone_refill'],jlc_part_numbers='COMPLETE codes; domestic SMT supply PARTIAL: C15008 SMT stock unknown; partial refresh failures and electrical equivalence gaps documented' ,hardware_tests='NOT PERFORMED',files_sha256={str(f.relative_to(OUT)):digest(f) for f in sorted(OUT.rglob('*')) if f.is_file()})
(OUT/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'output':str(OUT),'assembled':data['assembled_components'],'smt':machine_count,'smt_groups':len(smt),'CAD_checks':'PASS','production_released':False},ensure_ascii=False))
