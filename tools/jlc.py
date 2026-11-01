"""JLCPCB/LCSC parts search (stock + price). usage: python3 jlc.py "KW1;KW2" [n]"""
import json,sys,urllib.request
API="https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList"
def search(kw,n=6):
    req=urllib.request.Request(API,data=json.dumps({"keyword":kw,"currentPage":1,"pageSize":n}).encode(),headers={'Content-Type':'application/json'})
    d=json.load(urllib.request.urlopen(req,timeout=40)); out=[]
    for c in (d.get('data') or {}).get('componentPageInfo',{}).get('list',[]) or []:
        pr=c.get('componentPrices') or []
        out.append(dict(lcsc=c.get('componentCode'),mpn=c.get('componentModelEn'),mfr=c.get('componentBrandEn'),pkg=c.get('componentSpecificationEn'),
            stock=c.get('stockCount'),lib=c.get('componentLibraryType'),p1=pr[0]['productPrice'] if pr else None,pN=pr[-1]['productPrice'] if pr else None,
            prices=[(p['startNumber'],p['productPrice']) for p in pr],desc=(c.get('describe') or '')[:110]))
    return out
def lookup(code):
    r=[x for x in search(code,5) if x['lcsc']==code]; return r[0] if r else None
if __name__=='__main__':
    for kw in sys.argv[1].split(';'):
        print('##',kw)
        for r in search(kw,int(sys.argv[2]) if len(sys.argv)>2 else 6): print('  {lcsc} | {mpn} | {mfr} | {pkg} | stock {stock} | ${p1}->${pN}'.format(**r))
