from pathlib import Path
import gmsh,json,hashlib
b=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work/runs/openfoam-pressure-verification');d=b/'plenum-family-1-native-hex-feasibility/constant/triSurface';(d/'air.obj').rename(d/'air-ungrouped-not-adopted.obj');gmsh.initialize();gmsh.option.setNumber('General.Terminal',0);gmsh.open(str(b/'plenum-family-1-balanced-core-optimized/air-exterior-gmsh22.msh'));tags,flat,_=gmsh.model.mesh.getNodes();xyz={int(n):tuple(map(float,flat[i*3:i*3+3])) for i,n in enumerate(tags)};groups={}
for dim,g in gmsh.model.getPhysicalGroups(2):
 name=gmsh.model.getPhysicalName(dim,g);rows=[]
 for entity in gmsh.model.getEntitiesForPhysicalGroup(dim,g):
  types,ets,arrays=gmsh.model.mesh.getElements(2,int(entity))
  for kind,a in zip(types,arrays):
   assert kind in [2,3];n=3 if kind==2 else 4;rows.extend(tuple(map(int,a[i:i+n])) for i in range(0,len(a),n))
 groups[name]=rows
gmsh.finalize();assert set(groups)=={'inlet','outlet_0','outlet_1','outlet_2','outlet_3','wall'};used=sorted({n for rows in groups.values() for f in rows for n in f});mapping={n:i+1 for i,n in enumerate(used)};lines=['# Source-bound physical-region OBJ adapter; numerical surface only']+['v '+' '.join(format(x,'.17g') for x in xyz[n]) for n in used]
for name,rows in groups.items():lines+=['g '+name]+['f '+' '.join(str(mapping[n]) for n in f) for f in rows]
p=d/'air.obj';p.write_text('\n'.join(lines)+'\n');parsed={};points=[];name=None
for line in p.read_text().splitlines():
 if line.startswith('v '):points.append(tuple(map(float,line.split()[1:])))
 if line.startswith('g '):name=line[2:];parsed[name]=[]
 if line.startswith('f '):parsed[name].append(tuple(used[int(n)-1] for n in line.split()[1:]))
assert parsed==groups and points==[xyz[n] for n in used];r={'scope':'Lossless grouped surface exchange only; native closure and meshing pending','surface_vertices':len(used),'group_face_counts':{k:len(v) for k,v in groups.items()},'all_oriented_faces_and_coordinates_reconciled':True,'obj_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'engineering_accepted':False};(d.parent.parent/'surface-exchange-review.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
