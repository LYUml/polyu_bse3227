import json,hashlib
from pathlib import Path
from shapely.geometry import shape,mapping,LineString
from bsa.air_allocation import prepare
base=Path(r'C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work/runs/manufacturer-linear-slot-layout');old=base/'uniform-main-15-rows';out=base/'column-avoiding';out.mkdir(exist_ok=True);a=json.loads((old/'allocation.json').read_text());source=base.parent.parent/'project/bse3227-column-row-candidate/office-boundary.geojson';assert hashlib.sha256(source.read_bytes()).hexdigest()=='c64f5b2df5be607b7aebc978a51d3a168b45ca9e057135f0df6540e651a4a617';b=shape(json.loads(source.read_text()));points=[]
for t in a['terminals']:
 if t['id'].startswith('bay-'):points.append(dict(id=t['id'],center_m=t['center_m']));continue
 col,row=map(int,t['id'].split('-')[1:])
 if row in [1,11,15]:continue
 points.append(dict(id=t['id'],center_m=t['center_m']))
for row in [1,15]:
 y=next(t['center_m'][1] for t in a['terminals'] if t['id']==f'main-1-{row}')
 for col in range(3):points.append(dict(id=f'edge-{row}-{col+1}',center_m=[64.525932+(col+.5)*44.64/3,y]))
ss=[LineString([(t['center_m'][0],t['center_m'][1]-.6096),(t['center_m'][0],t['center_m'][1]+.6096)]) for t in points];assert all(b.covers(s) for s in ss);assert all(not ss[i].intersects(ss[j]) for i in range(len(ss)) for j in range(i));fresh=prepare(mapping(b),points,a['load']['inputs'],a['turndown']);assert fresh['checks']['area_conserved'] and fresh['checks']['flow_conserved'];(out/'allocation.json').write_text(json.dumps(fresh,indent=2))
for name in ['first-candidate.json','independent-performance-check.json']:(out/name).write_bytes((old/name).read_bytes())
for name in ['check_finite_slots.py','check_dense_samples.py']:
 s=(old/name).read_text().replace('manufacturer-linear-slot-layout/uniform-main-15-rows','manufacturer-linear-slot-layout/column-avoiding');s=s.replace('boundary=union_all([shape(v["geometry"]) for v in a["allocation"]["terminals"]])',f'boundary=shape(json.loads(Path({str(source)!r}).read_text()))');(out/name).write_text(s)
(out/'geometry-check.json').write_text(json.dumps(dict(source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),all_segments_inside=True,intersections=0,terminal_count=len(points),scope='Source contains two interior column voids, both retained; centerlines only'),indent=2))
