import sys,json,hashlib,struct,math
from collections import Counter
from pathlib import Path
import gmsh
p=Path(__file__).parent
family=int(sys.argv[1]);d=p/f'family-{family}-layers';source=d/'air-planar-caps.msh';dest=d/'air-exterior-gmsh22.msh'
assert not dest.exists()
patterns={4:((0,2,1),(0,1,3),(1,2,3),(2,0,3)),6:((0,2,1),(3,4,5),(0,1,4,3),(1,2,5,4),(2,0,3,5))}
def volume():
 types,tags,arrays=gmsh.model.mesh.getElements(3);h=hashlib.sha256();used=set();total=0
 for kind,ets,flat in sorted(zip(types,tags,arrays),key=lambda x:int(x[0])):
  kind=int(kind);n=gmsh.model.mesh.getElementProperties(kind)[3];rows=sorted((int(tag),tuple(int(x) for x in flat[i*n:(i+1)*n])) for i,tag in enumerate(ets));total+=len(rows)
  for tag,nodes in rows:h.update(struct.pack('<'+'Q'*(len(nodes)+2),kind,tag,*nodes));used.update(nodes)
 return h.hexdigest(),used,total
def coordinates(used):
 tags,flat,_=gmsh.model.mesh.getNodes();return {int(tag):tuple(float(x) for x in flat[i*3:i*3+3]) for i,tag in enumerate(tags) if int(tag) in used}
gmsh.initialize()
try:
 gmsh.option.setNumber('General.Terminal',0);gmsh.open(str(source));before,used,ncells=volume();xyz=coordinates(used);inc=Counter()
 types,tags,arrays=gmsh.model.mesh.getElements(3)
 for kind,flat in zip(types,arrays):
  kind=int(kind);assert kind in patterns;n=gmsh.model.mesh.getElementProperties(kind)[3]
  for i in range(0,len(flat),n):
   nodes=[int(x) for x in flat[i:i+n]]
   for face in patterns[kind]:inc[tuple(sorted(nodes[j] for j in face))]+=1
 assert max(inc.values())<=2
 exterior={k for k,v in inc.items() if v==1};seen=set();removed=Counter();surface_before={};physical_before={}
 for dim,tag in gmsh.model.getPhysicalGroups():
  name=gmsh.model.getPhysicalName(dim,tag);physical_before[(dim,tag)]=name
  if dim!=2:continue
  surface_before[name]=0
  for entity in gmsh.model.getEntitiesForPhysicalGroup(dim,tag):
   ts,ets,flats=gmsh.model.mesh.getElements(2,int(entity));drop=[]
   for kind,element_tags,flat in zip(ts,ets,flats):
    n=gmsh.model.mesh.getElementProperties(kind)[3];assert n in (3,4)
    for i,eid in enumerate(element_tags):
     key=tuple(sorted(int(x) for x in flat[i*n:(i+1)*n]));surface_before[name]+=1
     if inc[key]==2:
      assert name=='wall';drop.append(int(eid));removed[name]+=1
     else:assert inc[key]==1 and key not in seen;seen.add(key)
   if drop:gmsh.model.mesh.removeElements(2,int(entity),drop)
 assert seen==exterior and removed=={'wall':1496}
 assert volume()[0]==before
 gmsh.option.setNumber('Mesh.MshFileVersion',2.2);gmsh.option.setNumber('Mesh.Binary',0);gmsh.option.setNumber('Mesh.Renumber',0);gmsh.write(str(dest));gmsh.clear();gmsh.open(str(dest));after,used_after,n_after=volume();assert after==before and used_after==used and n_after==ncells
 now=coordinates(used);delta=max(math.dist(xyz[k],now[k]) for k in used);assert delta<1e-12
 physical_after={(int(dim),int(tag)):gmsh.model.getPhysicalName(dim,tag) for dim,tag in gmsh.model.getPhysicalGroups()};assert physical_after==physical_before
 seen=set();counts={}
 for (dim,tag),name in physical_after.items():
  if dim!=2:continue
  counts[name]=0
  for entity in gmsh.model.getEntitiesForPhysicalGroup(dim,tag):
   ts,_,flats=gmsh.model.mesh.getElements(2,int(entity))
   for kind,flat in zip(ts,flats):
    n=gmsh.model.mesh.getElementProperties(kind)[3]
    for i in range(0,len(flat),n):
     key=tuple(sorted(int(x) for x in flat[i:i+n]));assert key in exterior and key not in seen;seen.add(key);counts[name]+=1
 assert seen==exterior
 r=dict(source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),output_sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),method_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),gmsh_version=gmsh.__version__,volume_cells=ncells,used_nodes=len(used),volume_element_tags_and_connectivity_sha256=before,volume_connectivity_unchanged=True,maximum_coordinate_serialization_difference_m=delta,removed_internal_wall_faces=dict(removed),physical_surface_face_counts=counts,all_exterior_faces_exactly_once=True,all_physical_names_preserved=True,format='Gmsh2.2 ASCII',target_solver_import_executed=False,engineering_accepted=False,scope='Native mesh exchange preparation only; no target solver or engineering acceptance.')
 with (d/'gmsh22-exchange-review.json').open('x') as f:json.dump(r,f,indent=2,allow_nan=False)
 print(json.dumps(r),flush=True)
finally:gmsh.finalize()
