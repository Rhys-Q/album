#!/usr/bin/env python3
"""Export/import explicit native DRC missing connections; DRC remains authoritative.
Run using bundled KiCad Python: export REPORT signal|power; import PATHS WIDTH.
The conservative grid router uses 0.2 mm signal / 0.5 mm repaired supply tracks.
"""
from pathlib import Path
import pcbnew as p,json,sys
R=Path(__file__).resolve().parents[1];D=R/'reports/hand-solder-v0.3';path=R/'gdep133c02-driver.kicad_pcb';b=p.LoadBoard(str(path));layers={p.F_Cu:0,p.In2_Cu:1,p.B_Cu:2};ly=[p.F_Cu,p.In2_Cu,p.B_Cu]
def xy(q):return p.ToMM(q.x)-50,p.ToMM(q.y)-50
if sys.argv[1]=='export':
 j=json.loads(Path(sys.argv[2]).read_text());kind=sys.argv[3];lines=[];objects={}
 for f in b.GetFootprints():
  for pad in f.Pads():
   objects[pad.m_Uuid.AsString()]=pad;bb=pad.GetBoundingBox();x,y=xy(pad.GetPosition());tht=pad.GetAttribute() in [p.PAD_ATTRIB_PTH,p.PAD_ATTRIB_NPTH];n=pad.GetNetCode() or -10000
   lines.append(f'P {n} {x} {y} {p.ToMM(bb.GetWidth())} {p.ToMM(bb.GetHeight())} {int(tht)}')
   if tht:lines.append(f'H {x} {y} {p.ToMM(pad.GetDrillSize().x)}')
 for t in b.GetTracks():
  objects[t.m_Uuid.AsString()]=t;n=t.GetNetCode();width=p.ToMM(t.GetWidth(p.F_Cu) if isinstance(t,p.PCB_VIA) else t.GetWidth())
  if isinstance(t,p.PCB_VIA):
   x,y=xy(t.GetPosition());lines.append(f'P {n} {x} {y} {width} {width} 1');lines.append(f'H {x} {y} {p.ToMM(t.GetDrill())}');continue
  if t.GetLayer() in layers:
   x,y=xy(t.GetStart());xx,yy=xy(t.GetEnd());lines.append(f'T {n} {layers[t.GetLayer()]} {x} {y} {xx} {yy} {width}')
 count=0;b.BuildConnectivity();connect=b.GetConnectivity()
 def component(item):
  queue=[item];seen={};
  while queue:
   z=queue.pop();uid=z.m_Uuid.AsString()
   if uid in seen:continue
   seen[uid]=z
   queue.extend(w for w in connect.GetConnectedItems(z) if isinstance(w,(p.PAD,p.PCB_TRACK)))
  return sorted(seen.values(),key=lambda z:0 if isinstance(z,p.PAD) else 1 if isinstance(z,p.PCB_VIA) else 2)
 for group,v in enumerate(j['unconnected_items']):
  a,c=[objects[i['uuid']] for i in v['items']];n=a.GetNetCode();power=a.GetNetname() in ['BENCH_3V3','VIN']
  if power!=(kind=='power'):continue
  for cmd,item in [(cmd,item) for cmd,root in [('S',a),('E',c)] for item in component(root)]:
   qs=[item.GetEnd(),item.GetStart()] if isinstance(item,p.PCB_TRACK) and not isinstance(item,p.PCB_VIA) else [item.GetPosition()]
   if len(qs)==2:
    aa,cc=qs;qs += [p.VECTOR2I(round(aa.x+(cc.x-aa.x)*t/20),round(aa.y+(cc.y-aa.y)*t/20)) for t in range(1,20)]
   for q in qs:
    x,y=xy(q);l=layers.get(item.GetLayer(),0);lines.append(f'{cmd} {n} {x} {y} {l} {group}')
  count+=1
 (D/f'route-{kind}-input.txt').write_text('\n'.join(lines)+'\n');print(kind,count,'jobs')
else:
 lines=iter(Path(sys.argv[2]).read_text().splitlines());width=float(sys.argv[3]);seen=set();nseg=nvia=0
 def vec(a):return p.VECTOR2I(p.FromMM(a[0]+50),p.FromMM(a[1]+50))
 for head in lines:
  _,n,count=head.split();n=int(n);pts=[]
  for _ in range(int(count)):
   x,y,l=next(lines).split();pts.append((float(x),float(y),int(l)))
  keep=[pts[0]]
  for i in range(1,len(pts)-1):
   a,c,d=pts[i-1:i+2]
   if a[2]==c[2]==d[2] and abs((c[0]-a[0])*(d[1]-c[1])-(c[1]-a[1])*(d[0]-c[0]))<1e-8:continue
   keep.append(c)
  keep.append(pts[-1])
  for a,c in zip(keep,keep[1:]):
   if a[2]!=c[2]:
    key=(n,a[0],a[1])
    if key in seen:continue
    seen.add(key);v=p.PCB_VIA(b);v.SetNetCode(n);v.SetPosition(vec(a));v.SetWidth(p.FromMM(.6));v.SetDrill(p.FromMM(.3));v.SetLayerPair(p.F_Cu,p.B_Cu);b.Add(v);nvia+=1
   elif a[:2]!=c[:2]:
    t=p.PCB_TRACK(b);t.SetNetCode(n);t.SetStart(vec(a));t.SetEnd(vec(c));t.SetWidth(p.FromMM(width));t.SetLayer(ly[a[2]]);b.Add(t);nseg+=1
 b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(path),b);print(nseg,'segments',nvia,'vias')
