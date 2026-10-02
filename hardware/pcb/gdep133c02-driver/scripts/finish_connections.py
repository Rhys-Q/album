#!/usr/bin/env python3
"""Normalize endpoints and add explicit FPC escapes and ground stitching."""
from pathlib import Path
import pcbnew as p
ROOT=Path(__file__).resolve().parents[1]
b=p.LoadBoard(str(ROOT/'gdep133c02-driver.kicad_pcb'))
vias=[t for t in b.GetTracks() if isinstance(t,p.PCB_VIA)]
for t in b.GetTracks():
 if isinstance(t,p.PCB_VIA):continue
 if t.GetWidth()<p.FromMM(.2):t.SetWidth(p.FromMM(.2))
 for v in vias:
  if t.GetNetCode()!=v.GetNetCode():continue
  pos=v.GetPosition()
  if (t.GetStart()-pos).EuclideanNorm()<p.FromMM(.23):t.SetStart(pos)
  if (t.GetEnd()-pos).EuclideanNorm()<p.FromMM(.23):t.SetEnd(pos)
def via(net,x,y):
 v=p.PCB_VIA(b);v.SetNet(b.FindNet(net));v.SetWidth(p.FromMM(.6));v.SetDrill(p.FromMM(.3));v.SetViaType(p.VIATYPE_THROUGH);v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetPosition(p.VECTOR2I(p.FromMM(x),p.FromMM(y)));b.Add(v)
def track(net,a,c):
 t=p.PCB_TRACK(b);t.SetNet(b.FindNet(net));t.SetWidth(p.FromMM(.2));t.SetLayer(p.F_Cu);t.SetStart(p.VECTOR2I(p.FromMM(a[0]),p.FromMM(a[1])));t.SetEnd(p.VECTOR2I(p.FromMM(c[0]),p.FromMM(c[1])));b.Add(t)
via('GND',101.85,56.3)
for net,x in [('AVDD',89.25),('VBB_3P5V',112.75)]:track(net,(x,57.5),(x,52));via(net,x,52)
p.SaveBoard(str(ROOT/'gdep133c02-driver.kicad_pcb'),b)
# Remove collapsed segments only; no electrical connection is lost.
import re
path=ROOT/'gdep133c02-driver.kicad_pcb';s=path.read_text()
def clean(m):
 block=m.group();a=re.search(r'\(start ([^)]+)\)',block).group(1);c=re.search(r'\(end ([^)]+)\)',block).group(1)
 return '' if a==c else block
s=re.sub(r'(?ms)^\t\(segment\b.*?^\t\)\n',clean,s);path.write_text(s)
