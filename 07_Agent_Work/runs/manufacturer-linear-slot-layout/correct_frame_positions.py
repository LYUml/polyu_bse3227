import json
from pathlib import Path
from shapely.geometry import shape,Point
base=Path(r'C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work/runs/manufacturer-linear-slot-layout');old=base/'column-bay-centres-balanced-services';out=base/'frame-b-clearance-corrected';out.mkdir(exist_ok=True);a=json.loads((old/'allocation.json').read_text());moves=[]
for t in a['terminals']:
 if t['id'] in ['bay-1-2','bay-1-3']:
  shift=(-1 if t['id']=='bay-1-2' else 1)*.009525;t['center_m'][1]+=shift;assert shape(t['geometry']).covers(Point(t['center_m']));moves.append(dict(id=t['id'],shift_y_m=shift))
for v in a['allocation']['terminals']:
 t=next(t for t in a['terminals'] if t['id']==v['id']);v['center_m']=t['center_m']
(out/'allocation.json').write_text(json.dumps(a,indent=2));(out/'frame-position-changes.json').write_text(json.dumps(dict(scope='Separate Frame B candidate, assumed10mm overall end gap, same explicit service cells and loads',moves=moves),indent=2))
for name in ['first-candidate.json','independent-performance-check.json','service-partition-check.json']:(out/name).write_bytes((old/name).read_bytes())
for name in ['check_finite_slots.py','check_dense_samples.py','check_event_samples.py']:(out/name).write_text((old/name).read_text().replace('manufacturer-linear-slot-layout/column-bay-centres-balanced-services','manufacturer-linear-slot-layout/frame-b-clearance-corrected'))
for src in ['prepare_candidate_review.py','check_frame_b.py']:(out/src).write_text((base/src).read_text().replace('manufacturer-linear-slot-layout/column-bay-centres-balanced-services','manufacturer-linear-slot-layout/frame-b-clearance-corrected'))
