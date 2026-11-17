import json
from pathlib import Path
from shapely.geometry import shape,LineString
base=Path(r'C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work/runs/manufacturer-linear-slot-layout');old=base/'three-column-edges';out=base/'column-bay-centres';out.mkdir(exist_ok=True);a=json.loads((old/'allocation.json').read_text());ts=[t for t in a['terminals'] if not t['id'].startswith('main-') or int(t['id'].split('-')[2])!=11]
for i,x in enumerate([(65.47093225182505+78.783432)/2,(79.908432+94.08426558515829)/2,(95.20926558515832+108.22093225182499)/2]):ts.append(dict(id=f'column-band-{i+1}',center_m=[x,30.874584]))
a['terminals']=ts;(out/'allocation.json').write_text(json.dumps(a,indent=2))
for name in ['first-candidate.json','independent-performance-check.json']:(out/name).write_bytes((old/name).read_bytes())
for name in ['check_finite_slots.py','check_dense_samples.py']:(out/name).write_text((old/name).read_text().replace('manufacturer-linear-slot-layout/three-column-edges','manufacturer-linear-slot-layout/column-bay-centres'))
s=(base/'explicit_service_strips.py').read_text().replace("['uniform-main-15-rows','column-avoiding']","['column-bay-centres']");s=s.replace("for i,y in enumerate(ys):","if zone=='main':cuts[1]=18.45\n  for i,y in enumerate(ys):");(base/'column_band_services.py').write_text(s)
