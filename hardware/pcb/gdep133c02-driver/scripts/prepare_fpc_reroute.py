#!/usr/bin/env python3
"""Re-route the connector fanout while retaining power converter core routing."""
from pathlib import Path
import re,math
import pcbnew as p
ROOT=Path(__file__).resolve().parents[1];path=ROOT/'gdep133c02-driver.kicad_pcb';s=path.read_text()
def drop(m):
 b=m.group();net=re.search(r'\(net "([^"]+)"\)',b).group(1)
 coords=re.findall(r'\((?:at|start|end) ([\d.-]+) ([\d.-]+)\)',b)
 if net=='GND' and b.startswith('\t(segment'):return ''
 if any(78<float(x)<124 and 50<float(y)<70 for x,y in coords):return ''
 return b
s=re.sub(r'(?ms)^\t\((?:segment|via)\b.*?^\t\)\n',drop,s);path.write_text(s)
b=p.LoadBoard(str(path));p.ExportSpecctraDSN(b,str(ROOT/'reports/fpc-reroute.dsn'))
dsn=ROOT/'reports/fpc-reroute.dsn';s=dsn.read_text()
s=re.sub(r'\(width (?:500|600)\)','(width 200)',s)
# DSN plane polygons are idealized outlines. Only expose the truly continuous
# internal plane to the router; surface pours will be refilled by KiCad later.
s=re.sub(r'(?ms)^    \(plane GND \(polygon (?:F.Cu|B.Cu)\b.*?\)\)\n','',s)
dsn.write_text(s)
