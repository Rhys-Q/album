#!/usr/bin/env python3
"""Export domestic JLC review files from audited CAD without modifying sources."""
from pathlib import Path
import csv, hashlib, json, re, subprocess, zipfile

ROOT = Path(__file__).resolve().parents[1]
CLI = '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
NAME = 'gdep133c02-driver'
BASE = ROOT/'releases/cad-review-2026-10-01'
OUT = ROOT/'releases/jlc-cn-review-2026-10-03'
PROOF = json.loads((BASE/'verification-2026-10-03.json').read_text())
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
for name, value in PROOF['source_sha256'].items():
    assert digest(ROOT/name) == value, ('Source changed: re-audit first', name)
for name, value in PROOF['artifact_sha256'].items():
    assert digest(BASE/name) == value, ('Audited artifact changed', name)
assert not OUT.exists(), 'Output exists; use a new version rather than overwriting it'
OUT.mkdir(); (OUT/'gerber').mkdir()
def run(*args): subprocess.run([CLI,*map(str,args)],check=True)
run('pcb','export','gerbers',ROOT/(NAME+'.kicad_pcb'),'-l','F.Cu,In1.Cu,In2.Cu,B.Cu,F.Mask,B.Mask,F.Silkscreen,B.Silkscreen,Edge.Cuts','--no-x2','--no-netlist','-o',OUT/'gerber')
run('pcb','export','drill',ROOT/(NAME+'.kicad_pcb'),'--excellon-separate-th','-o',OUT/'gerber')
run('pcb','export','pos',ROOT/(NAME+'.kicad_pcb'),'--format','csv','--units','mm','--smd-only','--exclude-dnp','-o',OUT/'positions-kicad.csv')
def read(p):
    with p.open(newline='') as f: return list(csv.DictReader(f))
def write(p,columns,rows):
    with p.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=columns);w.writeheader();w.writerows(rows)
positions=read(OUT/'positions-kicad.csv')
assert positions==read(BASE/'positions-kicad.csv')
refs={r['Ref'] for r in positions};assert len(refs)==len(positions)==127
maps={
'Resistor_SMD__R_0603_1608Metric':'0603',
'Resistor_SMD__R_1206_3216Metric':'1206',
'Capacitor_SMD__C_0603_1608Metric':'0603',
'Capacitor_SMD__C_0805_2012Metric':'0805',
'Capacitor_SMD__C_1210_3225Metric':'1210',
'Inductor_SMD__L_0603_1608Metric':'0603',
'Inductor_SMD__L_Coilcraft_MSS1246T-XXX':'MSS1246',
'Package_TO_SOT_SMD__SOT-23':'SOT-23',
'Package_TO_SOT_SMD__SOT-323_SC-70':'SOT-323',
'Diode_SMD__D_SOD-123':'SOD-123',
'Diode_SMD__D_SOD-123F':'SOD-123F',
'Package_SO__TSSOP-20_4.4x6.5mm_P0.65mm':'TSSOP-20',
'Package_SO__SOIC-8_3.9x4.9mm_P1.27mm':'SOIC-8',
'Package_CSP__WLCSP-4_0.89x0.89mm_Layout2x2_P0.5mm':'WLCSP-4',
'FPC_05FB_60PH20':'FPC 60P 0.5mm',
'Connector_PinHeader_2.54mm__PinHeader_1x02_P2.54mm_Vertical':'PinHeader 1x02 2.54mm',
'Connector_PinHeader_2.54mm__PinHeader_2x08_P2.54mm_Vertical':'PinHeader 2x08 2.54mm',
}
smt=[];manual=[];seen=set()
for row in read(BASE/'bom.csv'):
    rr=row['Designator'].split(',');assert len(rr)==int(row['Quantity'])
    assert not seen.intersection(rr);seen.update(rr)
    assert row['Footprint'] in maps, row['Footprint']
    targets=[ref in refs for ref in rr];assert all(targets) or not any(targets)
    new=dict(row);new['Footprint']=maps[row['Footprint']]
    new['Comment']=row['Comment'] if row['Comment']==row['MPN'] else row['Comment']+' '+row['MPN']
    (smt if all(targets) else manual).append(new)
assert seen-refs=={'J1','J2'}
assert {ref for row in smt for ref in row['Designator'].split(',')}==refs
columns=['Comment','Designator','Footprint','Quantity','Manufacturer','MPN']
write(OUT/(NAME+'-bom-smt.csv'),columns,smt)
write(OUT/(NAME+'-bom-manual.csv'),columns,manual)
cpl=[{'Designator':r['Ref'],'Mid X':r['PosX'],'Mid Y':r['PosY'],'Layer':'T' if r['Side']=='top' else 'B','Rotation':r['Rot']} for r in positions]
for row in cpl:
    for k in ['Mid X','Mid Y','Rotation']:assert re.fullmatch(r'-?\d+(\.\d+)?',row[k]);float(row[k])
assert all(r['Layer']=='T' for r in cpl)
write(OUT/(NAME+'-cpl-smt.csv'),['Designator','Mid X','Mid Y','Layer','Rotation'],cpl)
def graphics(s):
    return '\n'.join(l for l in s.splitlines() if not l.startswith(('G04','%TF','%TA','%TO','%TD','; DRILL file KiCad','; #@!')))
checks={}
manufacturing=[]
for p in sorted((OUT/'gerber').iterdir()):
    if p.suffix not in ['.gtl','.gbl','.g1','.g2','.gts','.gbs','.gto','.gbo','.gm1','.drl']:continue
    assert graphics(p.read_text())==graphics((BASE/'gerber'/p.name).read_text()), ('Geometry mismatch',p.name)
    if p.suffix!='.drl':assert not re.search(r'%T[FADO]',p.read_text()),p.name
    checks[p.name]='PASS: identical geometry commands; only comments/X2 attributes omitted'
    manufacturing.append(p)
assert len(manufacturing)==11
with zipfile.ZipFile(OUT/(NAME+'-gerber-rs274x.zip'),'w',zipfile.ZIP_DEFLATED) as z:
    for p in manufacturing:z.write(p,p.name)
for name,value in PROOF['source_sha256'].items():assert digest(ROOT/name)==value
report={'date':'2026-10-03','kicad_version':'10.0.6','production_released':False,'source_sha256':PROOF['source_sha256'],'source_audit':'../../reports/release-audit-2026-10-03/comparison.json','geometry_comparison':checks,'smt_bom_groups':len(smt),'smt_components':127,'cpl_components':127,'manual_components':['J1','J2'],'all_smt_on_top':True,'numeric_coordinates_mm':True,'origin_and_rotation_unchanged':True,'jlc_smt_part_numbers':'NOT MATCHED; exact MPN preserved; no stock/substitution claim','zone_basis':'Existing saved PCB fills; no refill or save performed','files_sha256':{str(p.relative_to(OUT)):digest(p) for p in sorted(OUT.rglob('*')) if p.is_file()}}
(OUT/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'output':str(OUT),'smt_groups':len(smt),'smt_components':127,'geometry_files_checked':len(checks),'source_unchanged':True},ensure_ascii=False))
