import json,re,hashlib
from pathlib import Path
from pypdf import PdfReader
from shapely import union_all
from shapely.geometry import shape,Point,LineString
from fluids.numerics import interp
from bsa.manufacturer_adpi import screen
base=Path(r'C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work');out=base/'runs/manufacturer-linear-slot-layout/boot-first-row-four-strip-services';pdf=base/'project/adpi-manufacturer-study/linear-slot-source/1900 Boot Performance.pdf';tables=json.loads((out/'All Boot Domain Combinations.json').read_text())['tables']

a=json.loads((out/'allocation.json').read_text());d=json.loads((out/'finite-slot-diagnostic.json').read_text());curves=json.loads((base/'runs/manufacturer-type4-native-curves/curves.json').read_text());results=[]
boundary=shape(json.loads(Path('C:\\Users\\lyuml-win\\Desktop\\polyu_bse3227\\07_Agent_Work\\project\\bse3227-column-row-candidate\\office-boundary.geojson').read_text()))
for t,g in zip(a['terminals'],d['results']):
 assert t['id']==g['id'];attempts=[]
 # Geometry is independent of catalogue flow domain: use maximum-case rays, present for all current positions.
 rays=[];x,y=t['center_m']
 events=[y-.6096,y+.6096]
 events += [v['center_m'][1]+sign*.6096 for v in a['terminals'] for sign in [-1,1] if y-.6096 < v['center_m'][1]+sign*.6096 < y+.6096]
 events += [py for ring in [boundary.exterior,*boundary.interiors] for px,py in ring.coords if y-.6096<py<y+.6096]
 events=sorted(set(events));samples=sorted(set(events+[(lo+hi)/2 for lo,hi in zip(events,events[1:])]))
 for sy in samples:
  for dx in [-1,1]:
   ray=boundary.intersection(LineString([(x,sy),(x+dx*200,sy)]));pieces=list(ray.geoms) if hasattr(ray,'geoms') else [ray]
   connected=[v for v in pieces if v.geom_type=='LineString' and v.distance(Point(x,sy))<1e-8];assert len(connected)==1
   L=max((vx-x)*dx for vx,vy in connected[0].coords)
   for other in a['terminals']:
    ox,oy=other['center_m'];along=(ox-x)*dx
    if other['id']!=t['id'] and along>1e-8 and abs(sy-oy)<=1.2192/2+1e-10:L=min(L,along/2)
   assert L>0;rays.append(dict(L_m=L))
 assert len(rays)>=6
 for width,table in tables.items():
  rows=table['rows'];fail=0;outside=0
  for case,key,loads in [('maximum','maximum_flow_L_s',(40,60)),('minimum','minimum_flow_L_s',(20,40))]:
   q=t[key]
   if not rows[0]['flow_L_s']<=q<=rows[-1]['flow_L_s']:outside+=1;continue
   throw=interp(q,[r['flow_L_s'] for r in rows],[r['T050_m'] for r in rows])
   for ray in rays:
    if any(screen(curves,load,throw/ray['L_m'])['status']!='paired_curve_threshold_met' for load in loads):fail+=1
  attempts.append(dict(slot_width_inch=width,out_of_table_flow_cases=outside,failed_sample_checks=fail,all_checks_pass=outside==0 and fail==0))
 best=min(attempts,key=lambda v:(v['out_of_table_flow_cases'],v['failed_sample_checks']))
 results.append(dict(id=t['id'],best=best,attempts=attempts))
r=dict(scope='UNCONFIRMED pattern hypothesis: BOOT published perpendicular T050 applied to both horizontal directions with Type4 curves, source does not establish two-way/baffle settings. Not product or ADPI acceptance',performance_source_sha256=hashlib.sha256(pdf.read_bytes()).hexdigest(),tables=tables,results=results,terminals_passing=sum(v['best']['all_checks_pass'] for v in results),terminals_with_flow_domain_gap=sum(v['best']['out_of_table_flow_cases']>0 for v in results),design_accepted=False)
(out/'Boot Own Throw Conditional Diagnostic.json').write_text(json.dumps(r,indent=2));print(json.dumps({k:v for k,v in r.items() if k not in ['tables','results']}))
