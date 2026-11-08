"""Compare actual native-saved geometry with data; DXF is inspection only."""
from pathlib import Path
from collections import Counter,defaultdict
import csv,json,math
import ezdxf
from cad_native import ROOT,CACHE,run,sha
D=ROOT/'05_Calculations/data';O=(64345.93225182503,15925.58365525945)
dwg=ROOT/'03_Design_Drawings/BSE3227_HVAC_Review_v04.dwg'
export=CACHE/'review_v04_inspection.dxf'
if export.exists():export.unlink()
run(dwg,[f'(command "_.DXFOUT" "{export.as_posix()}" "16")'],'reconcile_native_v04')
model=ezdxf.readfile(export).modelspace()
def read(n):return list(csv.DictReader((D/f'{n}_v04.csv').open()))
def point(x,y):return (round(float(x),3),round(float(y),3))
def endpoints(r):return (point(float(r['start_x_mm'])+O[0],float(r['start_y_mm'])+O[1]),point(float(r['end_x_mm'])+O[0],float(r['end_y_mm'])+O[1]))
for name,layer in [('ducts','M-DUCT'),('flex_routes','M-FLEX')]:
    actual=Counter(tuple(sorted([point(e.dxf.start.x,e.dxf.start.y),point(e.dxf.end.x,e.dxf.end.y)])) for e in model.query('LINE') if e.dxf.layer==layer)
    expected=Counter(tuple(sorted(endpoints(r))) for r in read(name))
    assert actual==expected,(name,actual-expected,expected-actual)
for name,layer,dimensions in [('diffusers','M-SUP-DIFF',[(600,600),(300,300)]),('vav_boxes','M-VAV',[(1000,800)])]:
    actual=Counter()
    for e in model.query('LWPOLYLINE'):
        if e.dxf.layer!=layer:continue
        ps=list(e.get_points('xy'));xx=[float(p[0]) for p in ps];yy=[float(p[1]) for p in ps]
        actual[(point(sum(xx)/len(xx),sum(yy)/len(yy)),point(max(xx)-min(xx),max(yy)-min(yy)))]+=1
    expected=Counter((point(float(r['x_mm'])+O[0],float(r['y_mm'])+O[1]),size) for r in read(name) for size in dimensions)
    assert actual==expected,(name,actual-expected,expected-actual)
labels=Counter(e.dxf.text for e in model.query('TEXT') if e.dxf.layer=='M-DUCT-TEXT')
assert labels==Counter(r['id'] for r in read('ducts'))
# Independent flow conservation at every geometric junction, without relying on
# the generator's downstream-VAV lists.
balance=defaultdict(float)
for r in read('ducts'):
    a,z=endpoints(r);q=float(r['flow_lps']);balance[a]-=q;balance[z]+=q
for v in read('vav_boxes'):
    x=float(v['x_mm'])+O[0];y=float(v['y_mm'])+O[1]
    terminal=point(x,y-400 if int(v['id'][-2:])>18 else y+400)
    balance[terminal]-=float(v['max_lps'])
root=point(19200+O[0],24600+O[1]);balance[root]+=sum(float(v['max_lps']) for v in read('vav_boxes'))
assert max(map(abs,balance.values()))<1e-6,dict(balance)
# Source geometry: source handles survive; only three original title/area
# texts intentionally move to an invisible layer. Layer colour is presentation.
source=ezdxf.readfile(CACHE/'source.dxf').modelspace();byhandle={e.dxf.handle:e for e in model}
def norm(v):
    if isinstance(v,(float,int)):return round(float(v),5)
    if isinstance(v,str):return v
    try:return tuple(norm(x) for x in v)
    except TypeError:return str(v)
def sig(e):
    attrs=e.dxfattribs();keys={'LINE':['start','end'],'ARC':['center','radius','start_angle','end_angle'],'TEXT':['text','insert','height','rotation'],'INSERT':['name','insert','xscale','yscale','zscale','rotation']}.get(e.dxftype(),[])
    values=[(k,norm(attrs.get(k))) for k in keys if k in attrs]
    if e.dxftype()=='INSERT' and e.dxf.name.startswith('*U'):
        values=[item for item in values if item[0]!='name']
        values.append(('anonymous_block_geometry',[sig(child) for child in e.doc.blocks[e.dxf.name]]))
    if e.dxftype()=='LWPOLYLINE':values.append(('vertices',norm(list(e.get_points()))));values.append(('closed',e.closed))
    return e.dxftype(),values
mismatches=[(e.dxf.handle,sig(e),sig(byhandle[e.dxf.handle]) if e.dxf.handle in byhandle else None) for e in source if e.dxf.handle not in byhandle or sig(e)!=sig(byhandle[e.dxf.handle])]
assert not mismatches,mismatches[:5]
result={'dwg_sha256':sha(dwg),'native_read_only_reopen_and_export':True,'duct_endpoints_matched':49,'flex_endpoints_matched':80,'diffuser_symbols_matched':80,'vav_envelopes_matched':20,'section_labels_matched':49,'geometric_node_flow_balance':True,'original_model_entity_geometry_matched':len(source),
        'scope':'Native DWG opened in AutoCAD 2027 before read-only inspection export. Export comparisons are not substitutes for native plot/visual quality checks.'}
(D/'native_reconciliation_v04.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
