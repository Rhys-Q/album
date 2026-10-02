#!/usr/bin/env python3
"""Use Xunpu Rev A 0.5 pitch / H2.0 land dimensions; retain mating check gate."""
from pathlib import Path
import json,re
import pcbnew as p
ROOT=Path(__file__).resolve().parents[1]
old='FPC_05FB_60PH20_UNVERIFIED';new='FPC_05FB_60PH20'
fp=ROOT/'lib/Driver.pretty'/f'{old}.kicad_mod';s=fp.read_text().replace(old,new).replace('UNVERIFIED placeholder: exact Xunpu drawing required. DO NOT FABRICATE','Xunpu FPC-05FB-NPH20 Rev A; 60 pins. Mating direction requires physical verification').replace('(size .3 1.6)','(size .3 1.2)').replace('(at -16.4 0) (size 2 2.4)','(at -16.3 5.75) (size 2 1.8)').replace('(at 16.4 0) (size 2 2.4)','(at 16.3 5.75) (size 2 1.8)').replace('(start -17.5 -2) (end 17.5 3.6)','(start -16.75 2.7) (end 16.75 7.6)').replace('(start -18.0 -2.5) (end 18.0 4.1)','(start -17.55 1.65) (end 17.55 7.85)').replace('DRAWING REQUIRED','FPC-05FB-60PH20')
(ROOT/'lib/Driver.pretty'/f'{new}.kicad_mod').write_text(s)
# Correct courtyard/fab on board from library; keep symbol path, properties and pads.
b=p.LoadBoard(str(ROOT/'gdep133c02-driver.kicad_pcb'))
f=next(f for f in b.GetFootprints() if f.GetReference()=='FPC1');f.SetFPID(p.LIB_ID('Driver',new))
for pad in f.Pads():
 if pad.GetNumber() in ['61','62']:
  pad.SetPosition(p.VECTOR2I(p.FromMM(100+(-16.3 if pad.GetNumber()=='61' else 16.3)),p.FromMM(60.75)))
for g in f.GraphicalItems():
 if g.GetLayer()==p.F_Fab:a,bx=(-16.75,2.7),(16.75,7.6)
 elif g.GetLayer()==p.F_CrtYd:a,bx=(-17.55,1.65),(17.55,7.85)
 else:continue
 g.SetStart(p.VECTOR2I(p.FromMM(100+a[0]),p.FromMM(55+a[1])))
 g.SetEnd(p.VECTOR2I(p.FromMM(100+bx[0]),p.FromMM(55+bx[1])))
p.SaveBoard(str(ROOT/'gdep133c02-driver.kicad_pcb'),b)
for path in [ROOT/'panel.kicad_sch',ROOT/'lib/Driver.kicad_sym']:
 path.write_text(path.read_text().replace(old,new))
path=ROOT/'design-data.json';d=json.loads(path.read_text())
for part in d['parts']:
 if part['ref']=='FPC1':part['fp']='Driver:'+new
# Footprint dimensions checked; contact mapping is a separate physical gate.
d['fpc_footprint_verified']=True;d['fpc_mating_verified']=False
path.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
