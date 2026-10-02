#!/usr/bin/env python3
from pathlib import Path
import pcbnew as p
ROOT=Path(__file__).resolve().parents[1]
b=p.LoadBoard(str(ROOT/'gdep133c02-driver.kicad_pcb'))
existing={z.GetLayer() for z in b.Zones() if z.GetNetname()=='GND'}
for layer in [p.F_Cu,p.B_Cu]:
 if layer in existing:continue
 z=p.ZONE(b);z.SetLayer(layer);z.SetNet(b.FindNet('GND'));z.SetLocalClearance(p.FromMM(.25));z.SetMinThickness(p.FromMM(.2));z.SetPadConnection(p.ZONE_CONNECTION_THT_THERMAL);z.SetThermalReliefGap(p.FromMM(.3));z.SetThermalReliefSpokeWidth(p.FromMM(.5));z.Outline().NewOutline()
 for x,y in [(51,51),(149,51),(149,129),(51,129)]:z.Outline().Append(p.FromMM(x),p.FromMM(y))
 b.Add(z)
p.SaveBoard(str(ROOT/'gdep133c02-driver.kicad_pcb'),b)
