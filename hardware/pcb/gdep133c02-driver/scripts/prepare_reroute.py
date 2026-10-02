#!/usr/bin/env python3
"""Correct placement and source-drawing land sizes before native DSN routing."""
from pathlib import Path
import pcbnew as p
ROOT=Path(__file__).resolve().parents[1]
# Strip only native top-level route records before loading, avoiding SWIG removal
# invalidation on large track collections. Original board remains checkpointed.
import re
boardpath=ROOT/'gdep133c02-driver.kicad_pcb'
text=boardpath.read_text()
text=re.sub(r'(?ms)^\t\((?:segment|via)\b.*?^\t\)\n', '', text)
tmp=ROOT/'reports/unrouted-input.kicad_pcb';tmp.write_text(text)
b=p.LoadBoard(str(tmp))
positions={'D2':(49,43),'D4':(69,43),'C27':(6,24),'R32':(74,55),'R43':(68,75),'R38':(91,70),'TP16':(10,76),'R25':(31,16),'R35':(31,20),'R36':(31,24)}
for f in b.GetFootprints():
 ref=f.GetReference()
 if ref in positions:
  x,y=positions[ref];f.SetPosition(p.VECTOR2I(p.FromMM(x+50),p.FromMM(y+50)))
 if ref=='FPC1':
  for pad in f.Pads():
   num=int(pad.GetNumber())
   if num<=60:pad.SetSize(p.VECTOR2I(p.FromMM(.3),p.FromMM(1.2)))
   else:
    pad.SetSize(p.VECTOR2I(p.FromMM(2),p.FromMM(1.8)))
    pad.SetPosition(p.VECTOR2I(p.FromMM(100+(-16.3 if num==61 else 16.3)),p.FromMM(59.25)))
# Native 4-layer export. Inner GND plane will be added after power routing.
import json
datafile=ROOT/'design-data.json';data=json.loads(datafile.read_text())
for part in data['parts']:
 if part['ref'] in positions:part['xy']=list(positions[part['ref']])
datafile.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
p.SaveBoard(str(ROOT/'gdep133c02-driver.kicad_pcb'),b)
print('DSN exported',p.ExportSpecctraDSN(b,str(ROOT/'reports/reroute.dsn')))
