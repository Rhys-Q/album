#!/usr/bin/env python3
"""Native PCB transformation from approved baseline; KiCad DRC is authoritative."""
from pathlib import Path
import json,xml.etree.ElementTree as ET
import pcbnew as p
R=Path(__file__).resolve().parents[1];B=R/'reports/hand-solder-v0.3/before'
# Migration helper only. The final native files are authoritative.
import sys
if '--rebuild-from-baseline' not in sys.argv:
 raise SystemExit('Migration already applied; rebuilding from the archived baseline discards subsequent layout/edits. Use --rebuild-from-baseline only in a disposable project copy.')
b=p.LoadBoard(str(B/'gdep133c02-driver.kicad_pcb'));change=json.loads((R/'reports/hand-solder-v0.3/change-map.json').read_text());alias=change['aliases'];removed=set(change['removed']);fps={f.GetReference():f for f in b.GetFootprints()}
reroute=set('HOST_SCLK HOST_MOSI HOST_CS_M_N HOST_CS_S_N HOST_RES_N BUF_SCLK BUF_MOSI BUF_CS_M_N BUF_CS_S_N BUF_RES_N HOST_BUSY_N HOST_MISO BUSY_N SI1 HOST_3V3 OE_PANEL_N OE_HOST_N ALERT_N'.split())
for t in list(b.GetTracks()):
 if t.GetNetname() in reroute or t.GetNetname().startswith('unconnected-'):b.Delete(t)
# Merge net references on preserved pads, tracks, zones.
def net(n):
 z=b.FindNet(n)
 if not z or z.GetNetCode()<0:
  z=p.NETINFO_ITEM(b,n);b.Add(z)
 return z
for f in fps.values():
 for pad in f.Pads():
  n=pad.GetNetname()
  if n in alias:pad.SetNet(net(alias[n]))
for t in b.GetTracks():
 if t.GetNetname() in alias:t.SetNet(net(alias[t.GetNetname()]))
for z in b.Zones():
 if z.GetNetname() in alias:z.SetNet(net(alias[z.GetNetname()]))
def track(n,a,c,w=.2):
 if a==c:return
 t=p.PCB_TRACK(b);t.SetNet(net(n));t.SetWidth(p.FromMM(w));t.SetLayer(p.F_Cu);t.SetStart(a);t.SetEnd(c);b.Add(t)
olddata=json.loads((B/'design-data.json').read_text());oldparts={x['ref']:x for x in olddata['parts']}
for ref in sorted(removed):
 f=fps[ref]
 if oldparts[ref]['value']=='0 ohm' and not oldparts[ref]['dnp']:
  pads={q.GetNumber():q for q in f.Pads()};n=alias.get(oldparts[ref]['pins']['1'],oldparts[ref]['pins']['1']);track(n,pads['1'].GetPosition(),pads['2'].GetPosition(),.8 if ref in ['R26','R27','R28','R31','R32'] else .5 if ref in ['R6','R9','R16','R33','R34'] else .2)
 b.Delete(f)
old=fps['U5'];uid=old.m_Uuid;path=old.GetPath();b.Delete(old)
f=p.FootprintLoad(str(R/'lib/Driver.pretty'),'Package_TO_SOT_SMD__SOT-23-6');f.SetReference('U5');f.SetValue('TPS22917DBVR');f.SetFPID(p.LIB_ID('Driver','Package_TO_SOT_SMD__SOT-23-6'));f.SetPath(path);f.SetPosition(p.VECTOR2I(p.FromMM(82),p.FromMM(119)));b.Add(f)
# Preserve UUID/path for U5, but replace its package and field values.
for name,value in [('MPN','TPS22917DBVR'),('Manufacturer','Texas Instruments'),('Datasheet','https://www.ti.com/lit/ds/symlink/tps22917.pdf')]:
 f.SetField(name,value)
f=p.FootprintLoad(str(R/'lib/Driver.pretty'),'Capacitor_SMD__C_0805_2012Metric');f.SetReference('C36');f.SetValue('1nF/50V C0G');f.SetFPID(p.LIB_ID('Driver','Capacitor_SMD__C_0805_2012Metric'));f.SetPosition(p.VECTOR2I(p.FromMM(84),p.FromMM(116)));b.Add(f)
for name,value in [('MPN','C0805C102J5GACTU'),('Manufacturer','KEMET'),('Datasheet','https://search.kemet.com/download/specsheet/C0805C102J5GACTU')]:
 f.SetField(name,value)
x=ET.parse(R/'reports/hand-solder-v0.3/netlist.xml').getroot();components={c.attrib['ref']:c for c in x.find('components')};nets={(q.attrib['ref'],q.attrib['pin']):n.attrib['name'] for n in x.find('nets') for q in n.findall('node')}
from schematic_sexp import parse,one
rootuuid=str(one(parse((R/'gdep133c02-driver.kicad_sch').read_text()),'uuid')[1])
for f in b.GetFootprints():
 ref=f.GetReference()
 if ref in components:
  c=components[ref];f.SetPath(p.KIID_PATH('/'+rootuuid+c.find('sheetpath').attrib['tstamps']+c.findtext('tstamps')))
  for pad in f.Pads():
   if (ref,pad.GetNumber()) in nets:pad.SetNet(net(nets[(ref,pad.GetNumber())]))
# No obsolete net list entries: removal is safe after every connected object was remapped.
used={pad.GetNetname() for f in b.GetFootprints() for pad in f.Pads()}|{t.GetNetname() for t in b.GetTracks()}|{z.GetNetname() for z in b.Zones()}
for nn in list(b.GetNetInfo().NetsByNetcode().values()):
 if nn.GetNetCode() and nn.GetNetname() not in used:b.Delete(nn)
b.GetTitleBlock().SetRevision('0.3-HAND-SOLDER');b.GetTitleBlock().SetDate('2026-10-03')
p.SaveBoard(str(R/'gdep133c02-driver.kicad_pcb'),b)
print('Native PCB transformed; rerouting and fill/check required')
