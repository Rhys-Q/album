#!/usr/bin/env python3
"""Check netlist/physical-pad parity and fixed design requirements. Not a DRC replacement."""
from pathlib import Path
import json,xml.etree.ElementTree as ET,csv,re,hashlib
ROOT=Path(__file__).resolve().parents[1];data=json.loads((ROOT/'design-data.json').read_text());parts={p['ref']:p for p in data['parts']}
assert len(parts)==len(data['parts'])
want={(p['ref'],str(k)):v for p in parts.values() for k,v in p['pins'].items() if v}
xml=ET.parse(ROOT/'reports/netlist.xml').getroot();got={}
for net in xml.find('nets'):
 for pin in net.findall('node'):
  ref=pin.attrib['ref'];key=(ref,pin.attrib['pin'])
  if ref.startswith('#') or net.attrib['name'].startswith('unconnected-'):continue
  got[key]=net.attrib['name']
assert got==want,('Schematic differs from design data',set(got.items())^set(want.items()))
# KiCad PCB symbol links omit the root schematic UUID. Compare against exported sheet paths.
from schematic_sexp import parse,kids,one
board_tree=parse((ROOT/'gdep133c02-driver.kicad_pcb').read_text())
footprint_links={}
for fp in kids(board_tree,'footprint'):
 ref=next(z[2] for z in kids(fp,'property') if z[1]=='Reference')
 assert ref not in footprint_links, ('Duplicate PCB reference',ref)
 paths=kids(fp,'path');footprint_links[ref]=str(paths[0][1]) if paths else ''
for comp in xml.find('components'):
 ref=comp.attrib['ref']
 if ref not in parts:continue
 z=parts[ref]
 assert comp.findtext('value')==z['value'], ('Value mismatch',ref)
 assert comp.findtext('footprint')==z['fp'], ('Footprint mismatch',ref)
 fields={f.attrib['name']:f.text or '' for f in comp.findall('fields/field')}
 assert fields.get('MPN')==z['mpn'] and fields.get('Manufacturer')==z['vendor'], ('BOM property mismatch',ref)
 expected=comp.find('sheetpath').attrib['tstamps']+comp.findtext('tstamps')
 assert footprint_links.get(ref)==expected, ('PCB symbol link incompatible with KiCad',ref,footprint_links.get(ref),expected)
pads=json.loads((ROOT/'reports/pads.json').read_text());actual={(p['ref'],p['pin']):p['netname'] for p in pads if p['net'] and not p['netname'].startswith('unconnected-')}
assert actual==want,('PCB pads differ from schematic',set(actual.items())^set(want.items()))
for pin,net in [('22','EPD_3V3'),('23','EPD_3V3'),('26','GND'),('41','VBB_3P5V'),('56','VBB_3P5V')]:assert parts['FPC1']['pins'][pin]==net
for pin in ['11','15','40','57']:assert parts['FPC1']['pins'][pin] is None
for ref in ['U1','U2','U3']:assert parts[ref]['value']=='0.2 ohm'
assert parts['U4']['pins']['8']=='EPD_3V3' and parts['U4']['pins']['3'] is None
assert set(parts['R1']['pins'].values())=={'BUSY_N','EPD_3V3'}
assert parts['J2']['pins']['16'] is None
assert parts['J2']['pins']['5']=='SI1' and parts['J2']['pins']['13']=='BUSY_N'
assert parts['U5']['mpn']=='TPS22917DBVR'
assert parts['U5']['pins']=={'1':'BENCH_3V3','2':'GND','3':'EPD_PWR_EN','4':'SW_CT','5':'EPD_3V3','6':'EPD_3V3'}
assert set(parts['C36']['pins'].values())=={'SW_CT','BENCH_3V3'}
assert parts['C36']['mpn']=='C0805C102J5GACTU'
removed={'C34','C35','Q9','Q10','R14','R15','R16','R22','R23','R24','R25','R26','R27','R28','R29','R31','R32','R33','R34','R37','R38','R4','R5','R6','R9','U6','U7'}
assert not (set(removed)|{'L4','L5'}).intersection(parts)
assert not {'VIN','AVDD'}.intersection(want.values())
assert parts['R49']['pins']=={'1':'GDRC','2':'Q7_GATE'}
assert parts['R49']['value']=='0 ohm' and 'R_0805_' in parts['R49']['fp'] and not parts['R49']['dnp']
assert parts['Q7']['pins']['1']=='Q7_GATE' and parts['R13']['pins']['2']=='Q7_GATE'
assert parts['TP25']['pins']=={'1':'GDRC'} and parts['TP26']['pins']=={'1':'Q7_GATE'}
assert parts['TP25']['dnp'] and parts['TP26']['dnp']
assert [z['ref'] for z in parts.values() if {'GDRC','Q7_GATE'} <= set(z['pins'].values())]==['R49']
for ref in ['C29','C30','C31','C32','C33']:
 assert set(parts[ref]['pins'].values())=={'EPD_3V3','GND'}
assert sum(not z['dnp'] for z in parts.values())==data['assembled_components']
assert len(want)==sum(bool(v) for z in data['parts'] for v in z['pins'].values())
assert parts['R17']['value']==parts['R50']['value']=='200k ohm'
assert parts['R17']['pins']=={'1':'VGL_FB_MID','2':'FBN'}
assert parts['R50']['pins']=={'1':'VGL','2':'VGL_FB_MID'}
for ref,host,screen in [('R39','HOST_SCLK','SCLK'),('R40','HOST_MOSI','SI0'),('R41','HOST_CS_M_N','CS_M_N'),('R42','HOST_CS_S_N','CS_S_N'),('R43','HOST_RES_N','RES_N')]:
 assert parts[ref]['pins']=={'1':host,'2':screen}
# Footprints must resolve locally, with no personal-directory model dependencies.
for fp in (ROOT/'lib/Driver.pretty').glob('*.kicad_mod'):
 for model in re.findall(r'\(model "([^"]+)"',fp.read_text()):
  assert model.startswith('${KIPRJMOD}/'),model
  assert (ROOT/model.replace('${KIPRJMOD}/','')).is_file(),model
assert not any(s['violations'] for s in json.loads((ROOT/'reports/erc.json').read_text())['sheets'])
drc=json.loads((ROOT/'reports/drc.json').read_text())
assert not any(drc[k] for k in ['violations','unconnected_items','schematic_parity']), 'KiCad DRC failed'
pro=json.loads((ROOT/'gdep133c02-driver.kicad_pro').read_text())['board']['design_settings']
assert not pro['drc_exclusions']
assert not any(v=='ignore' for v in pro['rule_severities'].values())
proof=json.loads((ROOT/'reports/check-provenance.json').read_text())
for name,digest in proof['source_sha256'].items():
 assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest, ('Stale check report',name)
result={'date':'2026-10-01','kicad_version':'10.0.6','schematic_connected_pins':len(want),'pcb_pad_parity':'PASS','fixed_pin_requirements':'PASS','project_local_libraries_and_available_models':'PASS','erc':'PASS - zero violations','drc':'PASS - zero violations/unconnected/parity; no ignored checks or exclusions','gui_open':'NOT VERIFIED for current sources','fpc_footprint':'LAND DIMENSIONS CHECKED - physical mating/pin orientation pending','routing':'CONNECTED - minimum 0.2mm; power core 0.5/0.8mm; 0.6/0.3mm vias','power_trace_and_loop_review':'WIDTH REPAIRED; transient/Kelvin/current/thermal acceptance pending','ground_plane':'IMPLEMENTED - In1.Cu GND and front/back pours','procurement_and_effective_capacitance':'PARTIAL - see docs/国内采购与手焊改版-v0.6.md and docs/采购清单-v0.6.csv; domestic payment and biased capacitance gaps remain','hardware_tests':'NOT PERFORMED','cad_checks_pass':True,'review_package_available':True,'release_allowed':False}
result['date']=proof['date']
result['revision']=data['revision']
result['assembled_components']=data['assembled_components']
result['pcb_symbol_links']='PASS - all footprint links match KiCad-exported sheet paths without root UUID'
result['signal_isolation']='REMOVED - mandatory host power sequencing'
result['zone_refill']=proof['zone_refill']
result['gui_open']=proof.get('gui_open','NOT VERIFIED for current sources - see reports/gui-open.json')
(ROOT/'reports/validation-status.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
with (ROOT/'reports/bom-review.csv').open('w',newline='') as f:
 w=csv.writer(f,lineterminator="\n");w.writerow(['Designator','Comment','Footprint','Manufacturer','MPN','Quantity','DNP','SelectionStatus'])
 for p in data['parts']:
  if p['group']=='test':continue
  w.writerow([p['ref'],p['value'],p['fp'],p['vendor'],p['mpn'],1,p['dnp'],'DRAFT: procurement/parameters not released'])
with (ROOT/'docs/host-interface.csv').open('w',newline='') as f:
 w=csv.writer(f,lineterminator="\n");w.writerow(['Connector','Pin','Net','Direction','SupplyDomain','DefaultState'])
 for pin,net in parts['J2']['pins'].items():
  dr='Host to driver' if net in ['HOST_SCLK','HOST_MOSI','HOST_CS_M_N','HOST_CS_S_N','HOST_RES_N','EPD_PWR_EN'] else 'Driver to host' if net in ['SI1','BUSY_N'] else 'Supply/reference'
  state='LOW by R30; screen disabled' if net=='EPD_PWR_EN' else 'Common ground' if net=='GND' else 'Unconnected; do not use' if net is None else 'See interface-power-state.md'
  w.writerow(['J2',pin,net,dr,'3.3V only; direct interface',state])
print('PASS:',len(want),'connected pins, parity, fixed interface, ERC/DRC, local libraries. Hardware acceptance remains pending.')
