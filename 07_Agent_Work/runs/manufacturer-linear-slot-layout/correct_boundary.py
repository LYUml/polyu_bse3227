import json
from pathlib import Path
from shapely import union_all
from shapely.geometry import shape,LineString,mapping
from bsa.air_allocation import prepare
base=Path(r'C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work/runs/manufacturer-linear-slot-layout');a=json.loads((base/'allocation.json').read_text());c=json.loads((base/'first-candidate.json').read_text());boundary=union_all([shape(t['geometry']) for t in a['allocation']['terminals']]);points=[dict(id=t['id'],center_m=t['center_m'][:]) for t in a['terminals']];moves=[];half=c['slot_length_m']/2
for t in points:
 x,y=t['center_m']
 if boundary.covers(LineString([(x,y-half),(x,y+half)])):continue
 options=[]
 for step in range(1,201):
  for sign in [-1,1]:
   ny=y+sign*step*.01
   if boundary.covers(LineString([(x,ny-half),(x,ny+half)])):options.append(ny)
  if options:break
 assert options
 ny=min(options,key=lambda v:abs(v-y));t['center_m']=[x,ny];moves.append(dict(id=t['id'],old_y_m=y,new_y_m=ny,shift_m=ny-y))
fresh=prepare(mapping(boundary),points,a['load']['inputs'],a['turndown']);assert fresh['checks']['area_conserved'] and fresh['checks']['flow_conserved']
new=base/'boundary-corrected';new.mkdir(exist_ok=True)
(new/'allocation.json').write_text(json.dumps(fresh,indent=2));(new/'first-candidate.json').write_text(json.dumps(c,indent=2));(new/'independent-performance-check.json').write_bytes((base/'independent-performance-check.json').read_bytes())
(new/'position-changes.json').write_text(json.dumps(dict(scope='Separate candidate: minimum 10mm-grid vertical move to contain finite slot; fresh nearest-centre load/flow allocation; no CAD or design acceptance',moves=moves,checks=fresh['checks']),indent=2))
script=(base/'check_finite_slots.py').read_text().replace("out=base/'runs/manufacturer-linear-slot-layout'","out=base/'runs/manufacturer-linear-slot-layout/boundary-corrected'")
(new/'check_finite_slots.py').write_text(script)
print(json.dumps(moves))
