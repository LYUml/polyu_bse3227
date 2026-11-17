import json
from pathlib import Path
from shapely.geometry import LineString,shape,mapping
from shapely import union_all
from bsa.air_allocation import prepare
base=Path(r'C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work/runs/manufacturer-linear-slot-layout');old=base/'bay-1-by-6';out=base/'clearance-corrected';out.mkdir(exist_ok=True);a=json.loads((old/'allocation.json').read_text());points=[dict(id=t['id'],center_m=t['center_m'][:]) for t in a['terminals']];lookup={t['id']:t for t in points};moves=[]
for lo,hi in [('main-1-2','main-1-3'),('main-4-2','main-4-3'),('bay-1-2','bay-1-3')]:
 p,q=lookup[lo],lookup[hi];mid=(p['center_m'][1]+q['center_m'][1])/2
 for t,y in [(p,mid-1.2292/2),(q,mid+1.2292/2)]:
  moves.append(dict(id=t['id'],old_center_m=t['center_m'][:],new_center_m=[t['center_m'][0],y]));t['center_m'][1]=y
b=union_all([shape(t['geometry']) for t in a['allocation']['terminals']]);ss=[LineString([(t['center_m'][0],t['center_m'][1]-.6096),(t['center_m'][0],t['center_m'][1]+.6096)]) for t in points];assert all(b.covers(s) for s in ss);assert all(not ss[i].intersects(ss[j]) for i in range(len(ss)) for j in range(i));fresh=prepare(mapping(b),points,a['load']['inputs'],a['turndown']);assert fresh['checks']['area_conserved'] and fresh['checks']['flow_conserved'];(out/'allocation.json').write_text(json.dumps(fresh,indent=2));(out/'geometry-correction.json').write_text(json.dumps(dict(scope='Separate candidate, fixed4ft length,10mm assumed centerline end gap; NOT equipment body clearance',moves=moves,all_segments_inside=True,pairwise_segment_intersections=0,design_accepted=False),indent=2))
for name in ['first-candidate.json','independent-performance-check.json']:(out/name).write_bytes((old/name).read_bytes())
for name in ['check_finite_slots.py','select_slot_count.py','check_dense_samples.py']:
 s=(old/name).read_text().replace('manufacturer-linear-slot-layout/bay-1-by-6','manufacturer-linear-slot-layout/clearance-corrected');(out/name).write_text(s)
print(json.dumps(dict(moved=len(moves),terminal_count=len(points),checks=fresh['checks'])))
