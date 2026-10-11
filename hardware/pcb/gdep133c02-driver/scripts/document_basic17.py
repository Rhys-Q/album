#!/usr/bin/env python3
"""Document the user-selected prototype revision, without asserting performance equivalence."""
import csv,json,math,re
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=json.loads((R/'design-data.json').read_text());P={p['ref']:p for p in D['parts']};proof=json.loads((R/'reports/procurement-v011.json').read_text());A=json.loads((R/'reports/basic-library-recheck-2026-10-11/group-review.json').read_text());products=json.loads((R/'reports/basic-library-recheck-2026-10-11/products.json').read_text());refresh=json.loads((R/'reports/stock-refresh-v011.json').read_text())if(R/'reports/stock-refresh-v011.json').exists()else{};old={p['ref']:p for p in json.loads((R/'reports/baseline-design-v010.json').read_text())['parts']}
# Keep unchanged-model commercial data as dated historical evidence, not live inventory.
for row in csv.DictReader((R/'docs/采购清单-v0.10.csv').open(encoding='utf-8-sig')):
 code=row.get('当前C号')or row.get('候选C号')
 if not code or code in products:continue
 def number(k):
  try:return int(row[k])
  except(ValueError,KeyError):return None
 ratio=number('购买倍数只');tiers=[{'startPurchasedNumber':int(q)/(ratio or 1),'productPrice':float(v)}for q,v in re.findall(r'(\d+)(?:\+|只起):([0-9.]+)',row.get('商城人民币阶梯',''))]
 minimum=number('MOQ只')
 products[code]={'code':code,'query_status':'HISTORICAL v0.10 snapshot','queried_at':row.get('商城查询时间')or row.get('查询时间',''),'url':row.get('采购链接',''),'domestic':{'smtLabel':row.get('国内库类别',''),'retail_stock':number('商城库存只'),'smt_stock':number('SMT库存只'),'theRatio':ratio,'minBuyNumber':minimum/(ratio or 1)if minimum else None},'pricing':{'theRatio':ratio,'productPriceList':tiers}}
def write(name,rows):
 with (R/'docs'/name).open('w',encoding='utf-8-sig',newline='')as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
rows=[]
for ref in proof['changed_refs']:
 p=P[ref];o=old.get(ref,{});rows.append(dict(位号=ref,原型号=o.get('mpn','新增'),原C号=o.get('lcsc',''),原封装=o.get('fp',''),本版型号=p['mpn'],本版C号=p['lcsc'],本版参数=p['value'],本版封装=p['fp'],电路网络=';'.join(p['pins'].values()),用户决定=p['exception_decision'],未验证项=p['selection_note']))
write('逐位号替换对照-v0.11.csv',rows)
groups={}
for p in D['parts']:
 if not p['dnp']:groups.setdefault(p['lcsc'],[]).append(p)
rows=[]
for code,ps in sorted(groups.items()):
 z=ps[0];x=products.get(code,{});fresh=refresh.get(code,{});good=fresh if fresh.get('query_status')=='OK'else x;dom=good.get('domestic')or{};pr=good.get('pricing')or{};ratio=pr.get('theRatio')or dom.get('theRatio');minimum=dom.get('minBuyNumber');tiers=pr.get('productPriceList')or[];qt=good.get('queried_at','');r=dict(C编号=code,型号=z['mpn'],品牌=z['vendor'],位号=','.join(p['ref']for p in ps),每板数量=len(ps),封装=z['fp'],装配方式='手工'if z['ref']in ['J1','J2']else'机器SMT',国内库类别=dom.get('smtLabel',z.get('library_category','未知')),商城库存=dom.get('retail_stock',''),SMT库存=dom.get('smt_stock')if dom.get('smt_stock')is not None else'未知',有效查询时间=qt,本次刷新状态=fresh.get('query_status','未刷新；历史记录'),采购倍数=ratio or'',MOQ只=minimum*ratio if minimum and ratio else'',商城人民币阶梯=';'.join(f"{t['startPurchasedNumber']*ratio}只起:{t['productPrice']}"for t in tiers)if ratio else'',SMT单价='',SMT采购费用='',采购链接=good.get('url',''),原厂资料=z['url'],审查状态=z.get('exception_decision','保持原件'),新增换料费估算='0（按国内基础库标签，订单重核）'if '基础库'in (dom.get('smtLabel')or'')else'未知或扩展库20元/型号/订单，订单重核')
 for boards,spares in [(1,0),(1,2),(5,0),(5,2)]:
  need=len(ps)*boards+spares;buy=math.ceil(max(need,(minimum or 1)*(ratio or 1))/(ratio or 1))*(ratio or 1)if ratio else None;valid=[t for t in tiers if buy and t['startPurchasedNumber']*ratio<=buy];unit=valid[-1]['productPrice']if valid else None;name=f'{boards}板+每型号{spares}备品';r[name+'商城购买量']=buy or'';r[name+'商城付款元']=round(buy*unit,4)if unit is not None else''
 rows.append(r)
write('采购清单-v0.11.csv',rows)
rows=[]
for a in A:
 e=a['例外编号'];selected=e in proof['selected_groups'];refs=a['位号'].split(',');active=[P[r]for r in refs];extra=[p for p in D['parts']if p['ref']in proof['new_refs']and e in p.get('exception_decision','')];rr=active+extra
 rows.append(dict(例外编号=e,原位号=a['位号'],本版位号=','.join(p['ref']for p in rr),本版C编号=','.join(sorted(set(p['lcsc']for p in rr))),决定='2026-10-11 用户指定采用3+14组，原型替换'if selected else'保留原件，后续待决定',电气状态='参数审核通过，CAD独立验收'if e in proof['electrical_equivalence_verified_groups']else'性能等效未验证，需焊后测试'if selected else a['结论'],电气要求=a['实际电路要求'],未验证项=a['判断与证据缺口'],换料费估算每单元=0 if selected else 20,是否生产定型='否'))
write('17组决定及剩余例外-v0.11.csv',rows)
text='''# v0.11：17组基础库原型改版

用户于2026-10-11指定将“3＋14组”采用本轮找到的基础库器件。3组（E20/E21/E22）有参数审核结论；其余14组为用户指定的原型试验，**性能等效未验证**。本版不代表可以直接量产，也没有把“基础库有货”当作“电气合格”。E01此前指定的22只C440198不变，其偏压容量/纹波与85℃温度上限仍须验收。

## 实施内容

|组|本版器件或组合|变化|
|---|---|---|
|E03|C28323 1µF/50V＋C28233 100nF/100V|六支路每个3.3µF改3×1µF＋3×100nF，增加30件；原3×10µF保留，每支路标称33.3µF|
|E04|C15008 CL31A107MQHNNNE|100µF/6.3V，1210→1206；国内SMT库存未返回，保持未知|
|E05|C29823 1206B475K500NT|九只4.7µF/50V，1210→1206；低压去耦与高压输出分别验收|
|E08/E10|C15127 AO3401A|Q7/Q8，30V P沟道；Q7保留R49，−1.8V导通保证缺口及驱动动态待验收|
|E09|C20917 AO3400A|Q1/Q4，30V N沟道，SOT-323→SOT-23，分别核对栅源波形|
|E11|C8678 SS34|D1/D2，40V/3A SMA；正确K/A脚序，重新布置功率支路|
|E12|C1622 CL10B473KB8NNNC|C26 47nF/50V，0805→0603|
|E13|C13967 CL21B474KBFNNNE|六只470nF/50V/X7R/0805|
|E14|C14858 CL10C101JB8NNNC|C36＋C151–C159共10×100pF/50V/C0G并联为1nF，增加9件；连接BENCH_3V3与SW_CT，不接GND|
|E15|C20526 MMBT3904(RANGE:100-300)|Q6，SOT-23，B/E/C=1/2/3；热/储存时间待验收|
|E17|C8598 B5819W SL|D4，40V/1A/SOD-123；Vf/漏电/结电容待验收|
|E18|C28233＋C1729 CL21B223KBANNNC|C18＋C160＋C161为2×100nF＋22nF=222nF，标称增加0.91%，增加2件|
|E19|C28323 CL21B105KBFNNNE|C22/C25，1µF/50V/X7R/0805；两个不同节点分别验收|
|E20|C17475 15k＋C17513 1k|R18＋R51串联16k，新增R18_FB_MID；不改变400k反馈上臂|
|E21|C28233 CL21B104KCFNNNE|C27/C33，100nF/100V/X7R/0805|
|E22|C149504 100k＋C17414 10k|R8＋R52串联110k，新增R8_FB_MID；不改变4.3k反馈下臂|

104→147装配件，102→145顶面SMT，J1/J2仍为手工插件；共36组采购型号。新增43件：C121–C161、R51/R52；原有符号UUID保留，PCB与原生原理图关联不变。新增basic-composites.kicad_sch是组合补充页，原来的符号仍在各原理图页。

## 参数与费用边界

R18与400k串联反馈链在保守100V端点差下电流约240µA，15k约0.87mW，1k约0.058mW；R8上臂110k在50V端点差下，100k约20.66mW、10k约2.07mW，均低于125mW并有85℃降额余量。两个串联组合的最坏总公差仍为±1%，温漂界限±100ppm/℃。这些计算不能证明屏幕反馈环路实测稳定性。

未验收：所有换料电容的工作偏压有效容量/ESR/纹波，Q7原件Qg约1.6nC而AO3401A约7nC/Ciss约645pF，Q8的Miller驱动和−1.8V导通缺口，Q1/Q4实际栅源电压与驱动负载，Q6脉冲损耗/散热，肖特基实际Vf/漏电/结电容。保留50V或更高耐压，CT不采用X7R，双肖特基D3/D5/D6连接形式不变。

按经济型SMT普通扩展库20元/型号/订单的场景，原24组例外中的17组采用基础库标签器件后，收费例外剩7组，理论换料费480→140元，减少340元/订单。**这是规则估算，不是新订单报价或总价节省。** 43个新增贴片件、购买倍数、备品及贴片费会改变付款。615元旧加工报价的订单条件未完整取得，不能直接宣称新版只需195元加工费。商城单价不作为SMT订单单价，SMT单价、MOQ、损耗及其他加工费未知时留空。

采购CSV按准确C编号汇总1板/5板，以及每型号组加2件备品的商城理论付款；同型号合并后再计算MOQ/倍数，未取得公开价格的留空。不含运费。此次公开接口刷新有部分失败，CSV分别保留“有效查询时间”和“本次刷新状态”，不能把历史库存当作实时保证。C15008的SMT库存仍未知；订单提交前必须核对。

## 剩余7组

E02 U4温度传感器、E06金属采样电阻、E07负载开关、E16 Q3 PNP、E23串联双肖特基、E24功率电感、E25 FPC保持原型号。尚未决定混合装配，机器BOM/CPL仍包括145个SMT位号。Q7旧料缺货已改为有基础库候选的AO3401A，但其低栅压/驱动性能缺口仍未闭环。

## 使用与验收

CAD验收以reports/ERC、DRC、引脚映射、GUI更新预览及release/verification.json为准。CAD通过不等于实板性能通过。首次仅建议小批原型；限流3.3V供电，先验证软启动/安全掉电和各正负电源波形，再接屏幕运行显示与温升测试。尤其关注Q7/R49两端GDRC的VGS幅度、尖峰、占空比、驱动负载和发热，以及六组源极电源的纹波和最低电压。

来源：[嘉立创元件库及经济型规则](https://m.jlc.com/portal/q2i38538.html)；准确C编号、国内库标签、库存、时间及厂家PDF见采购CSV和reports/procurement-v011.json。旧v0.9/v0.10文档与24组审核是历史快照；以本版逐位号对照和采购清单为当前选型。
'''
(R/'docs/基础库17组改版-v0.11.md').write_text(text)
(R/'docs/手焊说明-v0.11.md').write_text('# v0.11装配注意\n\n本版147件；145个顶面SMT，J1/J2插件手焊。完整BOM和机器BOM/CPL来源必须匹配同版verification.json，不混用旧release。新增CT十只0603请用放大镜、细镊子和助焊剂；切勿用X7R代替C0G。新增源极组合按位号采购，六支路不能互相短接。R51/R52不能省略或装成0Ω。SS34以本地SMA焊盘的1=K/2=A和外壳阴极条纹核对，Q1/Q4/Q7/Q8的G/S/D=1/2/3，Q6的B/E/C=1/2/3。\n\n参考编号见assembly-top.pdf的F.Fab标注；新增密集电容避免只凭丝印识别。先测电源、开关驱动和安全掉电，再接屏幕；关键电气等效未验证项见基础库17组改版说明。\n')
print('Wrote v0.11 change, purchasing and exception documents')
