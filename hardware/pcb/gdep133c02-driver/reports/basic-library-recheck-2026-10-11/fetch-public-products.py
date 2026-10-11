import json,csv,re,subprocess,pathlib,datetime,concurrent.futures,time
R=pathlib.Path(__file__).resolve().parents[2];O=R/'reports/basic-library-recheck-2026-10-11';O.mkdir(exist_ok=True)
rows=list(csv.DictReader((R/'docs/例外决定-v0.9.csv').open(encoding='utf-8-sig')))[1:]
codes=[r['原C号']for r in rows]+['C29823','C338088','C49066','C16133','C13967','C28233','C28323','C15849','C1622','C1623','C1625','C1636','C1729','C1740','C1745','C17490','C4210','C17422','C25805','C20526','C20527','C8512','C9169','C8392','C2128','C2508','C8598','C20917','C15127','C10487','C8414','C5359093','C545575','C5337195','C5224069','C28085','C30389','C636980','C42460613','C509950','C3290106','C5245314','C1021610','C317185','C1588','C2480','C22452','C8678','C167715','C7429','C7498','C8393','C8667','C1648','C21120','C1737','C1615','C15008','C96123','C60133','C2500','C2143','C47546','C85098','C1739','C1629','C17536','C17413','C17414','C17540','C17475','C17513','C149504','C14858','C8591','C2145','C7963','C3040358','C8543']
codes=list(dict.fromkeys(codes));out=json.loads((O/'products.json').read_text())if(O/'products.json').exists()else{}
def curl(u,post=False):
 cmd=['curl','-L','-s','--max-time','15','-A','Mozilla/5.0 Firefox/128.0']
 if post:cmd+=['-X','POST','-H','Content-Type: application/json','--data','{}']
 return subprocess.check_output(cmd+[u]).decode()
def get(c):
 rec={'code':c,'queried_at':datetime.datetime.now().astimezone().isoformat()}
 try:
  a=json.loads(curl('https://wmsc.lcsc.com/ftps/wm/product/detail?productCode='+c))['result'];rec['metadata']={k:v for k,v in a.items()if k in ['productId', 'productCode', 'productModel', 'brandNameEn', 'brandId', 'encapStandard', 'productKeyAttributes', 'catalogName', 'stockNumber', 'minBuyNumber', 'minPacketNumber', 'productPriceList', 'pdfUrl', 'paramVOList', 'productIntroEn', 'productDescEn']};url='https://item.szlcsc.com/'+str(a['productId'])+'.html';rec['url']=url
  s=curl(url);m=re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>',s,re.S)
  if not m:raise ValueError('SSR unavailable/challenge; not solved')
  w=json.loads(m[1])['props']['pageProps']['webData'];p=w['productRecord'];rec['domestic']={k:p.get(k)for k in ['productCode','productModel','productGradePlateName','encapsulationModel','smtLabel','minBuyNumber','theRatio','productPriceList']};rec['domestic'].update(retail_stock=w.get('totalStockNumber'),smt_stock=w.get('smtStockNumber'))
  a=json.loads(curl('https://list.szlcsc.com/substitute/simple/list?productCode='+c,True)).get('result')or{};main=a.get('mainProduct')or{};rec['pricing']={k:v for k,v in main.items()if k in ['productCode', 'productId', 'productModel', 'productGradePlateName', 'encapsulationModel', 'theRatio', 'productPriceList', 'stockNumber', 'totalStockNumber', 'smtStockNumber', 'paramLinkedMap']};rec['query_status']='OK'
 except Exception as e:rec['query_status']='INCOMPLETE';rec['error']=str(e)
 return c,rec
missing=[c for c in codes if c not in out]
with concurrent.futures.ThreadPoolExecutor(max_workers=2)as pool:
 for c,rec in pool.map(get,missing):
  out[c]=rec;(O/'products.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');p=rec.get('domestic',{});print(c,rec['query_status'],p.get('productModel'),p.get('smtLabel'),p.get('smt_stock'),flush=True)
print('DONE',len(out))
