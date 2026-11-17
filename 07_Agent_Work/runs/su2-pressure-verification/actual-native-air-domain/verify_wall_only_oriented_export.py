from pathlib import Path
import json,numpy as np
from collections import Counter
p=Path(__file__).parent;it=iter((p/'wall-only-oriented-air.su2').read_text().splitlines());assert next(it)=='NDIME= 3';ne=int(next(it).split('=')[1]);faces=Counter();patterns={10:((0,1,2),(0,1,3),(0,2,3),(1,2,3)),13:((0,1,2),(3,4,5),(0,1,4,3),(1,2,5,4),(2,0,3,5))}
for _ in range(ne):
 z=list(map(int,next(it).split()))
 for ix in patterns[z[0]]:faces[tuple(sorted(z[j+1] for j in ix))]+=1
nn=int(next(it).split('=')[1]);xyz=np.array([list(map(float,next(it).split()[:3])) for _ in range(nn)]);nm=int(next(it).split('=')[1]);markers={};boundary=Counter()
for _ in range(nm):
 name=next(it).split('=')[1].strip();n=int(next(it).split('=')[1]);markers[name]=[]
 for __ in range(n):
  z=list(map(int,next(it).split()));assert z[0] in (5,9);f=z[1:4] if z[0]==5 else z[1:5];markers[name].append(f);boundary[tuple(sorted(f))]+=1
ex={f for f,n in faces.items() if n==1};assert ex==set(boundary) and max(boundary.values())==1 and max(faces.values())==2
walls={i for f in markers['wall'] for i in f};rows=[]
for cap in json.loads((p/'boundary-review.json').read_text())['caps']:
 area=0;effective=0;inward=0
 for f in markers[cap['marker']]:
  # Triangulate quadrilateral strips to preserve linear nodal quadrature.
  for ids in ([f] if len(f)==3 else [[f[0],f[1],f[2]],[f[0],f[2],f[3]]]):
   q=xyz[ids];av=np.cross(q[1]-q[0],q[2]-q[0])/2;da=np.linalg.norm(av);area+=da;effective+=da*sum(i not in walls for i in ids)/3;inward+=np.dot(av,cap['outward_normal'])<=0
 print('CAP_DIAGNOSTIC',cap['marker'],area,cap['clear_area_m2'],inward)
 assert abs(area-cap['clear_area_m2'])<1e-8 and inward==0
 rows.append({'marker':cap['marker'],'area_m2':float(area),'inward_triangles':int(inward),'zero_wall_edge_effective_area_m2':float(effective)})
inlet=next(r for r in rows if r['marker']=='inlet');speed=12.000372763419485/inlet['zero_wall_edge_effective_area_m2'];r={'nodes':nn,'elements':ne,'caps':rows,'exterior_topology_pass':True,'inlet_flux_normalized_speed_m_s':speed,'pressure_accepted':False};(p/'wall-only-export-review.json').write_text(json.dumps(r,indent=2));print(json.dumps(r))
s=(p/'flux-normalized.cfg').read_text().replace('layered-air.su2','wall-only-oriented-air.su2').replace('12.558208523792572',str(speed)).replace('flux-normalized-history','wall-only-history').replace('flux-normalized-restart','wall-only-restart').replace('CFL_NUMBER=0.5','CFL_NUMBER=2').replace('INC_OUTLET_DAMPING=0.01','INC_OUTLET_DAMPING=0.1');(p/'wall-only-pilot.cfg').write_text(s)
