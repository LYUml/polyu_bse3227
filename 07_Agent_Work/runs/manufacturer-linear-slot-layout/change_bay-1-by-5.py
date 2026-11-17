import json
from pathlib import Path
from shapely import union_all
from shapely.geometry import shape,mapping
from bsa.manufacturer_adpi import grid
from bsa.air_allocation import prepare
base=Path(r'C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work/runs/manufacturer-linear-slot-layout');old=base/'boundary-corrected';a=json.loads((old/'allocation.json').read_text());b=union_all([shape(t['geometry']) for t in a['allocation']['terminals']]);freshbay=[t for t in grid(b,36.595584,((4,16),(1,5))) if t['id'].startswith('bay-')];points=[dict(id=t['id'],center_m=t['center_m']) for t in a['terminals'] if t['id'].startswith('main-')]+freshbay
fresh=prepare(mapping(b),points,a['load']['inputs'],a['turndown']);assert fresh['checks']['flow_conserved'] and fresh['checks']['area_conserved'];out=base/'bay-1-by-5';out.mkdir(exist_ok=True);(out/'allocation.json').write_text(json.dumps(fresh,indent=2))
for name in ['first-candidate.json','independent-performance-check.json']:(out/name).write_bytes((old/name).read_bytes())
for src in [old/'check_finite_slots.py',base/'select_width.py']:
 s=src.read_text().replace("runs/manufacturer-linear-slot-layout/boundary-corrected","runs/manufacturer-linear-slot-layout/bay-1-by-5");(out/src.name).write_text(s)
print('new terminal count',len(points),'checks',fresh['checks'])
