#!/usr/bin/env python3
"""Refresh checked CAD review files, never grant manufacturing release.

Run with KiCad's bundled Python. Native source files are authoritative.
"""
from pathlib import Path
import subprocess, json, csv, hashlib, zipfile
import pcbnew as pcb

ROOT = Path(__file__).resolve().parents[1]
raise SystemExit('Historical v0.2 exporter disabled: use export_hand_solder.py with a new versioned output directory; do not overwrite archived releases.')
CLI = '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
NAME = 'gdep133c02-driver'
BOARD = ROOT / (NAME + '.kicad_pcb')
SCH = ROOT / (NAME + '.kicad_sch')
OUT = ROOT / 'releases/cad-review-2026-10-01'
OUT.mkdir(parents=True, exist_ok=True)
def run(*args):
    subprocess.run([CLI, *map(str,args)], check=True)

run('sch','erc',SCH,'--format','json','-o',ROOT/'reports/erc.json','--exit-code-violations')
run('pcb','drc',BOARD,'--schematic-parity','--refill-zones','--save-board','--format','json','-o',ROOT/'reports/drc.json','--exit-code-violations')
run('sch','export','netlist',SCH,'--format','kicadxml','-o',ROOT/'reports/netlist.xml')
run('sch','export','pdf',SCH,'-o',ROOT/'reports/schematic.pdf')
run('pcb','export','pdf',BOARD,'--mode-single','-l','F.Cu,F.Silkscreen,Edge.Cuts','-o',ROOT/'reports/preview/board.pdf')
run('pcb','export','gerbers',BOARD,'-l','F.Cu,In1.Cu,In2.Cu,B.Cu,F.Mask,B.Mask,F.Silkscreen,B.Silkscreen,Edge.Cuts','-o',OUT/'gerber','--check-zones')
run('pcb','export','drill',BOARD,'-o',OUT/'gerber','--excellon-separate-th','--generate-map','--generate-report')
run('pcb','export','pos',BOARD,'--format','csv','--units','mm','--smd-only','--exclude-dnp','-o',OUT/'positions-kicad.csv')
run('pcb','export','step',BOARD,'--force','--no-dnp','-o',ROOT/'reports/placement.step')
run('pcb','export','svg',BOARD,'--mode-single','--fit-page-to-board','--exclude-drawing-sheet','-l','F.Cu,F.Silkscreen,Edge.Cuts','-o',ROOT/'reports/preview/top.svg')
run('pcb','export','svg',BOARD,'--mode-single','--fit-page-to-board','--exclude-drawing-sheet','-l','In1.Cu,Edge.Cuts','-o',ROOT/'reports/preview/ground.svg')
run('pcb','export','svg',BOARD,'--mode-single','--fit-page-to-board','--exclude-drawing-sheet','--mirror','-l','B.Cu,B.Silkscreen,Edge.Cuts','-o',ROOT/'reports/preview/bottom.svg')

b=pcb.LoadBoard(str(BOARD));pads=[];groups={};missing=[]
for f in b.GetFootprints():
    for p in f.Pads():
        q=p.GetPosition();sz=p.GetSize()
        pads.append({'ref':f.GetReference(),'pin':p.GetNumber(),'net':p.GetNetCode(),'netname':p.GetNetname(),'x':pcb.ToMM(q.x)-50,'y':pcb.ToMM(q.y)-50,'sx':pcb.ToMM(sz.x),'sy':pcb.ToMM(sz.y),'tht':p.GetAttribute() in [pcb.PAD_ATTRIB_PTH,pcb.PAD_ATTRIB_NPTH],'npth':p.GetAttribute()==pcb.PAD_ATTRIB_NPTH})
    if not len(f.Models()): missing.append(f.GetReference())
    if f.GetAttributes() & pcb.FP_EXCLUDE_FROM_BOM or f.IsDNP():continue
    fields={x.GetName():x.GetText() for x in f.GetFields()}
    key=(f.GetValue(),str(f.GetFPID().GetLibItemName()),fields.get('Manufacturer',''),fields.get('MPN',''))
    groups.setdefault(key,[]).append(f.GetReference())
(ROOT/'reports/pads.json').write_text(json.dumps(pads,indent=2)+'\n')
with (OUT/'bom.csv').open('w',newline='') as s:
    w=csv.writer(s);w.writerow(['Comment','Designator','Footprint','Quantity','Manufacturer','MPN'])
    for key,refs in sorted(groups.items()):w.writerow([key[0],','.join(sorted(refs)),key[1],len(refs),key[2],key[3]])
with (OUT/'positions-kicad.csv').open() as s:
    rows=list(csv.DictReader(s))
with (OUT/'cpl-jlc-review.csv').open('w',newline='') as s:
    w=csv.writer(s);w.writerow(['Designator','Mid X','Mid Y','Layer','Rotation'])
    for r in rows:w.writerow([r['Ref'],r['PosX']+'mm',r['PosY']+'mm','Top' if r['Side']=='top' else 'Bottom',r['Rot']])
summary={'footprints':len(list(b.GetFootprints())),'pads':len(pads),'tracks':sum(not isinstance(t,pcb.PCB_VIA) for t in b.GetTracks()),'vias':sum(isinstance(t,pcb.PCB_VIA) for t in b.GetTracks()),'minimum_track_mm':min(pcb.ToMM(t.GetWidth()) for t in b.GetTracks() if not isinstance(t,pcb.PCB_VIA)),'missing_3d_models':missing}
(ROOT/'reports/board-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
sources=[p for p in ROOT.iterdir() if p.suffix in ['.kicad_pro','.kicad_sch','.kicad_pcb','.kicad_dru']]
proof={'date':'2026-10-01','kicad_version':'10.0.6','source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}}
(ROOT/'reports/check-provenance.json').write_text(json.dumps(proof,indent=2)+'\n')
with zipfile.ZipFile(OUT/'gerber-review.zip','w',zipfile.ZIP_DEFLATED) as z:
    for p in sorted((OUT/'gerber').iterdir()):
        if p.suffix in ['.gbr','.gtl','.gbl','.g1','.g2','.gts','.gbs','.gto','.gbo','.gm1','.drl','.gbrjob']:z.write(p,p.name)
print(json.dumps(summary,indent=2))
