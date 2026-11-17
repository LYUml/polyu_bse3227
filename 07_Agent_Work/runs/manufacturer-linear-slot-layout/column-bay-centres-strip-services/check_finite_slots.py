import json,math,hashlib
from pathlib import Path
from shapely import union_all
from shapely.geometry import shape,Point,LineString
from fluids.numerics import interp
from bsa.manufacturer_adpi import screen
base=Path(r'C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work')
out=base/'runs/manufacturer-linear-slot-layout/column-bay-centres-strip-services'
a=json.loads((out/'allocation.json').read_text());c=json.loads((out/'first-candidate.json').read_text())
curves=json.loads((base/'runs/manufacturer-type4-native-curves/curves.json').read_text())
boundary=union_all([shape(t['geometry']) for t in a['allocation']['terminals']]);ts=a['terminals'];length=c['slot_length_m'];rows=c['source_rows'];results=[]
for t in ts:
 x,y=t['center_m'];segment=LineString([(x,y-length/2),(x,y+length/2)])
 if not boundary.covers(segment):
  results.append(dict(id=t['id'],segment_inside=False,status='outside_boundary'));continue
 checks=[];outside=0
 for case,key,loads in [('maximum','maximum_flow_L_s',(40,60)),('minimum','minimum_flow_L_s',(20,40))]:
  q=t[key]/length
  if not rows[0]['flow_L_s_m']<=q<=rows[-1]['flow_L_s_m']:
   outside+=1;continue
  throw=interp(q,[r['flow_L_s_m'] for r in rows],[r['T050_m'] for r in rows])
  for k in range(9):
   sy=y-length/2+length*k/8;p=Point(x,sy)
   for direction,dx in [('east',1),('west',-1)]:
    ray=boundary.intersection(LineString([(x,sy),(x+dx*200,sy)]))
    pieces=list(ray.geoms) if hasattr(ray,'geoms') else [ray]
    connected=[g for g in pieces if g.geom_type=='LineString' and g.distance(p)<1e-8]
    assert len(connected)==1
    wall=max((vx-x)*dx for vx,vy in connected[0].coords);L=wall;opponent=None
    for other in ts:
     ox,oy=other['center_m'];along=(ox-x)*dx
     if other['id']!=t['id'] and along>1e-8 and abs(sy-oy)<=length/2+1e-10 and along/2<L:
      L=along/2;opponent=other['id']
    assert L>0
    statuses=[screen(curves,load,throw/L) for load in loads]
    checks.append(dict(case=case,sample=k,direction=direction,L_m=L,opposing_terminal=opponent,ratio=throw/L,paired_loads=list(loads),passed=all(s['status']=='paired_curve_threshold_met' for s in statuses)))
 results.append(dict(id=t['id'],segment_inside=True,flow_cases_outside_table=outside,sampled_checks=len(checks),failed_sample_checks=sum(not v['passed'] for v in checks),all_sample_checks_pass=outside==0 and all(v['passed'] for v in checks),checks=checks))
r=dict(scope='Nine finite-slot sample rays each side, opposing finite segment overlap and polygon walls; diagnostic only, no continuous jet/ADPI/installation acceptance',slot_length_m=length,samples_per_slot=9,source_input_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [out/'allocation.json',out/'first-candidate.json',out/'independent-performance-check.json']},terminals_with_all_sample_checks_pass=sum(v.get('all_sample_checks_pass',False) for v in results),outside_boundary=sum(not v['segment_inside'] for v in results),results=results,design_accepted=False)
(out/'finite-slot-diagnostic.json').write_text(json.dumps(r,indent=2))
print(json.dumps({k:v for k,v in r.items() if k not in ('results','source_input_sha256')}))
