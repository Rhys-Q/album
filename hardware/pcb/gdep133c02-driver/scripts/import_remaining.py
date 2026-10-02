#!/usr/bin/env python3
"""Append DRC-verifiable native segments using explicit net names."""
from pathlib import Path
import json,uuid
ROOT=Path(__file__).resolve().parents[1];path=ROOT/'gdep133c02-driver.kicad_pcb';text=path.read_text();names=json.loads((ROOT/'reports/remaining-nets.json').read_text());lines=iter((ROOT/'reports/remaining-paths.txt').read_text().splitlines());out=[];layers=['F.Cu','In2.Cu','B.Cu'];nseg=nvia=0;seen=set()
for head in lines:
 if not head:continue
 _,code,count=head.split();name=names[code];pts=[]
 for _ in range(int(count)):
  x,y,l=next(lines).split();pts.append((float(x)+50,float(y)+50,int(l)))
 keep=[pts[0]]
 for i in range(1,len(pts)-1):
  a,b,c=pts[i-1],pts[i],pts[i+1]
  if a[2]==b[2]==c[2] and abs((b[0]-a[0])*(c[1]-b[1])-(b[1]-a[1])*(c[0]-b[0]))<1e-8:continue
  keep.append(b)
 keep.append(pts[-1])
 for a,c in zip(keep,keep[1:]):
  uid=str(uuid.uuid4())
  if a[2]!=c[2]:
   key=(name,a[0],a[1])
   if key in seen:continue
   seen.add(key);nvia+=1
   out.append(f'\t(via (at {a[0]:.4f} {a[1]:.4f}) (size 0.6) (drill 0.3) (layers "F.Cu" "B.Cu") (net "{name}") (uuid "{uid}"))\n')
  elif a[:2]!=c[:2]:
   nseg+=1;out.append(f'\t(segment (start {a[0]:.4f} {a[1]:.4f}) (end {c[0]:.4f} {c[1]:.4f}) (width 0.2) (layer "{layers[a[2]]}") (net "{name}") (uuid "{uid}"))\n')
# Canonical position before zones; loader will normalize formatting on save.
i=text.index('\t(zone\n');text=text[:i]+''.join(out)+text[i:];path.write_text(text);print(nseg,'segments and',nvia,'vias')
