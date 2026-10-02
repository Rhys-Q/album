#!/usr/bin/env python3
"""Apply schematic metadata and remove redundant drill objects, preserving routes."""
import json,xml.etree.ElementTree as ET
from pathlib import Path
import pcbnew as pcb
ROOT=Path(__file__).resolve().parents[1]
board=pcb.LoadBoard(str(ROOT/'gdep133c02-driver.kicad_pcb'))
parts={p['ref']:p for p in json.loads((ROOT/'design-data.json').read_text())['parts']}
xml=ET.parse(ROOT/'reports/netlist.xml').getroot()
nets={}
for n in xml.find('nets'):
 for node in n.findall('node'):nets[node.attrib['ref'],node.attrib['pin']]=n.attrib['name']
for f in board.GetFootprints():
 ref=f.GetReference()
 if ref not in parts:
  if ref.startswith('H'):f.SetAttributes(f.GetAttributes()|pcb.FP_BOARD_ONLY|pcb.FP_EXCLUDE_FROM_BOM|pcb.FP_EXCLUDE_FROM_POS_FILES)
  continue
 p=parts[ref]
 f.SetFields({'MPN':p['mpn'],'Manufacturer':p['vendor'],'Datasheet':p['url']})
 for name in ('MPN','Manufacturer','Datasheet'):f.GetField(name).SetVisible(False)
 f.SetDNP(p['dnp'])
 if p['group']=='test':f.SetAttributes(f.GetAttributes()|pcb.FP_EXCLUDE_FROM_BOM|pcb.FP_EXCLUDE_FROM_POS_FILES)
 for pad in f.Pads():
  num=pad.GetNumber();name=nets.get((ref,num))
  if name and name.startswith('unconnected-'):
   ni=board.FindNet(name)
   if ni is None or ni.GetNetCode()<0:ni=pcb.NETINFO_ITEM(board,name);board.Add(ni)
   pad.SetNet(ni)
# A via at an existing same-net through-hole is unnecessary and can violate drills.
seen=set();removed=0
pth=[p for f in board.GetFootprints() for p in f.Pads() if p.GetAttribute()==pcb.PAD_ATTRIB_PTH]
for t in list(board.GetTracks()):
 if not isinstance(t,pcb.PCB_VIA):continue
 pos=t.GetPosition();key=(pos.x,pos.y,t.GetNetCode())
 redundant=key in seen
 for p in pth:
  if p.GetNetCode()==t.GetNetCode() and (p.GetPosition()-pos).EuclideanNorm()<pcb.FromMM(.1):redundant=True
 if redundant:board.Remove(t);removed+=1
 else:seen.add(key)
pcb.SaveBoard(str(ROOT/'gdep133c02-driver.kicad_pcb'),board)
print('Schematic attributes synchronized; redundant vias removed:',removed)
