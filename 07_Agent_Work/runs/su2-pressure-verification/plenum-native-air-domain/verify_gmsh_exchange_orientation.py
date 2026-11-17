import gmsh,json,hashlib,math,sys
from pathlib import Path
from collections import Counter
p=Path(__file__).parent/f'family-{int(sys.argv[1])}-layers'
patterns={4:((0,2,1),(0,1,3),(1,2,3),(2,0,3)),6:((0,2,1),(3,4,5),(0,1,4,3),(1,2,5,4),(2,0,3,5))}
def nodes():
 tags,flat,_=gmsh.model.mesh.getNodes();return {int(t):tuple(float(x) for x in flat[i*3:i*3+3]) for i,t in enumerate(tags)}
def cells(mapping=None):
 ts,_,arrays=gmsh.model.mesh.getElements(3);records=[];used=set()
 for t,flat in zip(ts,arrays):
  t=int(t);n=gmsh.model.mesh.getElementProperties(t)[3]
  for i in range(0,len(flat),n):
   row=tuple((mapping[int(k)] if mapping else int(k)) for k in flat[i:i+n]);records.append((t,row));used.update(row)
 h=hashlib.sha256()
 for t,row in sorted(records):h.update((str(t)+':'+','.join(map(str,row))+'\n').encode())
 return records,used,h.hexdigest()
def surfaces(mapping=None):
 result={}
 for dim,tag in gmsh.model.getPhysicalGroups():
  name=gmsh.model.getPhysicalName(dim,tag)
  if dim!=2:continue
  rows=[]
  for entity in gmsh.model.getEntitiesForPhysicalGroup(dim,tag):
   types,_,arrays=gmsh.model.mesh.getElements(2,int(entity))
   for t,flat in zip(types,arrays):
    n=gmsh.model.mesh.getElementProperties(t)[3]
    for i in range(0,len(flat),n):rows.append(tuple(mapping[int(k)] if mapping else int(k) for k in flat[i:i+n]))
  result[name]=rows
 return result
gmsh.initialize();gmsh.option.setNumber('General.Terminal',0)
try:
 source=p/'air-planar-caps.msh';output=p/'air-exterior-gmsh22.msh';gmsh.open(str(source));records,used,before=cells();xyz={k:v for k,v in nodes().items() if k in used};index={tuple(round(v,12) for v in point):k for k,point in xyz.items()};assert len(index)==len(xyz)
 physical_before={(int(dim),int(tag)):gmsh.model.getPhysicalName(dim,tag) for dim,tag in gmsh.model.getPhysicalGroups()};inc=Counter()
 for t,ids in records:
  for face in patterns[t]:inc[tuple(sorted(ids[i] for i in face))]+=1
 assert max(inc.values())==2
 expected={};removed=Counter()
 for name,faces in surfaces().items():
  expected[name]=[]
  for face in faces:
   if inc[tuple(sorted(face))]==2:assert name=='wall';removed[name]+=1
   else:assert inc[tuple(sorted(face))]==1;expected[name].append(face)
 assert removed=={'wall':1496};gmsh.clear();gmsh.open(str(output));new=nodes();mapping={k:index[tuple(round(v,12) for v in point)] for k,point in new.items()};assert len(set(mapping.values()))==len(xyz)==len(mapping)
 delta=max(math.dist(new[k],xyz[v]) for k,v in mapping.items());assert delta<1e-12
 _,used_after,after=cells(mapping);assert before==after and used_after==used
 physical_after={(int(dim),int(tag)):gmsh.model.getPhysicalName(dim,tag) for dim,tag in gmsh.model.getPhysicalGroups()};assert physical_after==physical_before
 actual=surfaces(mapping);assert set(actual)==set(expected)
 def oriented(face):return min(face[i:]+face[:i] for i in range(len(face)))
 for name in expected:assert Counter(oriented(f) for f in actual[name])==Counter(oriented(f) for f in expected[name])
 counts=Counter(tuple(sorted(face)) for faces in actual.values() for face in faces);assert all(v==1 for v in counts.values());assert set(counts)=={f for f,n in inc.items() if n==1}
 r=dict(source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),output_sha256=hashlib.sha256(output.read_bytes()).hexdigest(),method_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),gmsh_version=gmsh.__version__,volume_cells=len(records),used_nodes=len(used),node_and_element_numbering_preserved=False,one_to_one_node_coordinate_correspondence=True,maximum_coordinate_difference_m=delta,canonical_source_volume_connectivity_sha256=before,volume_connectivity_preserved_under_explicit_node_mapping=True,removed_internal_wall_faces=dict(removed),physical_surface_face_counts={k:len(v) for k,v in actual.items()},all_exterior_faces_exactly_once=True,all_physical_names_preserved=True,all_surface_orientations_preserved=True,target_solver_import_executed=False,engineering_accepted=False,scope='Gmsh4.1 to2.2 exchange with full coordinate/connectivity/boundary correspondence. Native writer renumbers identifiers; byte or identifier identity is not claimed. No target solver import or pressure acceptance.')
 with (p/'gmsh22-oriented-correspondence-review.json').open('x') as f:json.dump(r,f,indent=2)
 print(json.dumps(r))
finally:gmsh.finalize()
