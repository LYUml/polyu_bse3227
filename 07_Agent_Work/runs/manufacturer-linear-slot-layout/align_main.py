import json
from pathlib import Path
from shapely.geometry import LineString,shape,mapping
from shapely import union_all
from bsa.air_allocation import prepare
base=Path(r'C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work/runs/manufacturer-linear-slot-layout');old=base/'clearance-corrected';out=base/'aligned-main';out.mkdir(exist_ok=True);a=json.loads((old/'allocation.json').read_text());b=union_all([shape(t['geometry']) for t in a['allocation']['terminals']]);points=[dict(id=t['id'],center_m=t['center_m'][:]) for t in a['terminals']];moves=[]
for t in points:
 if not t['id'].startswith('main-'):continue
 original=t['center_m'][:];col=int(t['id'].split('-')[1]);x=64.525932+(col-.5)*11.16;y=t['center_m'][1]
 if not b.covers(LineString([(x,y-.6096),(x,y+.6096)])):
  candidates=[y+sign*step*.01 for step in range(1,201) for sign in [-1,1] if b.covers(LineString([(x,y+sign*step*.01-.6096),(x,y+sign*step*.01+.6096)]))];assert candidates
  y=min(candidates,key=lambda v:abs(v-y))
 t['center_m']=[x,y]
 if original!=t['center_m']:moves.append(dict(id=t['id'],old=original,new=t['center_m']))
ss=[LineString([(t['center_m'][0],t['center_m'][1]-.6096),(t['center_m'][0],t['center_m'][1]+.6096)]) for t in points];collisions=[(points[i]['id'],points[j]['id']) for i in range(len(ss)) for j in range(i) if ss[i].intersects(ss[j])];print('collisions',collisions)
fresh=prepare(mapping(b),points,a['load']['inputs'],a['turndown']);(out/'allocation.json').write_text(json.dumps(fresh,indent=2));(out/'geometry-correction.json').write_text(json.dumps(dict(scope='Separate column alignment diagnostic, not accepted design',moves=moves,intersections=collisions),indent=2))
for name in ['first-candidate.json','independent-performance-check.json']:(out/name).write_bytes((old/name).read_bytes())
for name in ['check_finite_slots.py','check_dense_samples.py']:(out/name).write_text((old/name).read_text().replace('manufacturer-linear-slot-layout/clearance-corrected','manufacturer-linear-slot-layout/aligned-main'))
