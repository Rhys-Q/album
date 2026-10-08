#!/usr/bin/env python3
"""One-time native board migration; final routed board is authoritative."""
from pathlib import Path
import pcbnew as p
from schematic_sexp import parse,kids,one
R=Path(__file__).resolve().parents[1];BOARD=R/'gdep133c02-driver.kicad_pcb';b=p.LoadBoard(str(BOARD));assert not any(f.GetReference()=='R49' for f in b.GetFootprints()),'Already applied'
ng=p.NETINFO_ITEM(b,'Q7_GATE');b.Add(ng);nc=b.FindNet('GDRC')
for f in b.GetFootprints():
 if f.GetReference() in ['Q7','R13']:
  for q in f.Pads():
   if q.GetNetname()=='GDRC':q.SetNet(ng)
for t in list(b.GetTracks()):
 if t.m_Uuid.AsString()=='4c8fe7e3-18c7-42d1-ba92-909900c914aa':b.Delete(t);continue
 if t.GetNetname()=='GDRC' and not isinstance(t,p.PCB_VIA):
  aa,cc=t.GetStart(),t.GetEnd()
  if min(p.ToMM(aa.x),p.ToMM(cc.x))>=109.8:t.SetNet(ng)
a=parse((R/'power.kicad_sch').read_text());sy={next(z[2] for z in kids(s,'property') if z[1]=='Reference'):s for s in kids(a,'symbol')}
def point(x,y):return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
def add(ref,fp,x,y,value,nets,dnp=False):
 f=p.FootprintLoad(str(R/'lib/Driver.pretty'),fp);f.SetReference(ref);f.SetValue(value);f.SetFPID(p.LIB_ID('Driver',fp));f.SetPosition(point(x,y));s=sy[ref];path=one(one(one(s,'instances'),'project'),'path')[1];f.SetPath(p.KIID_PATH('/'+'/'.join(str(path).strip('/').split('/')[1:])+'/'+str(one(s,'uuid')[1])));f.SetDNP(dnp);f.SetExcludedFromBOM(dnp)
 props={z[1]:z[2] for z in kids(s,'property')}
 for k in ['MPN','Manufacturer','Datasheet']:f.SetField(k,str(props[k]))
 f.Reference().SetTextSize(point(.8,.8));f.Reference().SetTextThickness(p.FromMM(.12));f.Reference().SetPosition(point(x,y-1.7));f.Value().SetVisible(False);b.Add(f)
 for q in f.Pads():q.SetNet(nets[q.GetNumber()])
 return {q.GetNumber():q.GetPosition() for q in f.Pads()}
r=add('R49','Resistor_SMD__R_0805_2012Metric',108.9,94,'0 ohm',{'1':nc,'2':ng})
tp25=add('TP25','TestPoint__TestPoint_Pad_D1.5mm',106.2,94.8,'GDRC',{'1':nc},True)
tp26=add('TP26','TestPoint__TestPoint_Pad_D1.5mm',111.1,92.5,'Q7_GATE',{'1':ng},True)
for t in b.GetTracks():
 if t.m_Uuid.AsString()=='fd6ed77c-9766-417b-aa92-0c143e37a632':t.SetEnd(r['1'])
def track(n,aa,cc):
 t=p.PCB_TRACK(b);t.SetNet(n);t.SetStart(aa);t.SetEnd(cc);t.SetLayer(p.F_Cu);t.SetWidth(p.FromMM(.2));b.Add(t)
track(ng,r['2'],point(109.825,94));track(nc,tp25['1'],point(107.435,93.2597));track(ng,tp26['1'],point(109.825,94))
b.GetTitleBlock().SetRevision('0.5-GDRC-DEBUG');b.BuildConnectivity();fill=p.ZONE_FILLER(b);assert fill.Fill(b.Zones());p.SaveBoard(str(BOARD),b);print('Added and routed; unconnected',b.GetConnectivity().GetUnconnectedCount(False))
