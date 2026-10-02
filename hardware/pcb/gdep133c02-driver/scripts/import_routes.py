#!/usr/bin/env python3
"""Import review-only grid routes into the native PCB; not a release check."""
import pcbnew as pcb
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];path=ROOT/'reports/routed-paths.txt'
if (ROOT/'reports/check-provenance.json').exists():
    raise SystemExit('Historical initializer disabled: edit the repaired native KiCad project directly.')
b=pcb.LoadBoard(str(ROOT/'gdep133c02-driver.kicad_pcb'))
for t in list(b.GetTracks()):b.Remove(t)
layers=[pcb.F_Cu,pcb.In2_Cu,pcb.B_Cu]
lines=iter(path.read_text().splitlines());branches=0;segments=0;vias=0
for header in lines:
 if not header:continue
 _,net,n=header.split();net=int(net);pts=[]
 for i in range(int(n)):
  x,y,l=next(lines).split();pts.append((float(x),float(y),int(l)))
 # collapse grid-collinear steps, preserving layer transitions
 keep=[pts[0]]
 for i in range(1,len(pts)-1):
  a,p,c=pts[i-1],pts[i],pts[i+1]
  if a[2]==p[2]==c[2] and abs((p[0]-a[0])*(c[1]-p[1])-(p[1]-a[1])*(c[0]-p[0]))<1e-7:continue
  keep.append(p)
 keep.append(pts[-1])
 for a,c in zip(keep,keep[1:]):
  pa=pcb.VECTOR2I(pcb.FromMM(a[0]+50),pcb.FromMM(a[1]+50));pc=pcb.VECTOR2I(pcb.FromMM(c[0]+50),pcb.FromMM(c[1]+50))
  if a[2]!=c[2]:
   v=pcb.PCB_VIA(b);v.SetPosition(pa);v.SetWidth(pcb.FromMM(.7));v.SetDrill(pcb.FromMM(.3));v.SetViaType(pcb.VIATYPE_THROUGH);v.SetLayerPair(pcb.F_Cu,pcb.B_Cu);v.SetNetCode(net);b.Add(v);vias+=1
  elif pa!=pc:
   t=pcb.PCB_TRACK(b);t.SetStart(pa);t.SetEnd(pc);t.SetWidth(pcb.FromMM(.2));t.SetLayer(layers[a[2]]);t.SetNetCode(net);b.Add(t);segments+=1
 branches+=1
pcb.SaveBoard(str(ROOT/'gdep133c02-driver.kicad_pcb'),b)
print('Review-only routing:',branches,'branches;',segments,'segments;',vias,'vias. Power widths and remaining nets NOT accepted.')
