from pathlib import Path
from collections import Counter
import gmsh,json,hashlib,math
p=Path(__file__).parent;source=p/'wall-only-oriented-air.su2';dest=p/'main-exterior-gmsh22.msh';assert not dest.exists()
source_review=json.loads((p/'main-exchange-source-boundary-review.json').read_text());assert hashlib.sha256(source.read_bytes()).hexdigest()==source_review['source_sha256']
lines=source.read_text().splitlines();i=1;ne=int(lines[i].split('=')[1]);i+=1;cells=[];bytype={10:[],13:[]};nmap={10:4,13:6}
for line in lines[i:i+ne]:
 row=list(map(int,line.split()));kind=row[0];n=nmap[kind];nodes=tuple(row[1:1+n]);cells.append((kind,nodes));bytype[kind].append(nodes)
i+=ne;nn=int(lines[i].split('=')[1]);i+=1;xyz={}
for line in lines[i:i+nn]:v=line.split();xyz[int(v[3])]=tuple(map(float,v[:3]))
i+=nn;nm=int(lines[i].split('=')[1]);i+=1;markers={}
for _ in range(nm):
 name=lines[i].split('=')[1].strip();count=int(lines[i+1].split('=')[1]);i+=2;markers[name]=[tuple(map(int,line.split()[1:])) for line in lines[i:i+count]];i+=count
assert len(xyz)==nn and set(xyz)==set(range(nn));index={tuple(round(x,12) for x in v):k for k,v in xyz.items()};assert len(index)==nn
def digest(records):
 h=hashlib.sha256()
 for kind,nodes in sorted(records):h.update((str(kind)+':'+','.join(map(str,nodes))+'\n').encode())
 return h.hexdigest()
def oriented(face):return min(face[j:]+face[:j] for j in range(len(face)))
gmsh.initialize();gmsh.option.setNumber('General.Terminal',0)
try:
 gmsh.model.add('source-bound-main-mesh');vol=gmsh.model.addDiscreteEntity(3);gmsh.model.mesh.addNodes(3,vol,[j+1 for j in range(nn)],[v for j in range(nn) for v in xyz[j]])
 tag=1
 for kind,rows in bytype.items():
  gt={10:4,13:6}[kind];gmsh.model.mesh.addElementsByType(vol,gt,list(range(tag,tag+len(rows))),[row[k]+1 for row in rows for k in ((0,2,1,3,5,4) if kind==13 else (0,1,2,3))]);tag+=len(rows)
 for group,(name,faces) in enumerate(markers.items(),1):
  surf=gmsh.model.addDiscreteEntity(2)
  for n in (3,4):
   rows=[f for f in faces if len(f)==n]
   if rows:gmsh.model.mesh.addElementsByType(surf,{3:2,4:3}[n],list(range(tag,tag+len(rows))),[j+1 for row in rows for j in row]);tag+=len(rows)
  gmsh.model.addPhysicalGroup(2,[surf],group,name)
 gmsh.model.addPhysicalGroup(3,[vol],nm+1,'fluid');ts,et,_=gmsh.model.mesh.getElements(3);element_tags=[int(j) for ids in et for j in ids];quality=gmsh.model.mesh.getElementQualities(element_tags,'minSICN');volumes=gmsh.model.mesh.getElementQualities(element_tags,'volume');assert min(quality)>0 and min(volumes)>0
 gmsh.option.setNumber('Mesh.MshFileVersion',2.2);gmsh.option.setNumber('Mesh.Binary',0);gmsh.write(str(dest));gmsh.clear();gmsh.open(str(dest));nt,flat,_=gmsh.model.mesh.getNodes();new={int(t):tuple(float(x) for x in flat[j*3:j*3+3]) for j,t in enumerate(nt)};mapping={j:index[tuple(round(x,12) for x in v)] for j,v in new.items()};assert len(mapping)==len(set(mapping.values()))==nn;delta=max(math.dist(new[j],xyz[k]) for j,k in mapping.items());assert delta<1e-12
 ts,et,arrays=gmsh.model.mesh.getElements(3);records=[]
 for gt,a in zip(ts,arrays):
  kind={4:10,6:13}[int(gt)];n=nmap[kind]
  for j in range(0,len(a),n):row=tuple(mapping[int(x)] for x in a[j:j+n]);records.append((kind,tuple(row[k] for k in (0,2,1,3,5,4)) if kind==13 else row))
 assert digest(records)==digest(cells) and len(records)==ne
 actual={}
 for dim,phys in gmsh.model.getPhysicalGroups():
  if dim!=2:continue
  name=gmsh.model.getPhysicalName(dim,phys);actual[name]=[]
  for entity in gmsh.model.getEntitiesForPhysicalGroup(dim,phys):
   ts,_,arrays=gmsh.model.mesh.getElements(2,int(entity))
   for gt,a in zip(ts,arrays):
    n={2:3,3:4}[int(gt)]
    for j in range(0,len(a),n):actual[name].append(tuple(mapping[int(x)] for x in a[j:j+n]))
 assert set(actual)==set(markers)
 for name in markers:assert Counter(oriented(f) for f in markers[name])==Counter(oriented(f) for f in actual[name])
 r=dict(source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),source_boundary_review_sha256=hashlib.sha256((p/'main-exchange-source-boundary-review.json').read_bytes()).hexdigest(),output_sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),method_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),gmsh_version=gmsh.__version__,volume_cells=ne,nodes=nn,canonical_volume_connectivity_sha256=digest(cells),minimum_SICN=float(min(quality)),minimum_signed_volume_m3=float(min(volumes)),maximum_coordinate_difference_m=delta,prism_su2_to_gmsh_permutation=[0,2,1,3,5,4],all_volume_connectivity_preserved=True,all_boundary_names_and_orientations_preserved=True,boundary_face_counts={k:len(v) for k,v in actual.items()},new_geometry_or_remeshing=False,target_solver_import_executed=False,engineering_accepted=False,scope='Source-checked SU2 discrete mesh encoded with existing Gmsh API as MSH2.2; identifiers may renumber, geometry/connectivity/boundary correspondence checked. No OpenFOAM or pressure acceptance.')
 with (p/'main-gmsh22-exchange-review.json').open('x') as f:json.dump(r,f,indent=2,allow_nan=False)
 print(json.dumps(r))
finally:gmsh.finalize()
