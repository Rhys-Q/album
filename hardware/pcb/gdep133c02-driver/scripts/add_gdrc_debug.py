#!/usr/bin/env python3
"""One-time v0.4 -> v0.5 schematic migration. Native sources remain authoritative."""
from pathlib import Path
from copy import deepcopy
import json,uuid,math,shutil
from schematic_sexp import Q,parse,dump,kids,one
R=Path(__file__).resolve().parents[1]
data=json.loads((R/'design-data.json').read_text())
assert data['revision']=='0.4-direct-p1','Already applied or incompatible source revision'
def uid():return Q(str(uuid.uuid4()))
def prop(s,k,v):next(x for x in kids(s,'property') if x[1]==k)[2]=Q(v)
def wire(a,b):return parse(f'(wire(pts(xy {a[0]} {a[1]})(xy {b[0]} {b[1]}))(stroke(width 0)(type default))(uuid "{uuid.uuid4()}"))')
def label(n,x,y):return parse(f'(global_label "{n}"(shape bidirectional)(at {x} {y} 0)(effects(font(size .9 .9))(justify left))(uuid "{uuid.uuid4()}")(property "Intersheetrefs" ""(at {x} {y} 0)(effects(font(size .9 .9))(hide yes))))')
a=parse((R/'power.kicad_sch').read_text());it=parse((R/'interface.kicad_sch').read_text());lib=parse((R/'lib/Driver.kicad_sym').read_text());rootid=one(parse((R/'gdep133c02-driver.kicad_sch').read_text()),'uuid')[1]
sheetid=next(one(one(one(s,'instances'),'project'),'path')[1] for s in kids(a,'symbol') if any(x[1]=='Reference' and x[2]=='Q7' for x in kids(s,'property')))
def clone(ref,new,x,y,angle,value,fp,mpn,maker):
 src=a if ref=='R13' else it
 sy=deepcopy(next(s for s in kids(src,'symbol') if any(z[1]=='Reference' and z[2]==ref for z in kids(s,'property'))))
 oldlib=one(sy,'lib_id')[1];dd=deepcopy(next(d for d in kids(one(src,'lib_symbols'),'symbol') if d[1]==oldlib))
 dd[1]=Q('Driver:P_'+new)
 for c in kids(dd,'symbol'):c[1]=Q(str(c[1]).replace('P_'+ref,'P_'+new))
 for k,v in [('Value',value),('Footprint','Driver:'+fp)]:prop(dd,k,v)
 one(a,'lib_symbols').append(dd);lib.append(deepcopy(dd));one(sy,'lib_id')[1]=Q('Driver:P_'+new);one(sy,'uuid')[1]=uid();one(sy,'at')[1:]=[str(x),str(y),str(angle)]
 for k,v in [('Reference',new),('Value',value),('Footprint','Driver:'+fp),('MPN',mpn),('Manufacturer',maker),('Datasheet','')]:prop(sy,k,v)
 for z in kids(sy,'property'):one(z,'at')[1:]=[str(x),str(y-7.62 if z[1]=='Reference' else y-3.81 if z[1]=='Value' else y),'0']
 for pin in kids(sy,'pin'):one(pin,'uuid')[1]=uid()
 path=one(one(one(sy,'instances'),'project'),'path');path[1]=Q(sheetid);one(path,'reference')[1]=Q(new)
 a.append(sy);return sy
for l in kids(a,'global_label'):
 if l[1]=='GDRC':l[1]=Q('Q7_GATE')
# Existing right-hand gate label becomes controller side, with R49 inserted in its wire.
right=next(l for l in kids(a,'global_label') if l[1]=='Q7_GATE' and float(one(l,'at')[2])==198.12);right[1]=Q('GDRC')
for w in list(kids(a,'wire')):
 pts=[tuple(map(float,z[1:])) for z in one(w,'pts')[1:]]
 if pts==[(473.71,198.12),(492.76,198.12)]:a.remove(w)
sy=clone('R13','R49',480.06,198.12,270,'0 ohm','Resistor_SMD__R_0805_2012Metric','RC0805JR-070RL','Yageo')
a.extend([wire((473.71,198.12),(476.25,198.12)),wire((483.87,198.12),(492.76,198.12))])
for ref,net,y in [('TP25','GDRC',170.18),('TP26','Q7_GATE',195.58)]:
 clone('TP1',ref,563.88,y,0,net,'TestPoint__TestPoint_Pad_D1.5mm','PCB test pad','PCB');a.append(label(net,563.88,y+2.54))
(R/'lib/Driver.kicad_sym').write_text(dump(lib)+'\n');(R/'power.kicad_sch').write_text(dump(a)+'\n')
for name in ['power','panel','interface','gdep133c02-driver']:
 f=R/(name+'.kicad_sch');s=parse(f.read_text());t=one(s,'title_block');one(t,'rev')[1]=Q('0.5-GDRC-DEBUG');f.write_text(dump(s)+'\n')
parts={p['ref']:p for p in data['parts']};parts['Q7']['pins']['1']='Q7_GATE';parts['R13']['pins']['2']='Q7_GATE'
for ref,template,value,fp,mpn,maker,pins,xy in [('R49','R13','0 ohm','Resistor_SMD:R_0805_2012Metric','RC0805JR-070RL','Yageo',{'1':'GDRC','2':'Q7_GATE'},[58.9,44]),('TP25','TP1','GDRC','TestPoint:TestPoint_Pad_D1.5mm','PCB test pad','PCB',{'1':'GDRC'},[56.2,44.8]),('TP26','TP1','Q7_GATE','TestPoint:TestPoint_Pad_D1.5mm','PCB test pad','PCB',{'1':'Q7_GATE'},[61.1,42.5])]:
 p=deepcopy(parts[template]);p.update(ref=ref,value=value,fp=fp,mpn=mpn,vendor=maker,pins=pins,xy=xy,group='converters' if ref=='R49' else 'test',uuid=str(uuid.uuid4()),url='',names={},types={});data['parts'].append(p)
data['revision']='0.5-gdrc-debug';(R/'design-data.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
# Localize official KiCad 0805 footprint and its model.
base=Path('/Applications/KiCad/KiCad.app/Contents/SharedSupport');f=base/'footprints/Resistor_SMD.pretty/R_0805_2012Metric.kicad_mod';s=f.read_text().replace('(footprint "R_0805_2012Metric"','(footprint "Resistor_SMD__R_0805_2012Metric"').replace('${KICAD10_3DMODEL_DIR}/Resistor_SMD.3dshapes/','${KIPRJMOD}/models/');(R/'lib/Driver.pretty/Resistor_SMD__R_0805_2012Metric.kicad_mod').write_text(s);shutil.copy2(base/'3dmodels/Resistor_SMD.3dshapes/R_0805_2012Metric.step',R/'models/R_0805_2012Metric.step')
print('Added R49, TP25, TP26; R13 remains on Q7_GATE')
