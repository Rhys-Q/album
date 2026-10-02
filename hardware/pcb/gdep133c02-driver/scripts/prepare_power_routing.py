#!/usr/bin/env python3
"""Reserve GND layer and export width classes for local native routing."""
from pathlib import Path
import json,re
import pcbnew as p
ROOT=Path(__file__).resolve().parents[1]
b=p.LoadBoard(str(ROOT/'gdep133c02-driver.kicad_pcb'))
z=p.ZONE(b);z.SetLayer(p.In1_Cu);z.SetNet(b.FindNet('GND'));z.SetLocalClearance(p.FromMM(.25));z.SetMinThickness(p.FromMM(.2));z.SetPadConnection(p.ZONE_CONNECTION_FULL)
z.Outline().NewOutline()
for x,y in [(51,51),(149,51),(149,129),(51,129)]:z.Outline().Append(p.FromMM(x),p.FromMM(y))

if not list(b.Zones()):b.Add(z)
p.SaveBoard(str(ROOT/'gdep133c02-driver.kicad_pcb'),b)
p.ExportSpecctraDSN(b,str(ROOT/'reports/power-reroute.dsn'))
# DSN classes are also entered into the native project's net classes.
groups={'InputPower':(.8,['BENCH_3V3','VIN','SW_IN','SW_OUT','AVDD_PRE','AVDD_CAP','EPD_VDD','EPD_3V3','SW_ON']),
'PanelPower':(.5,['AVDD','VDD','VDDIO','VDDP','VDDN','VDDN_RAW','VBB_3P5V','VNCP_3P5V','LX','SW_N','SW_VCOM','RESEP','SENSE_N','SENSE_VCOM']),
'Ground':(.6,['GND'])}
path=ROOT/'reports/power-reroute.dsn';s=path.read_text();start=s.index('    (class kicad_default');stop=s.index('      (circuit',start)
head=s[start:stop]
for _,(_,nets) in groups.items():
 for n in nets:head=re.sub(r'(?<![\w-])'+re.escape(n)+r'(?![\w-])','',head)
s=s[:start]+head+s[stop:]
idx=s.index('  (wiring')
extra=''
for name,(width,nets) in groups.items():
 extra+='    (class '+name+' '+' '.join(nets)+' (circuit (use_via "Via[0-3]_600:300_um")) (rule (width '+str(int(width*1000))+') (clearance 200)))\n'
# Insert before network's closing parenthesis.
s=s[:idx-4]+extra+s[idx-4:]
path.write_text(s)
propath=ROOT/'gdep133c02-driver.kicad_pro';pro=json.loads(propath.read_text());ns=pro['net_settings'];ns['netclass_patterns']=[]
ns['classes']=[c for c in ns['classes'] if c['name'] not in groups]
for name,(width,nets) in groups.items():
 ns['classes'].append({'name':name,'clearance':.2,'track_width':width,'via_diameter':.6,'via_drill':.3,'microvia_diameter':.3,'microvia_drill':.1,'diff_pair_width':.2,'diff_pair_gap':.25,'diff_pair_via_gap':.25,'pcb_color':'rgba(0, 0, 0, 0.000)','schematic_color':'rgba(0, 0, 0, 0.000)','wire_width':6,'bus_width':12})
 for n in nets:ns['netclass_patterns'].append({'netclass':name,'pattern':n})
propath.write_text(json.dumps(pro,indent=2)+'\n')
