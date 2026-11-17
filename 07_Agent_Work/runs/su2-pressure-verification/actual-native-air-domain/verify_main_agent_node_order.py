from pathlib import Path
from collections import Counter
import gmsh,json,hashlib,math
import bsa.cfd_node_order as method
p=Path(__file__).parent;source=p/'wall-only-oriented-air.su2';target=p/'main-exterior-gmsh22.msh';old=json.loads((p/'main-gmsh22-exchange-review.json').read_text());assert hashlib.sha256(source.read_bytes()).hexdigest()==old['source_sha256'] and hashlib.sha256(target.read_bytes()).hexdigest()==old['output_sha256']
lines=source.read_text().splitlines();n=int(lines[1].split('=')[1]);cells=[];counts=Counter()
for line in lines[2:2+n]:
 a=list(map(int,line.split()));kind=a[0];nodes=tuple(a[1:1+{10:4,13:6}[kind]]);assert method.gmsh_to_su2(*method.su2_to_gmsh(kind,nodes))==(kind,nodes);cells.append((kind,nodes));counts[kind]+=1
i=2+n;nn=int(lines[i].split('=')[1]);xyz={}
for line in lines[i+1:i+1+nn]:a=line.split();xyz[int(a[3])]=tuple(map(float,a[:3]))
index={tuple(round(x,12) for x in v):k for k,v in xyz.items()};assert len(index)==nn
def digest(records):
 h=hashlib.sha256()
 for kind,nodes in sorted(records):h.update((str(kind)+':'+','.join(map(str,nodes))+'\n').encode())
 return h.hexdigest()
gmsh.initialize();gmsh.option.setNumber('General.Terminal',0)
try:
 gmsh.open(str(target));tags,flat,_=gmsh.model.mesh.getNodes();mapping={};delta=0
 for i,tag in enumerate(tags):
  point=tuple(float(x) for x in flat[i*3:i*3+3]);key=index[tuple(round(x,12) for x in point)];mapping[int(tag)]=key;delta=max(delta,math.dist(point,xyz[key]))
 assert len(mapping)==len(set(mapping.values()))==nn and delta<1e-12
 types,ets,arrays=gmsh.model.mesh.getElements(3);actual=[];all_tags=[]
 for kind,ids,a in zip(types,ets,arrays):
  count=gmsh.model.mesh.getElementProperties(kind)[3];all_tags.extend(int(x) for x in ids)
  for j in range(0,len(a),count):actual.append(method.gmsh_to_su2(int(kind),[mapping[int(x)] for x in a[j:j+count]]))
 assert len(actual)==n and digest(actual)==digest(cells)==old['canonical_volume_connectivity_sha256']
 quality=gmsh.model.mesh.getElementQualities(all_tags,'minSICN');volumes=gmsh.model.mesh.getElementQualities(all_tags,'volume');assert min(quality)>0 and min(volumes)>0
 r=dict(source_sha256=old['source_sha256'],target_mesh_sha256=old['output_sha256'],agent_method_sha256=hashlib.sha256(Path(method.__file__).read_bytes()).hexdigest(),verification_method_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),gmsh_version=gmsh.__version__,cells_checked=n,source_cell_type_counts=dict(counts),nodes_checked=nn,maximum_coordinate_difference_m=delta,all_source_cells_roundtrip_pass=True,all_native_gmsh_cells_match_source_ordering=True,canonical_volume_connectivity_sha256=digest(actual),minimum_native_SICN=float(min(quality)),minimum_native_signed_volume_m3=float(min(volumes)),target_solver_import_executed=False,engineering_accepted=False,scope='Existing Gmsh mesh plus new thin ordering helper replay on all actual main cells. Node ordering only; no new solver, geometry, pressure or general mesh-format acceptance.')
 with (p/'main-agent-node-order-review.json').open('x') as f:json.dump(r,f,indent=2,allow_nan=False)
 print(json.dumps(r))
finally:gmsh.finalize()
