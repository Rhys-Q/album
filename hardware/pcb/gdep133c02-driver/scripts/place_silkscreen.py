#!/usr/bin/env python3
"""Move assembly outlines that collide to Fab and place readable reference marks."""
import json,math
from pathlib import Path
import pcbnew as p
ROOT=Path(__file__).resolve().parents[1]
b=p.LoadBoard(str(ROOT/'gdep133c02-driver.kicad_pcb'))
report=json.loads(Path('/tmp/album-placement-drc.json').read_text())
bad={i['uuid'] for v in report['violations'] if v['type'] in ['silk_overlap','silk_over_copper'] for i in v['items']}
obstacles=[]
def bb(item,margin=0):
 q=item.GetBoundingBox();return (p.ToMM(q.GetX())-margin,p.ToMM(q.GetY())-margin,p.ToMM(q.GetRight())+margin,p.ToMM(q.GetBottom())+margin)
for f in b.GetFootprints():
 for g in f.GraphicalItems():
  if str(g.m_Uuid) in bad and g.GetLayer()==p.F_SilkS:g.SetLayer(p.F_Fab)
  if g.GetLayer()==p.F_SilkS:obstacles.append(bb(g,.2))
 for pad in f.Pads():obstacles.append(bb(pad,.22))
 if f.GetReference().startswith('H'):obstacles.append(bb(f,.2))
for t in b.GetDrawings():
 if isinstance(t,p.PCB_TEXT) and t.GetLayer()==p.F_SilkS:
  # General instructions go on back; front keeps individual identifiers.
  t.SetLayer(p.B_SilkS);t.SetMirrored(True)
  if 'NOT VERIFIED' in t.GetText():t.SetText('FPC PIN1 / CONTACT: VERIFY MATING')
placed=[]
for f in sorted(b.GetFootprints(),key=lambda f:(not f.GetReference().startswith('FPC'),f.GetReference())):
 if f.GetReference().startswith('H'):continue
 r=f.Reference();r.SetTextSize(p.VECTOR2I(p.FromMM(1),p.FromMM(1)));r.SetTextThickness(p.FromMM(.15));r.SetTextAngle(p.EDA_ANGLE(0,p.DEGREES_T));r.SetLayer(p.F_SilkS)
 pos=f.GetPosition();cx,cy=p.ToMM(pos.x),p.ToMM(pos.y);w=.72*len(f.GetReference())+.25;h=1.25
 options=[]
 for dx in range(-16,17):
  for dy in range(-16,17):
   x,y=cx+dx*.5,cy+dy*.5;rr=(x-w/2,y-h/2,x+w/2,y+h/2)
   if rr[0]<51 or rr[1]<51 or rr[2]>149 or rr[3]>129:continue
   if any(rr[0]<a[2] and rr[2]>a[0] and rr[1]<a[3] and rr[3]>a[1] for a in obstacles+placed):continue
   options.append((dx*dx+dy*dy+.1*abs(dx),x,y,rr))
 if not options:raise RuntimeError('No readable reference position for '+f.GetReference())
 _,x,y,rr=min(options);r.SetPosition(p.VECTOR2I(p.FromMM(x),p.FromMM(y)));r.SetVisible(True);placed.append((rr[0]-.2,rr[1]-.2,rr[2]+.2,rr[3]+.2))
p.SaveBoard(str(ROOT/'gdep133c02-driver.kicad_pcb'),b)
print('Placed',len(placed),'reference labels without covering pads')
