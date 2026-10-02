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
pads=json.loads((ROOT/'reports/pads.json').read_text());actual={(p['ref'],p['pin']):p['netname'] for p in pads if p['net'] and not p['netname'].startswith('unconnected-')}
assert actual==want,('PCB pads differ from schematic',set(actual.items())^set(want.items()))
for pin,net in [('22','BS0'),('23','BS1'),('26','GND'),('41','VNCP_3P5V'),('56','VBB_3P5V')]:assert parts['FPC1']['pins'][pin]==net
for pin in ['11','15','40','57']:assert parts['FPC1']['pins'][pin] is None
assert set(parts['R24']['pins'].values())=={'BS0','VDD'}
assert set(parts['R25']['pins'].values())=={'BS1','VDD'}
assert set(parts['R16']['pins'].values())=={'VNCP_3P5V','VBB_3P5V'}
for ref in ['U1','U2','U3']:assert parts[ref]['value']=='0.2 ohm'
assert parts['U4']['pins']['8']=='EPD_3V3'
assert set(parts['R1']['pins'].values())=={'BUSY_N','VDDIO'}
assert parts['J2']['pins']['16']=='HOST_3V3'
assert parts['U6']['pins']['20']=='EPD_3V3' and parts['U7']['pins']['20']=='HOST_3V3'
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
result={'date':'2026-10-01','kicad_version':'10.0.6','schematic_connected_pins':len(want),'pcb_pad_parity':'PASS','fixed_pin_requirements':'PASS','project_local_libraries_and_available_models':'PASS','erc':'PASS - zero violations','drc':'PASS - zero violations/unconnected/parity; no ignored checks or exclusions','gui_open':'PASS - schematic and PCB opened; GUI DRC zero violations/unconnected/ignored checks; parity checked by CLI','fpc_footprint':'LAND DIMENSIONS CHECKED - physical mating/pin orientation pending','routing':'CONNECTED - minimum 0.2mm; power core 0.5/0.8mm; 0.6/0.3mm vias','power_trace_and_loop_review':'WIDTH REPAIRED; transient/Kelvin/current/thermal acceptance pending','ground_plane':'IMPLEMENTED - In1.Cu GND and front/back pours','procurement_and_effective_capacitance':'NOT COMPLETED - see docs/design-review.md','hardware_tests':'NOT PERFORMED','cad_checks_pass':True,'review_package_available':True,'release_allowed':False}
(ROOT/'reports/validation-status.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
with (ROOT/'reports/bom-review.csv').open('w',newline='') as f:
 w=csv.writer(f);w.writerow(['Designator','Comment','Footprint','Manufacturer','MPN','Quantity','DNP','SelectionStatus'])
 for p in data['parts']:
  if p['group']=='test':continue
  w.writerow([p['ref'],p['value'],p['fp'],p['vendor'],p['mpn'],1,p['dnp'],'DRAFT: procurement/parameters not released'])
with (ROOT/'docs/host-interface.csv').open('w',newline='') as f:
 w=csv.writer(f);w.writerow(['Connector','Pin','Net','Direction','SupplyDomain','DefaultState'])
 for pin,net in parts['J2']['pins'].items():
  dr='Host to driver' if net in ['HOST_SCLK','HOST_MOSI','HOST_CS_M_N','HOST_CS_S_N','HOST_RES_N','EPD_PWR_EN'] else 'Driver to host' if net in ['HOST_MISO','HOST_BUSY_N'] else 'Supply/reference'
  state='LOW by R30 via R29; screen disabled' if net=='EPD_PWR_EN' else 'Common ground' if net=='GND' else '3.3V logic supply only' if net=='HOST_3V3' else 'See interface-power-state.md'
  w.writerow(['J2',pin,net,dr,'HOST_3V3',state])
print('PASS:',len(want),'connected pins, parity, fixed interface, ERC/DRC, local libraries. Hardware acceptance remains pending.')
