#!/usr/bin/env python3
"""Preserve wide power routing while finishing fine-pitch pad escapes."""
from pathlib import Path
import pcbnew as p,re
ROOT=Path(__file__).resolve().parents[1]
b=p.LoadBoard(str(ROOT/'gdep133c02-driver.kicad_pcb'))
for t in b.GetTracks():
 if not isinstance(t,p.PCB_VIA) and t.GetWidth()<p.FromMM(.2):t.SetWidth(p.FromMM(.2))
 t.SetLocked(True)
p.SaveBoard(str(ROOT/'gdep133c02-driver.kicad_pcb'),b)
p.ExportSpecctraDSN(b,str(ROOT/'reports/fanout.dsn'))
path=ROOT/'reports/fanout.dsn';s=path.read_text();s=re.sub(r'\(width (?:500|600|800)\)','(width 200)',s);path.write_text(s)
