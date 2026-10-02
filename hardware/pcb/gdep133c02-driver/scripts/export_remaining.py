#!/usr/bin/env python3
from pathlib import Path
import json
import pcbnew as p
ROOT=Path(__file__).resolve().parents[1];b=p.LoadBoard(str(ROOT/'gdep133c02-driver.kicad_pcb'));layers={p.F_Cu:0,p.In2_Cu:1,p.B_Cu:2};lines=[]
for f in b.GetFootprints():
 for pad in f.Pads():
  bb=pad.GetBoundingBox();pos=pad.GetPosition();tht=pad.GetAttribute() in [p.PAD_ATTRIB_PTH,p.PAD_ATTRIB_NPTH];net=pad.GetNetCode() if pad.GetNetCode() else -10000
  lines.append(f'P {net} {p.ToMM(pos.x)-50} {p.ToMM(pos.y)-50} {p.ToMM(bb.GetWidth())} {p.ToMM(bb.GetHeight())} {int(tht)}')
  if tht:lines.append(f'H {p.ToMM(pos.x)-50} {p.ToMM(pos.y)-50} {p.ToMM(pad.GetDrillSize().x)}')
for t in b.GetTracks():
 n=t.GetNetCode();width=p.ToMM(t.GetWidth(p.F_Cu) if isinstance(t,p.PCB_VIA) else t.GetWidth())
 if isinstance(t,p.PCB_VIA):
  q=t.GetPosition();lines.append(f'P {n} {p.ToMM(q.x)-50} {p.ToMM(q.y)-50} {width} {width} 1');lines.append(f'H {p.ToMM(q.x)-50} {p.ToMM(q.y)-50} {p.ToMM(t.GetDrill())}');continue
 if t.GetLayer() not in layers:continue
 a,c=t.GetStart(),t.GetEnd();lines.append(f'T {n} {layers[t.GetLayer()]} {p.ToMM(a.x)-50} {p.ToMM(a.y)-50} {p.ToMM(c.x)-50} {p.ToMM(c.y)-50} {width}')
jobs={}
for netname,xy,ref,pin in [('AVDD',(85.372,62.4257),'C12','1'),('VGL',(115.3098,56.5983),'C21','1')]:
 net=b.FindNet(netname).GetNetCode();jobs[net]=netname
 lines.append(f'S {net} {xy[0]-50} {xy[1]-50} 2 {net}')
 f=next(f for f in b.GetFootprints() if f.GetReference()==ref)
 pad=next(pad for pad in f.Pads() if pad.GetNumber()==pin);q=pad.GetPosition()
 lines.append(f'E {net} {p.ToMM(q.x)-50} {p.ToMM(q.y)-50} 0')
net=b.FindNet('GND').GetNetCode();jobs[net]='GND'
groundvias=[t for t in b.GetTracks() if isinstance(t,p.PCB_VIA) and t.GetNetname()=='GND']
for v in groundvias:
 q=v.GetPosition()
 for l in [0,1,2]:lines.append(f'E {net} {p.ToMM(q.x)-50} {p.ToMM(q.y)-50} {l}')
for z in b.Zones():
 if z.GetLayer()!=p.F_Cu:continue
 poly=z.GetFilledPolysList(p.F_Cu)
 for idx in range(poly.OutlineCount()):
  if any(any(poly.Contains(v.GetPosition()+p.VECTOR2I(p.FromMM(dx),p.FromMM(dy)),idx) for dx,dy in [(.24,0),(-.24,0),(0,.24),(0,-.24)]) for v in groundvias):continue
  box=poly.COutline(idx).BBox();opts=[]
  x0,y0=p.ToMM(box.GetX()),p.ToMM(box.GetY());x1,y1=p.ToMM(box.GetRight()),p.ToMM(box.GetBottom())
  for ix in range(int(x0*4),int(x1*4)+1):
   for iy in range(int(y0*4),int(y1*4)+1):
    x,y=ix/4,iy/4
    if all(poly.Contains(p.VECTOR2I(p.FromMM(x+dx),p.FromMM(y+dy)),idx) for dx,dy in [(0,0),(.12,0),(-.12,0),(0,.12),(0,-.12)]):
     dist=min((x-p.ToMM(v.GetPosition().x))**2+(y-p.ToMM(v.GetPosition().y))**2 for v in groundvias)
     opts.append((dist,x,y))
  if opts:
   
   for _,x,y in sorted(opts)[:25]:lines.append(f'S {net} {x-50} {y-50} 0 {100+idx}')
   print('Ground island',idx,'candidate sources',min(25,len(opts)))
(ROOT/'reports/remaining-input.txt').write_text('\n'.join(lines)+'\n');(ROOT/'reports/remaining-nets.json').write_text(json.dumps(jobs,indent=2)+'\n')
