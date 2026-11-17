from pathlib import Path
from collections import Counter
import gmsh,json,hashlib
base=Path(__file__).parent
src=base.parent/'su2-pressure-verification/plenum-native-air-domain/family-1-layers/air-exterior-gmsh22.msh'
out=base/'plenum-family-1-constrained-core-relocation';out.mkdir(exist_ok=False)
gmsh.initialize();gmsh.option.setNumber('General.Terminal',0);gmsh.option.setNumber('Mesh.Renumber',0);gmsh.open(str(src));original=gmsh.model.getCurrent()
def coords():
 t,a,_=gmsh.model.mesh.getNodes();return {int(v):tuple(float(x) for x in a[i*3:i*3+3]) for i,v in enumerate(t)}
def elements(dim):
 ts,es,ns=gmsh.model.mesh.getElements(dim);return [(int(t),[int(x) for x in e],[int(x) for x in n]) for t,e,n in zip(ts,es,ns)]
before=coords();vol=elements(3);sur=elements(2);protected=set()
for typ,tags,nodes in vol:
 if typ==6:protected.update(nodes)
for typ,tags,nodes in sur:protected.update(nodes)
tets=next(x for x in vol if x[0]==4);tags=tets[1];flat=tets[2];used=set(flat);faces={};inc=Counter()
for i in range(0,len(flat),4):
 a,b,c,d=flat[i:i+4]
 for face in ((a,c,b),(a,b,d),(b,c,d),(c,a,d)):
  key=tuple(sorted(face));inc[key]+=1;faces[key]=face
assert max(inc.values())==2
boundary=[faces[k] for k,n in inc.items() if n==1];boundary_nodes={i for face in boundary for i in face}
assert used&protected<=boundary_nodes
print('core',len(tags),'boundary triangles',len(boundary),flush=True)
gmsh.model.add('tet_core');gmsh.model.addDiscreteEntity(2,1);gmsh.model.addDiscreteEntity(3,1,[1]);nodes=sorted(used)
gmsh.model.mesh.addNodes(3,1,nodes,[x for i in nodes for x in before[i]])
gmsh.model.mesh.addElementsByType(1,2,list(range(max(tags)+1,max(tags)+1+len(boundary))),[x for face in boundary for x in face])
gmsh.model.mesh.addElementsByType(1,4,tags,flat);gmsh.model.mesh.reclassifyNodes()
gmsh.model.mesh.optimize('Relocate3D',force=True,niter=5)
after=coords();changed=[i for i in used if before[i]!=after[i]]
assert not set(changed)&protected
assert not set(changed)&boundary_nodes
assert next(x for x in elements(3) if x[0]==4)==tets
assert min(gmsh.model.mesh.getElementQualities(tags,'minDetJac'))>0
print('changed internal nodes',len(changed),flush=True)
gmsh.model.setCurrent(original)
for i in changed:gmsh.model.mesh.setNode(i,after[i],[])
assert elements(3)==vol and elements(2)==sur
assert min(gmsh.model.mesh.getElementQualities([i for _,ts,_ in vol for i in ts],'minDetJac'))>0
gmsh.option.setNumber('Mesh.MshFileVersion',2.2);gmsh.option.setNumber('Mesh.Binary',0);gmsh.write(str(out/'air-exterior-gmsh22.msh'))
r={'method':'Gmsh4.15.2 Relocate3D five iterations on extracted original tetrahedral core with explicit discrete triangular boundary','source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'core_tetrahedra':len(tags),'core_boundary_triangles':len(boundary),'moved_nodes':len(changed),'moved_protected_nodes':0,'volume_connectivity_unchanged':True,'surface_connectivity_unchanged':True,'engineering_accepted':False}
(out/'optimization-review.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r),flush=True);gmsh.finalize()
